import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

LYRICS_DIR = "../data/music4all/lyrics"
BATCH_SIZE = 500

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE song ADD COLUMN IF NOT EXISTS tsv tsvector;"))

with engine.connect() as conn:
    ids = [row[0] for row in conn.execute(
        text("SELECT id FROM song WHERE tsv IS NULL ORDER BY id")
    )]

print(f"sparse-indexing {len(ids)} songs")


def read_lyrics(song_id):
    with open(f"{LYRICS_DIR}/{song_id}.txt", encoding="utf-8") as f:
        return f.read().strip()


for i in range(0, len(ids), BATCH_SIZE):
    batch_ids = ids[i:i + BATCH_SIZE]
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE song
                SET tsv = setweight(to_tsvector('english', coalesce(artist, '') || ' ' || coalesce(song, '')), 'A')
                        || setweight(to_tsvector('english', :lyrics), 'B')
                WHERE id = :id
            """),
            [{"id": sid, "lyrics": read_lyrics(sid)} for sid in batch_ids],
        )
    print(f"{min(i + BATCH_SIZE, len(ids))}/{len(ids)}")

print("tsvector build done, creating GIN index")

with engine.begin() as conn:
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_song_tsv_gin ON song USING GIN (tsv);"))

print("GIN index built")
