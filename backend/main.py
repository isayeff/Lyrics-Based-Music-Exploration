import os
import time
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

import retrieval
import spotify

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("api")

engine = create_engine(os.environ["DATABASE_URL"])
model = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI(title="Lyrics Music Exploration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# corpus lexeme document frequencies for the sparse rarest-lexeme filter (D26);
# computed once at startup (~1s) and held in memory
TERM_DF = {}


@app.on_event("startup")
def load_corpus_stats():
    t0 = time.perf_counter()
    with engine.connect() as conn:
        TERM_DF.update(retrieval.load_term_df(conn))
    log.info("loaded %d corpus lexemes in %.2fs", len(TERM_DF), time.perf_counter() - t0)
    if not spotify.credentials_configured():
        log.warning(
            "SPOTIFY_CLIENT_ID/SECRET not set — /artwork returns empty and the UI "
            "falls back to deterministic colour blocks"
        )


@app.middleware("http")
async def log_timing(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    log.info(
        "%s %s -> %s in %.1fms",
        request.method, request.url.path, response.status_code,
        (time.perf_counter() - t0) * 1000,
    )
    return response


class SearchQuery(BaseModel):
    query: str
    mode: Literal["dense", "sparse", "hybrid"] = "hybrid"
    limit: int = Field(default=20, ge=1, le=100)


SONG_FIELDS = "id, artist, song, album_name, genres, tags, lyric_snippet, spotify_id"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search")
def search(body: SearchQuery):
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query must not be empty")

    t0 = time.perf_counter()
    # dense modes need the query embedded; sparse does not
    query_vec = model.encode(query).tolist() if body.mode in ("dense", "hybrid") else None
    embed_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    with engine.begin() as conn:
        hits = retrieval.search(conn, body.mode, query, query_vec, body.limit, TERM_DF)
        if not hits:
            log.info("search mode=%s q=%r -> 0 results", body.mode, query)
            return {"query": query, "mode": body.mode, "count": 0, "results": []}

        ids = [sid for sid, _, _ in hits]
        rows = conn.execute(
            text(f"SELECT {SONG_FIELDS} FROM song WHERE id = ANY(:ids)"), {"ids": ids}
        ).fetchall()
    retrieve_ms = (time.perf_counter() - t1) * 1000

    by_id = {r.id: r for r in rows}
    results = []
    for rank, (sid, score, contributors) in enumerate(hits, start=1):
        row = by_id.get(sid)
        if row is None:
            continue
        results.append({
            "song_id": row.id,
            "title": row.song,
            "artist": row.artist,
            "album_name": row.album_name,
            "genres": split_list(row.genres),
            "spotify_id": row.spotify_id,
            "lyric_snippet": row.lyric_snippet,
            "score": round(score, 5),
            "rank": rank,
            "retrievers": contributors,
        })

    log.info(
        "search mode=%s q=%r -> %d results (embed %.1fms, retrieve %.1fms)",
        body.mode, query, len(results), embed_ms, retrieve_ms,
    )
    return {"query": query, "mode": body.mode, "count": len(results), "results": results}


@app.get("/song/{song_id}")
def get_song(song_id: str):
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {SONG_FIELDS} FROM song WHERE id = :id"), {"id": song_id}
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="song not found")
    return {
        "song_id": row.id,
        "title": row.song,
        "artist": row.artist,
        "album_name": row.album_name,
        "genres": split_list(row.genres),
        "tags": split_list(row.tags),
        "lyric_snippet": row.lyric_snippet,
        "spotify_id": row.spotify_id,
    }


@app.get("/genres")
def genres(limit: int = 200):
    """Distinct genres with song counts. genres is a comma-separated text column."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT trim(g) AS genre, count(*) AS count
                FROM song, unnest(string_to_array(genres, ',')) AS g
                WHERE genres IS NOT NULL AND trim(g) <> ''
                GROUP BY trim(g)
                ORDER BY count DESC
                LIMIT :lim
            """),
            {"lim": limit},
        ).fetchall()
    return {"count": len(rows), "genres": [{"genre": r.genre, "count": r.count} for r in rows]}


@app.get("/genre/{genre}")
def songs_by_genre(genre: str, limit: int = 50):
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"""
                SELECT {SONG_FIELDS} FROM song
                WHERE genres IS NOT NULL
                  AND :genre = ANY(SELECT trim(g) FROM unnest(string_to_array(genres, ',')) AS g)
                ORDER BY id
                LIMIT :lim
            """),
            {"genre": genre, "lim": limit},
        ).fetchall()
    return {
        "genre": genre,
        "count": len(rows),
        "songs": [{
            "song_id": r.id,
            "title": r.song,
            "artist": r.artist,
            "album_name": r.album_name,
            "genres": split_list(r.genres),
            "spotify_id": r.spotify_id,
            "lyric_snippet": r.lyric_snippet,
        } for r in rows],
    }


@app.get("/artwork")
def artwork(ids: str):
    """ids = comma-separated song ids (not spotify ids). Only for rendered results."""
    song_ids = [s for s in (i.strip() for i in ids.split(",")) if s][:200]
    if not song_ids:
        return {"artwork": {}}

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, spotify_id FROM song WHERE id = ANY(:ids)"), {"ids": song_ids}
        ).fetchall()

    art = spotify.get_artwork({r.id: r.spotify_id for r in rows})
    log.info("artwork requested=%d resolved=%d", len(song_ids), len(art))
    return {"artwork": art}


def split_list(value):
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]
