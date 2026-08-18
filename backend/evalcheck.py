import os, json, random
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
random.seed(42)

with open("../data/songInterpretation/dataset_full_256_clean.json", encoding="utf-8") as f:
    records = json.load(f)
by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])
queries = [(sid, random.choice(c)) for sid, c in by_song.items()]

model = SentenceTransformer("all-MiniLM-L6-v2")

def vec(e): return "[" + ",".join(str(float(x)) for x in e) + "]"

# check 5 queries: is the correct song present + embedded, and where did it rank?
sample = random.sample(queries, 5)
with engine.begin() as conn:
    conn.execute(text("SET LOCAL ivfflat.probes = 100"))
    for sid, comment in sample:
        row = conn.execute(text(
            "SELECT artist, song, (embedding IS NOT NULL) AS has_emb FROM song WHERE id = :id"
        ), {"id": sid}).fetchone()
        emb = model.encode(comment)
        top = conn.execute(text(
            "SELECT id FROM song ORDER BY embedding <=> (:v)::vector LIMIT 20"
        ), {"v": vec(emb)}).fetchall()
        top_ids = [r[0] for r in top]
        rank = top_ids.index(sid) + 1 if sid in top_ids else None
        print("---")
        print("song in table:", row is not None, "| has embedding:", row.has_emb if row else "N/A")
        print("correct:", (row.artist, row.song) if row else "MISSING FROM TABLE")
        print("rank in top20:", rank)
        print("query:", comment[:120])