"""Deliverable 2 (D36): dense / sparse-old / sparse-new / hybrid-old / hybrid-new
across Recall@{1,5,10}, MRR, nDCG@10."""
import json
import os

METRICS = ["recall@1", "recall@5", "recall@10", "mrr", "ndcg@10"]
OUT_PATH = "results/comparison_v1_vs_v2.json"

SYSTEMS = [
    ("dense",       "results/dense_baseline.json"),
    ("sparse-old",  "results/sparse_baseline.json"),
    ("sparse-new",  "results/sparse_baseline_v2.json"),
    ("hybrid-old",  "results/hybrid_baseline.json"),
    ("hybrid-new",  "results/hybrid_baseline_v2.json"),
]

table = {}
for name, path in SYSTEMS:
    if not os.path.exists(path):
        print(f"  (missing: {path} - skipped)")
        continue
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    table[name] = {m: data[m] for m in METRICS}

header = f"{'system':<13}" + "".join(f"{m:>11}" for m in METRICS)
print(header)
print("-" * len(header))
for name, _ in SYSTEMS:
    if name in table:
        print(f"{name:<13}" + "".join(f"{table[name][m]:>11.4f}" for m in METRICS))

# deltas that matter for the write-up
if "sparse-old" in table and "sparse-new" in table:
    print("\nsparse change (new vs old):")
    for m in METRICS:
        o, n = table["sparse-old"][m], table["sparse-new"][m]
        mult = f"{n / o:.2f}x" if o else "n/a"
        print(f"  {m:<11}{o:.4f} -> {n:.4f}  ({mult})")

if "hybrid-old" in table and "hybrid-new" in table:
    print("\nhybrid change (new vs old):")
    for m in METRICS:
        o, n = table["hybrid-old"][m], table["hybrid-new"][m]
        mult = f"{n / o:.2f}x" if o else "n/a"
        print(f"  {m:<11}{o:.4f} -> {n:.4f}  ({mult})")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump({"systems": table,
               "note": ("sparse-new/hybrid-new use the D36 ts_rank_cd weights "
                        "{0.02,0.05,0.05,1.0} with normalisation flag 1 and an "
                        "id tiebreak. Query set, seed and dense arm are unchanged.")},
              f, indent=2)
print(f"\nsaved to {OUT_PATH}")
