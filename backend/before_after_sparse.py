"""Before/after top-5 for the four UI-found failure cases (D36 deliverable 1)."""
import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import retrieval

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

OLD = ([0.1, 0.2, 0.4, 1.0], 0)                                  # Postgres defaults
NEW = (retrieval.RANK_WEIGHTS, retrieval.RANK_NORMALIZATION)     # chosen config

QUERIES = ["eminem killshot", "The Cranberries Ridiculous Thoughts",
           "cranberries", "The Cranberries Zombie"]
TARGETS = {
    "eminem killshot": ["OmQcmF5CgKDwHBOP"],
    "The Cranberries Ridiculous Thoughts": ["blY1LX2kILebFED4", "8qK6JfM8qnWmiBIE"],
    "cranberries": None,
    "The Cranberries Zombie": ["ayw1SNXO3IZRRHwc", "ttrIlUpcyJYJQkgV", "BqgP6zIxmViq4NRR"],
}
OUT_PATH = "results/sparse_before_after.json"


def run(conn, query, weights, norm, term_df, limit=20):
    tsq = retrieval.build_or_tsquery(conn, query, term_df)
    if tsq is None:
        return []
    return conn.execute(
        text("""
            WITH q AS (SELECT to_tsquery('english', :tsq) AS tsq)
            SELECT song.id, song.song, song.artist,
                   ts_rank_cd(CAST(:w AS float4[]), song.tsv, q.tsq, :norm) AS score
            FROM song, q WHERE song.tsv @@ q.tsq
            ORDER BY score DESC, song.id ASC LIMIT :lim
        """),
        {"tsq": tsq, "w": weights, "norm": norm, "lim": limit},
    ).fetchall()


def target_rank(rows, targets):
    if targets is None:
        for i, r in enumerate(rows, 1):
            if "cranberries" in (r.artist or "").lower():
                return i
        return None
    for i, r in enumerate(rows, 1):
        if r.id in targets:
            return i
    return None


report = {}
with engine.connect() as conn:
    term_df = retrieval.load_term_df(conn)
    for q in QUERIES:
        before = run(conn, q, *OLD, term_df)
        after = run(conn, q, *NEW, term_df)
        rb, ra = target_rank(before, TARGETS[q]), target_rank(after, TARGETS[q])
        report[q] = {
            "target_rank_before": rb, "target_rank_after": ra,
            "top5_before": [{"rank": i, "title": r.song, "artist": r.artist,
                             "score": round(float(r.score), 4)}
                            for i, r in enumerate(before[:5], 1)],
            "top5_after": [{"rank": i, "title": r.song, "artist": r.artist,
                            "score": round(float(r.score), 4)}
                           for i, r in enumerate(after[:5], 1)],
        }

        print(f"\n=== {q} ===")
        print(f"  target rank: {rb or 'MISS'}  ->  {ra or 'MISS'}")
        print(f"  {'BEFORE (default w, n=0)':<44} | AFTER (B=0.05, n=16)")
        for i in range(5):
            b = before[i] if i < len(before) else None
            a = after[i] if i < len(after) else None
            bs = f"{i+1}. {b.song[:26]:26} {float(b.score):6.3f}" if b else ""
            as_ = f"{i+1}. {a.song[:26]:26} {float(a.score):6.3f}" if a else ""
            print(f"  {bs:<44} | {as_}")

os.makedirs("results", exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump({"old_config": {"weights_DCBA": OLD[0], "normalization": OLD[1]},
               "new_config": {"weights_DCBA": NEW[0], "normalization": NEW[1]},
               "queries": report}, f, indent=2)
print(f"\nsaved to {OUT_PATH}")
