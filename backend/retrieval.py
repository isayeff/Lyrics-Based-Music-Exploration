"""Shared retrieval logic: dense (pgvector), sparse (Postgres FTS), hybrid (RRF).

Single source of truth for fusion — `evaluate_hybrid.py` imports `rrf_fuse` from
here so the API and the offline evaluation cannot drift apart (D30).
"""
from collections import defaultdict
from sqlalchemy import text

RRF_K = 60          # matches evaluate_hybrid.py PRIMARY_K
FUSION_DEPTH = 50   # each retriever contributes its top-50 (D30)
PROBES = 100        # ivfflat.probes, matches evaluate.py
MAX_QUERY_LEXEMES = 20  # rarest-lexeme filter, matches evaluate_sparse.py (D26)

# ts_rank_cd weights as {D, C, B, A}; A = artist+title, B = lyric body (D26).
# Postgres' default {0.1, 0.2, 0.4, 1.0} makes a title hit worth only 2.5x a
# lyric hit, so repeated lyric mentions swamp exact title/artist matches: the
# query "eminem killshot" ranked "Brainless" (artist name repeated 9x in its
# lyrics) above "KILLSHOT" itself. Widening the A:B gap fixes that (D36).
RANK_WEIGHTS = [0.02, 0.05, 0.05, 1.0]
# Normalisation flag. 1 = divide by 1 + log(document length): a gentle length
# correction, chosen on measurement (D36) — it wins on both the short known-item
# queries and a 300-query sample of the long interpretation queries.
# Flag 2 (divide by raw length) is actively harmful here: it over-penalises long
# lyric bodies and pushed KILLSHOT to rank 12. Flag 16 scored worst of the
# candidates on the interpretation sample (nDCG@10 0.032 vs 0.040 for flag 1).
RANK_NORMALIZATION = 1


# --- fusion ------------------------------------------------------------------

def rrf_score_map(ranked_lists, k=RRF_K):
    """{retriever_name: [song_id, ...]} -> ordered [(song_id, score, {name: rank})].

    Insertion order is retriever order, then rank order, so the stable sort below
    reproduces evaluate_hybrid.py's tie-breaking exactly.
    """
    scores = defaultdict(float)
    contributors = defaultdict(dict)
    for name, ids in ranked_lists.items():
        for rank, sid in enumerate(ids, start=1):
            scores[sid] += 1.0 / (k + rank)
            contributors[sid][name] = rank
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    return [(sid, score, contributors[sid]) for sid, score in ranked]


def rrf_fuse(dense_list, sparse_list, k=RRF_K):
    """Ordered song ids. Kept identical to the offline evaluation (D30)."""
    return [sid for sid, _, _ in rrf_score_map(
        {"dense": dense_list, "sparse": sparse_list}, k
    )]


# --- retrievers --------------------------------------------------------------

def to_vector_literal(vec):
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


def dense_search(conn, query_vec, limit):
    """Cosine nearest neighbours. Returns [(song_id, similarity), ...]."""
    conn.execute(text(f"SET LOCAL ivfflat.probes = {PROBES}"))
    rows = conn.execute(
        text("""
            SELECT id, embedding <=> (:q)::vector AS distance
            FROM song
            ORDER BY distance ASC
            LIMIT :lim
        """),
        {"q": to_vector_literal(query_vec), "lim": limit},
    ).fetchall()
    return [(r.id, 1.0 - float(r.distance)) for r in rows]


def build_or_tsquery(conn, query_text, term_df):
    """OR of the query's rarest lexemes — see D26/D27 for why not plainto_tsquery."""
    lexemes = conn.execute(
        text("SELECT tsvector_to_array(to_tsvector('english', :t))"), {"t": query_text}
    ).scalar()
    if not lexemes:
        return None
    lexemes = sorted(lexemes, key=lambda lex: term_df.get(lex, 0))[:MAX_QUERY_LEXEMES]
    return " | ".join("'" + lex.replace("'", "''") + "'" for lex in lexemes)


def sparse_search(conn, query_text, limit, term_df):
    """Lexical FTS ranked by ts_rank_cd. Returns [(song_id, rank_score), ...].

    `song.id ASC` is a deterministic tiebreak: with A dominant and no IDF term,
    short queries produce many exactly-tied scores, and without it Postgres is
    free to reshuffle identical searches between runs.
    """
    tsq_input = build_or_tsquery(conn, query_text, term_df)
    if tsq_input is None:
        return []
    rows = conn.execute(
        text("""
            WITH q AS (SELECT to_tsquery('english', :tsq) AS tsq)
            SELECT song.id,
                   ts_rank_cd(CAST(:w AS float4[]), song.tsv, q.tsq, :norm) AS score
            FROM song, q
            WHERE song.tsv @@ q.tsq
            ORDER BY score DESC, song.id ASC
            LIMIT :lim
        """),
        {"tsq": tsq_input, "w": RANK_WEIGHTS, "norm": RANK_NORMALIZATION, "lim": limit},
    ).fetchall()
    return [(r.id, float(r.score)) for r in rows]


def load_term_df(conn):
    """Corpus-wide lexeme document frequencies for the rarest-lexeme filter."""
    return dict(
        conn.execute(text("SELECT word, ndoc FROM ts_stat('SELECT tsv FROM song')")).fetchall()
    )


def search(conn, mode, query_text, query_vec, limit, term_df):
    """Returns [(song_id, score, {retriever: rank}), ...] ranked best-first."""
    if mode == "dense":
        hits = dense_search(conn, query_vec, limit)
        return [(sid, score, {"dense": i}) for i, (sid, score) in enumerate(hits, start=1)]

    if mode == "sparse":
        hits = sparse_search(conn, query_text, limit, term_df)
        return [(sid, score, {"sparse": i}) for i, (sid, score) in enumerate(hits, start=1)]

    # hybrid: fuse each retriever's top-FUSION_DEPTH, exactly as in D30
    dense_ids = [sid for sid, _ in dense_search(conn, query_vec, FUSION_DEPTH)]
    sparse_ids = [sid for sid, _ in sparse_search(conn, query_text, FUSION_DEPTH, term_df)]
    fused = rrf_score_map({"dense": dense_ids, "sparse": sparse_ids})
    return fused[:limit]
