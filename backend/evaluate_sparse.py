import os
import json
import random
import math
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from tqdm import tqdm

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATASET_PATH = "../data/songInterpretation/dataset_full_256_clean.json"
TOP_K = 20
MAX_QUERY_LEXEMES = 20  # keep only the K rarest lexemes per query (see build_or_tsquery)
SEED = 42
RESULTS_PATH = "results/sparse_baseline.json"
PER_QUERY_PATH = "results/sparse_per_query.json"
DENSE_PER_QUERY_PATH = "results/dense_per_query.json"
OVERLAP_PATH = "results/dense_vs_sparse_overlap.json"
TOP_K_FUSION = 50
TOP50_PATH = "results/sparse_top50.json"

random.seed(SEED)

# identical query sampling to evaluate.py: same file, same seed -> same picks
with open(DATASET_PATH, encoding="utf-8") as f:
    records = json.load(f)

by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])

queries = [(song_id, random.choice(comments)) for song_id, comments in by_song.items()]
print(f"{len(queries)} queries (one interpretation per song)")


print("computing corpus-wide lexeme document frequencies (one-time, for query term filtering)")
with engine.connect() as conn:
    term_df = dict(
        conn.execute(text("SELECT word, ndoc FROM ts_stat('SELECT tsv FROM song')")).fetchall()
    )
print(f"{len(term_df)} distinct lexemes in corpus")


def build_or_tsquery(conn, query_text):
    # Queries here are long free-text interpretations (50-300+ words), not short
    # keyword searches. plainto_tsquery/websearch_to_tsquery AND every lexeme
    # together, so requiring the full query vocabulary in one song's tsvector
    # almost never matches (measured recall@10 ~0.0001). OR-ing every lexeme
    # instead matched 73% of the corpus for a typical query (~0.6s/query, and
    # ts_rank_cd has no IDF term so ubiquitous words like "love"/"never" count
    # the same as distinctive ones). Fix: keep only the MAX_QUERY_LEXEMES
    # rarest lexemes per query (by corpus document frequency) before OR-ing.
    # Lexemes are quoted (with ' doubled) so stray special characters can't
    # break tsquery syntax.
    lexemes = conn.execute(
        text("SELECT tsvector_to_array(to_tsvector('english', :t))"), {"t": query_text}
    ).scalar()
    if not lexemes:
        return None
    lexemes = sorted(lexemes, key=lambda lex: term_df.get(lex, 0))[:MAX_QUERY_LEXEMES]
    return " | ".join("'" + lex.replace("'", "''") + "'" for lex in lexemes)


def sparse_search_ids(conn, query_text, k=TOP_K):
    tsq_input = build_or_tsquery(conn, query_text)
    if tsq_input is None:
        return []
    rows = conn.execute(
        text("""
            WITH q AS (SELECT to_tsquery('english', :tsq) AS tsq)
            SELECT song.id
            FROM song, q
            WHERE song.tsv @@ q.tsq
            ORDER BY ts_rank_cd(song.tsv, q.tsq) DESC
            LIMIT :k
        """),
        {"tsq": tsq_input, "k": k},
    ).fetchall()
    return [row[0] for row in rows]


ranks = []
top50_by_id = {}
with engine.connect() as conn:
    for song_id, query_text in tqdm(queries):
        retrieved50 = sparse_search_ids(conn, query_text, k=TOP_K_FUSION)
        top50_by_id[song_id] = retrieved50
        retrieved = retrieved50[:TOP_K]  # unchanged: old metrics/outputs stay top-20-based
        rank = retrieved.index(song_id) + 1 if song_id in retrieved else None
        ranks.append(rank)


def recall_at(k):
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


mrr = sum((1 / r) if r is not None else 0 for r in ranks) / len(ranks)
ndcg10 = sum(
    (1 / math.log2(r + 1)) if r is not None and r <= 10 else 0 for r in ranks
) / len(ranks)

metrics = {
    "model": "postgres_fts_english_ts_rank_cd",
    "n_queries": len(ranks),
    "top_k": TOP_K,
    "query_fn": "to_tsquery_or_of_rarest_lexemes",
    "max_query_lexemes": MAX_QUERY_LEXEMES,
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

sparse_by_id = {song_id: rank for (song_id, _), rank in zip(queries, ranks)}
with open(PER_QUERY_PATH, "w", encoding="utf-8") as f:
    json.dump(sparse_by_id, f, indent=2)

print(f"saved to {RESULTS_PATH} and {PER_QUERY_PATH}")

# full top-50 ranked candidate lists per query, for RRF fusion (evaluate_hybrid.py)
with open(TOP50_PATH, "w", encoding="utf-8") as f:
    json.dump(top50_by_id, f)

print(f"saved to {TOP50_PATH}")

# overlap analysis vs dense baseline (correct song in top 10)
with open(DENSE_PER_QUERY_PATH, encoding="utf-8") as f:
    dense_by_id = json.load(f)

both = dense_only = sparse_only = neither = 0
for song_id, _ in queries:
    dense_hit = dense_by_id.get(song_id) is not None and dense_by_id[song_id] <= 10
    sparse_hit = sparse_by_id.get(song_id) is not None and sparse_by_id[song_id] <= 10
    if dense_hit and sparse_hit:
        both += 1
    elif dense_hit:
        dense_only += 1
    elif sparse_hit:
        sparse_only += 1
    else:
        neither += 1

overlap = {
    "n_queries": len(queries),
    "both_top10": both,
    "dense_only_top10": dense_only,
    "sparse_only_top10": sparse_only,
    "neither_top10": neither,
}

with open(OVERLAP_PATH, "w", encoding="utf-8") as f:
    json.dump(overlap, f, indent=2)

print(f"\n{'category':<20}{'count':>10}")
for k in ["both_top10", "dense_only_top10", "sparse_only_top10", "neither_top10"]:
    print(f"{k:<20}{overlap[k]:>10}")
print(f"saved to {OVERLAP_PATH}")
