import os
import time
import logging
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

import retrieval
import spotify
import auth as auth_lib

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
    auth_lib.init_schema(engine)
    log.info("auth schema ready")
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


@app.get("/genre-art")
def genre_art(genres: str, per_genre: int = 4):
    """Representative album art per genre, for the browse tiles.

    Returns up to `per_genre` artwork urls for each requested genre. The UI lays
    them out as a mosaic with the genre label *outside* the images: Spotify's
    terms forbid drawing text over their artwork (D34).
    """
    names = [g for g in (n.strip() for n in genres.split(",")) if g][:24]
    if not names:
        return {"genre_art": {}}

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT genre, id FROM (
                    SELECT trim(g) AS genre, song.id,
                           row_number() OVER (
                               PARTITION BY trim(g)
                               -- hash on (genre, id) so each genre draws a
                               -- different pseudo-random sample: ordering by id
                               -- alone gave neighbouring genres the same covers,
                               -- since one song belongs to several genres
                               ORDER BY md5(trim(g) || song.id)
                           ) AS rn
                    FROM song, unnest(string_to_array(song.genres, ',')) AS g
                    WHERE song.spotify_id IS NOT NULL AND trim(g) = ANY(:names)
                ) ranked
                WHERE rn <= :per
            """),
            {"names": names, "per": per_genre},
        ).fetchall()

    by_genre = {}
    for r in rows:
        by_genre.setdefault(r.genre, []).append(r.id)

    song_ids = [sid for ids in by_genre.values() for sid in ids]
    with engine.connect() as conn:
        meta = conn.execute(
            text("SELECT id, spotify_id FROM song WHERE id = ANY(:ids)"), {"ids": song_ids}
        ).fetchall()

    art = spotify.get_artwork({m.id: m.spotify_id for m in meta})
    out = {
        genre: [art[sid]["url"] for sid in ids if sid in art]
        for genre, ids in by_genre.items()
    }
    log.info("genre-art requested=%d resolved=%d", len(names), sum(1 for v in out.values() if v))
    return {"genre_art": out}


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


# --- authentication (D25: fabricated test accounts only, no real personal data) ---

# Plain format check rather than pydantic's EmailStr: accounts here are
# fabricated test accounts by design (D25), and EmailStr rejects reserved test
# domains like .local / .test, which is exactly what we want people to use.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class SignupBody(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8)
    taste_genres: list[str] = []


class LoginBody(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str


class TasteBody(BaseModel):
    taste_genres: list[str]


def current_user(authorization: str | None):
    """Resolves a Bearer token to a user row, or None."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    payload = auth_lib.decode_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        return None
    with engine.connect() as conn:
        return auth_lib.get_user(conn, int(payload["sub"]))


def require_user(authorization: str | None):
    user = current_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="not authenticated")
    return user


def user_payload(row, token=None):
    out = {"id": row.id, "email": row.email, "taste_genres": list(row.taste_genres or [])}
    if token:
        out["token"] = token
    return out


@app.post("/auth/signup")
def signup(body: SignupBody):
    email = body.email.strip().lower()
    with engine.begin() as conn:
        if auth_lib.get_user_by_email(conn, email):
            raise HTTPException(status_code=409, detail="an account with that email already exists")
        row = auth_lib.create_user(conn, email, body.password, body.taste_genres)
    log.info("signup id=%s", row.id)
    return user_payload(row, auth_lib.make_token(row.id, row.email))


@app.post("/auth/login")
def login(body: LoginBody):
    email = body.email.strip().lower()
    with engine.connect() as conn:
        row = auth_lib.get_user_by_email(conn, email)
    # same message either way: don't reveal whether the email exists
    if row is None or not auth_lib.verify_password(body.password, row.password_hash):
        raise HTTPException(status_code=401, detail="incorrect email or password")
    log.info("login id=%s", row.id)
    return user_payload(row, auth_lib.make_token(row.id, row.email))


@app.get("/auth/me")
def me(authorization: str | None = Header(default=None)):
    return user_payload(require_user(authorization))


@app.put("/auth/taste")
def update_taste(body: TasteBody, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with engine.begin() as conn:
        auth_lib.set_taste_genres(conn, user.id, body.taste_genres)
        return user_payload(auth_lib.get_user(conn, user.id))


@app.post("/history/{song_id}")
def add_history(song_id: str, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    with engine.begin() as conn:
        auth_lib.record_view(conn, user.id, song_id)
    return {"ok": True}


@app.get("/recommendations")
def recommendations(limit: int = 12, authorization: str | None = Header(default=None)):
    """Taste-genre songs, excluding anything already viewed, plus recent history.

    Deliberately simple: a genre sample the user has not seen. Anything stronger
    (collaborative filtering, taste vectors) is further work per D3.
    """
    user = require_user(authorization)
    genres = list(user.taste_genres or [])

    with engine.connect() as conn:
        viewed = [r.song_id for r in auth_lib.recent_views(conn, user.id, 20)]

        recs = []
        if genres:
            rows = conn.execute(
                text(f"""
                    SELECT {SONG_FIELDS} FROM song
                    WHERE genres IS NOT NULL
                      AND EXISTS (
                          SELECT 1 FROM unnest(string_to_array(genres, ',')) AS g
                          WHERE trim(g) = ANY(:genres)
                      )
                      AND (CAST(:viewed AS text[]) IS NULL OR NOT (id = ANY(CAST(:viewed AS text[]))))
                    ORDER BY md5(id)
                    LIMIT :lim
                """),
                {"genres": genres, "viewed": viewed or None, "lim": limit},
            ).fetchall()
            recs = [song_summary(r) for r in rows]

        history = []
        if viewed:
            rows = conn.execute(
                text(f"SELECT {SONG_FIELDS} FROM song WHERE id = ANY(:ids)"), {"ids": viewed}
            ).fetchall()
            by_id = {r.id: r for r in rows}
            history = [song_summary(by_id[sid]) for sid in viewed if sid in by_id]

    return {"taste_genres": genres, "recommendations": recs, "recently_viewed": history}


def song_summary(row):
    return {
        "song_id": row.id,
        "title": row.song,
        "artist": row.artist,
        "album_name": row.album_name,
        "genres": split_list(row.genres),
        "spotify_id": row.spotify_id,
        "lyric_snippet": row.lyric_snippet,
    }
