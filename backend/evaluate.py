import os
import json
import random
import math
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATASET_PATH = "../data/songInterpretation/dataset_full_256_clean.json"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 20
PROBES = 100
SEED = 42
RESULTS_PATH = "results/dense_baseline.json"

random.seed(SEED)

with open(DATASET_PATH, encoding="utf-8") as f:
    records = json.load(f)

by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])

# one interpretation per song, fixed seed -> reproducible query set
queries = [(song_id, random.choice(comments)) for song_id, comments in by_song.items()]
print(f"{len(queries)} queries (one interpretation per song)")

model = SentenceTransformer(MODEL_NAME)
texts = [q[1] for q in queries]
embeddings = model.encode(texts, batch_size=128, show_progress_bar=True)


def to_vector_literal(vec):
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


ranks = []
with engine.begin() as conn:
    conn.execute(text(f"SET LOCAL ivfflat.probes = {PROBES}"))
    for (song_id, _), emb in tqdm(zip(queries, embeddings), total=len(queries)):
        rows = conn.execute(
            text("SELECT id FROM song ORDER BY embedding <=> (:v)::vector LIMIT :k"),
            {"v": to_vector_literal(emb), "k": TOP_K},
        ).fetchall()
        retrieved = [row[0] for row in rows]
        rank = retrieved.index(song_id) + 1 if song_id in retrieved else None
        ranks.append(rank)


def recall_at(k):
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


mrr = sum((1 / r) if r is not None else 0 for r in ranks) / len(ranks)
ndcg10 = sum(
    (1 / math.log2(r + 1)) if r is not None and r <= 10 else 0 for r in ranks
) / len(ranks)

metrics = {
    "model": MODEL_NAME,
    "n_queries": len(ranks),
    "top_k": TOP_K,
    "ivfflat_probes": PROBES,
    "seed": SEED,
    "recall@1": recall_at(1),
    "recall@5": recall_at(5),
    "recall@10": recall_at(10),
    "mrr": mrr,
    "ndcg@10": ndcg10,
}

print(f"{'metric':<12}{'value':>10}")
for k in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"]:
    print(f"{k:<12}{metrics[k]:>10.4f}")

os.makedirs("results", exist_ok=True)
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"saved to {RESULTS_PATH}")
