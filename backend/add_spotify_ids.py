"""Backfill song.spotify_id from music4all id_metadata.csv (tab-separated, see D12).

Idempotent + resumable: safe to re-run, only fills rows that are still NULL.
"""
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATA = "../data/music4all"
BATCH_SIZE = 1000

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE song ADD COLUMN IF NOT EXISTS spotify_id text;"))

meta = pd.read_csv(f"{DATA}/id_metadata.csv", sep="\t")[["id", "spotify_id"]]
meta = meta[meta["spotify_id"].notna()]
print(f"{len(meta)} spotify ids in metadata")

with engine.connect() as conn:
    todo = {r[0] for r in conn.execute(text("SELECT id FROM song WHERE spotify_id IS NULL"))}
print(f"{len(todo)} song rows still missing a spotify_id")

rows = [
    {"id": r.id, "sid": r.spotify_id}
    for r in meta.itertuples()
    if r.id in todo
]
print(f"{len(rows)} to update")

for i in range(0, len(rows), BATCH_SIZE):
    batch = rows[i:i + BATCH_SIZE]
    with engine.begin() as conn:
        conn.execute(text("UPDATE song SET spotify_id = :sid WHERE id = :id"), batch)
    print(f"{min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

with engine.connect() as conn:
    filled = conn.execute(text("SELECT count(*) FROM song WHERE spotify_id IS NOT NULL")).scalar()
    total = conn.execute(text("SELECT count(*) FROM song")).scalar()
print(f"done: {filled}/{total} songs have a spotify_id")
