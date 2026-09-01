"""Pick the sparse ranking config on a 1000-query sample of the real evaluation
set, so the 3h full run is spent on a config chosen with evidence.

The sample is a deterministic slice of the SAME seed-42 query set; the full run
still uses all 20,672 queries with the untouched seed.
"""
import os
import json
import math
import random
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATASET_PATH = "../data/songInterpretation/dataset_full_256_clean.json"
SAMPLE = 1000
TOP_K = 20
SEED = 42

CONFIGS = {
    "current: default w, n=0": ([0.1, 0.2, 0.4, 1.0], 0),
    "B=0.05 n=0": ([0.02, 0.05, 0.05, 1.0], 0),
    "B=0.05 n=1": ([0.02, 0.05, 0.05, 1.0], 1),
    "B=0.05 n=16": ([0.02, 0.05, 0.05, 1.0], 16),
    "B=0.02 n=1": ([0.02, 0.02, 0.02, 1.0], 1),
    "B=0.10 n=16": ([0.02, 0.05, 0.10, 1.0], 16),
}

random.seed(SEED)
with open(DATASET_PATH, encoding="utf-8") as f:
    records = json.load(f)
by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])
queries = [(sid, random.choice(c)) for sid, c in by_song.items()]

# deterministic sample, independent of the query-sampling RNG stream
sample = random.Random(1234).sample(queries, SAMPLE)
print(f"{len(sample)} sample queries\n")

with engine.connect() as conn:
    term_df = dict(conn.execute(
        text("SELECT word, ndoc FROM ts_stat('SELECT tsv FROM song')")).fetchall())

    def tsq_for(qtext):
        lex = conn.execute(
            text("SELECT tsvector_to_array(to_tsvector('english', :t))"), {"t": qtext}
        ).scalar()
        if not lex:
            return None
        lex = sorted(lex, key=lambda l: term_df.get(l, 0))[:20]
        return " | ".join("'" + l.replace("'", "''") + "'" for l in lex)

    tsqs = [(sid, tsq_for(q)) for sid, q in sample]

    header = f"{'config':<26}{'R@1':>8}{'R@5':>8}{'R@10':>8}{'MRR':>8}{'nDCG@10':>10}"
    print(header)
    print("-" * len(header))

    for name, (weights, norm) in CONFIGS.items():
        ranks = []
        for sid, tsq in tsqs:
            if tsq is None:
                ranks.append(None)
                continue
            rows = conn.execute(
                text("""
                    WITH q AS (SELECT to_tsquery('english', :tsq) AS tsq)
                    SELECT song.id
                    FROM song, q
                    WHERE song.tsv @@ q.tsq
                    ORDER BY ts_rank_cd(CAST(:w AS float4[]), song.tsv, q.tsq, :norm) DESC,
                             song.id ASC
                    LIMIT :lim
                """),
                {"tsq": tsq, "w": weights, "norm": norm, "lim": TOP_K},
            ).fetchall()
            ids = [r[0] for r in rows]
            ranks.append(ids.index(sid) + 1 if sid in ids else None)

        n = len(ranks)
        rec = lambda k: sum(1 for r in ranks if r and r <= k) / n
        mrr = sum(1 / r for r in ranks if r) / n
        ndcg = sum(1 / math.log2(r + 1) for r in ranks if r and r <= 10) / n
        print(f"{name:<26}{rec(1):>8.4f}{rec(5):>8.4f}{rec(10):>8.4f}{mrr:>8.4f}{ndcg:>10.4f}")
