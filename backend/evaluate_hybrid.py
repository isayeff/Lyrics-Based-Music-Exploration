import json
import math
import traceback
from collections import defaultdict

DENSE_TOP50_PATH = "results/dense_top50.json"
SPARSE_TOP50_PATH = "results/sparse_top50.json"
DENSE_PER_QUERY_PATH = "results/dense_per_query.json"  # top-20-based, from evaluate.py
SPARSE_PER_QUERY_PATH = "results/sparse_per_query.json"  # top-20-based, from evaluate_sparse.py
DENSE_BASELINE_PATH = "results/dense_baseline.json"
SPARSE_BASELINE_PATH = "results/sparse_baseline.json"

HYBRID_BASELINE_PATH = "results/hybrid_baseline.json"
HYBRID_PER_QUERY_PATH = "results/hybrid_per_query.json"
K_SENSITIVITY_PATH = "results/hybrid_k_sensitivity.json"
COMPARISON_PATH = "results/dense_sparse_hybrid_comparison.json"
VS_PARENTS_PATH = "results/hybrid_vs_parents.json"

PRIMARY_K = 60
K_VALUES = [10, 60, 200]
TOP_N_FUSED = 50  # fusion operates over the saved top-50 lists per retriever

NOTE = (
    "Fusion operates over each retriever's saved top-50 candidate list. A song "
    "ranked, say, 60th by one retriever and not retrieved at all by the other "
    "contributes nothing and cannot surface here -- these numbers are a lower "
    "bound relative to fusing deeper (or full-corpus) candidate sets."
)


def rrf_fuse(dense_list, sparse_list, k):
    scores = defaultdict(float)
    for rank, sid in enumerate(dense_list, start=1):
        scores[sid] += 1.0 / (k + rank)
    for rank, sid in enumerate(sparse_list, start=1):
        scores[sid] += 1.0 / (k + rank)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return [sid for sid, _ in ranked]


def recall_at(ranks, k):
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


def compute_metrics(ranks):
    n = len(ranks)
    mrr = sum((1 / r) if r is not None else 0 for r in ranks) / n
    ndcg10 = sum(
        (1 / math.log2(r + 1)) if r is not None and r <= 10 else 0 for r in ranks
    ) / n
    return {
        "recall@1": recall_at(ranks, 1),
        "recall@5": recall_at(ranks, 5),
        "recall@10": recall_at(ranks, 10),
        "mrr": mrr,
        "ndcg@10": ndcg10,
    }


def main():
    with open(DENSE_TOP50_PATH, encoding="utf-8") as f:
        dense_top50 = json.load(f)
    with open(SPARSE_TOP50_PATH, encoding="utf-8") as f:
        sparse_top50 = json.load(f)

    song_ids = list(dense_top50.keys())
    assert set(song_ids) == set(sparse_top50.keys()), "dense/sparse top-50 query sets differ"
    print(f"{len(song_ids)} queries")

    # fuse once per k value; keep full per-query rank list for each
    ranks_by_k = {}
    for k in K_VALUES:
        ranks = []
        for song_id in song_ids:
            fused = rrf_fuse(dense_top50[song_id], sparse_top50[song_id], k)
            rank = fused.index(song_id) + 1 if song_id in fused else None
            ranks.append(rank)
        ranks_by_k[k] = ranks
        print(f"fused k={k} done")

    primary_ranks = ranks_by_k[PRIMARY_K]
    primary_metrics = compute_metrics(primary_ranks)

    hybrid_baseline = {
        "method": "reciprocal_rank_fusion",
        "n_queries": len(song_ids),
        "k": PRIMARY_K,
        "fused_over_top_n": TOP_N_FUSED,
        "note": NOTE,
        **primary_metrics,
    }
    with open(HYBRID_BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(hybrid_baseline, f, indent=2)

    hybrid_per_query = dict(zip(song_ids, primary_ranks))
    with open(HYBRID_PER_QUERY_PATH, "w", encoding="utf-8") as f:
        json.dump(hybrid_per_query, f, indent=2)

    print(f"\nhybrid (k={PRIMARY_K}), fused over top-{TOP_N_FUSED}:")
    print(f"{'metric':<12}{'value':>10}")
    for name in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"]:
        print(f"{name:<12}{primary_metrics[name]:>10.4f}")
    print(f"saved to {HYBRID_BASELINE_PATH} and {HYBRID_PER_QUERY_PATH}")

    # --- k sensitivity ---
    k_sensitivity = {
        str(k): compute_metrics(ranks_by_k[k]) for k in K_VALUES
    }
    with open(K_SENSITIVITY_PATH, "w", encoding="utf-8") as f:
        json.dump({"note": NOTE, "by_k": k_sensitivity}, f, indent=2)

    print(f"\nk sensitivity (fused over top-{TOP_N_FUSED}):")
    header = f"{'k':<6}" + "".join(f"{m:>12}" for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"])
    print(header)
    for k in K_VALUES:
        row = f"{k:<6}" + "".join(f"{k_sensitivity[str(k)][m]:>12.4f}" for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"])
        print(row)
    print(f"saved to {K_SENSITIVITY_PATH}")

    # --- dense / sparse / hybrid comparison table ---
    with open(DENSE_BASELINE_PATH, encoding="utf-8") as f:
        dense_baseline = json.load(f)
    with open(SPARSE_BASELINE_PATH, encoding="utf-8") as f:
        sparse_baseline = json.load(f)

    comparison = {
        "dense": {m: dense_baseline[m] for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"]},
        "sparse": {m: sparse_baseline[m] for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"]},
        "hybrid": primary_metrics,
        "note": NOTE + " dense/sparse rows here are the original top-20 baselines (D19/D27), unaffected by this rerun.",
    }
    with open(COMPARISON_PATH, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print("\ndense vs sparse vs hybrid:")
    header = f"{'system':<10}" + "".join(f"{m:>12}" for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"])
    print(header)
    for system in ["dense", "sparse", "hybrid"]:
        row = f"{system:<10}" + "".join(f"{comparison[system][m]:>12.4f}" for m in ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"])
        print(row)
    print(f"saved to {COMPARISON_PATH}")

    # --- hybrid vs parents: solves neither found, loses what dense had ---
    with open(DENSE_PER_QUERY_PATH, encoding="utf-8") as f:
        dense_by_id = json.load(f)
    with open(SPARSE_PER_QUERY_PATH, encoding="utf-8") as f:
        sparse_by_id = json.load(f)

    def hit10(d, sid):
        r = d.get(sid)
        return r is not None and r <= 10

    solves_neither = 0
    loses_vs_dense = 0
    for song_id in song_ids:
        hybrid_hit = hybrid_per_query.get(song_id) is not None and hybrid_per_query[song_id] <= 10
        dense_hit = hit10(dense_by_id, song_id)
        sparse_hit = hit10(sparse_by_id, song_id)
        if hybrid_hit and not dense_hit and not sparse_hit:
            solves_neither += 1
        if dense_hit and not hybrid_hit:
            loses_vs_dense += 1

    vs_parents = {
        "hybrid_solves_neither_parent_top10": solves_neither,
        "hybrid_loses_vs_dense_top10": loses_vs_dense,
        "n_queries": len(song_ids),
        "note": "top10 membership for dense/sparse uses the original top-20 per-query files (D19/D27); hybrid uses k=60 fusion over top-50.",
    }
    with open(VS_PARENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(vs_parents, f, indent=2)

    print(f"\nhybrid solves neither parent solved (top10): {solves_neither}")
    print(f"hybrid loses vs dense (dense had top10, hybrid doesn't): {loses_vs_dense}")
    print(f"saved to {VS_PARENTS_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("evaluate_hybrid.py FAILED:")
        traceback.print_exc()
        with open("results/_evaluate_hybrid_error.log", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise
