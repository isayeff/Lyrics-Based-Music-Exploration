import os
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
model = SentenceTransformer("all-MiniLM-L6-v2")

app = FastAPI(title="Lyrics Music Exploration API")

class SearchQuery(BaseModel):
    query: str
    limit: int = 10

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(body: SearchQuery):
    vec = model.encode(body.query).tolist()
    vec_literal = "[" + ",".join(str(float(x)) for x in vec) + "]"
    with engine.connect() as conn:
        conn.execute(text("SET LOCAL ivfflat.probes = 10"))
        rows = conn.execute(text("""
            SELECT id, artist, song, genres, lyric_snippet,
                   embedding <=> (:q)::vector AS distance
            FROM song
            ORDER BY distance ASC
            LIMIT :lim
        """), {"q": vec_literal, "lim": body.limit}).fetchall()
    return [
        {"id": r.id, "artist": r.artist, "song": r.song,
         "genres": r.genres, "snippet": r.lyric_snippet,
         "score": round(1 - r.distance, 3)}
        for r in rows
    ]