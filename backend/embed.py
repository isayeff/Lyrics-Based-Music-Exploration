import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

LYRICS_DIR = "../data/music4all/lyrics"  # ingest.py's DATA/lyrics, not ../data/lyrics
MODEL_NAME = "all-MiniLM-L6-v2"
DIM = 384
BATCH_SIZE = 128
IVFFLAT_LISTS = 100  # ~ n/1000 for n=84k rows (pgvector rule of thumb)

model = SentenceTransformer(MODEL_NAME)

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.execute(text(f"ALTER TABLE song ADD COLUMN IF NOT EXISTS embedding vector({DIM});"))

with engine.connect() as conn:
    ids = [row[0] for row in conn.execute(
        text("SELECT id FROM song WHERE embedding IS NULL ORDER BY id")
    )]

print(f"embedding {len(ids)} songs with {MODEL_NAME}")

def read_lyrics(song_id):
    with open(f"{LYRICS_DIR}/{song_id}.txt", encoding="utf-8") as f:
        return f.read().strip()


def to_vector_literal(vec):
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


for i in tqdm(range(0, len(ids), BATCH_SIZE)):
    batch_ids = ids[i:i + BATCH_SIZE]
    texts = [read_lyrics(sid) for sid in batch_ids]
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False)

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE song SET embedding = (:emb)::vector WHERE id = :id"),
            [
                {"id": sid, "emb": to_vector_literal(emb)}
                for sid, emb in zip(batch_ids, embeddings)
            ],
        )

print("embedding done, building ivfflat index")

with engine.begin() as conn:
    conn.execute(text("SET LOCAL maintenance_work_mem = '256MB'"))
    # WITH (lists=...) is a storage parameter, not a bind param -> must be a literal
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_song_embedding_cosine "
        f"ON song USING ivfflat (embedding vector_cosine_ops) WITH (lists = {IVFFLAT_LISTS})"
    ))

print("index built")
