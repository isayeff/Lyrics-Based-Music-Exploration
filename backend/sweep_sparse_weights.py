"""Sweep ts_rank_cd weight arrays / normalisation flags against the four UI-found
failure cases, to pick the sparse ranking config on evidence rather than a guess."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

# {query: (label, [acceptable target ids])}
TESTS = {
    "eminem killshot": ("A: KILLSHOT", ["OmQcmF5CgKDwHBOP"]),
    "The Cranberries Ridiculous Thoughts": ("B: Ridiculous Thoughts",
                                            ["blY1LX2kILebFED4", "8qK6JfM8qnWmiBIE"]),
    "cranberries": ("C: any Cranberries (control)", None),  # scored by artist match
    "The Cranberries Zombie": ("D: Zombie", ["ayw1SNXO3IZRRHwc", "ttrIlUpcyJYJQkgV",
                                             "BqgP6zIxmViq4NRR"]),
}

# {D,C,B,A} - B is the lyric body, A is artist+title
WEIGHT_SETS = {
    "default {0.1,0.2,0.4,1.0}": [0.1, 0.2, 0.4, 1.0],
    "B=0.10": [0.02, 0.05, 0.10, 1.0],
    "B=0.05": [0.02, 0.05, 0.05, 1.0],
    "B=0.02": [0.02, 0.02, 0.02, 1.0],
}
NORMS = {"0 none": 0, "1 log(len)": 1, "2 len": 2, "16 log(uniq)": 16}


def lexemes_for(conn, query, term_df):
    lex = conn.execute(
        text("SELECT tsvector_to_array(to_tsvector('english', :t))"), {"t": query}
    ).scalar() or []
    lex = sorted(lex, key=lambda l: term_df.get(l, 0))[:20]
    return " | ".join("'" + l.replace("'", "''") + "'" for l in lex)


def ranked(conn, tsq, weights, norm, limit=20):
    return conn.execute(
        text("""
            WITH q AS (SELECT to_tsquery('english', :tsq) AS tsq)
            SELECT song.id, song.song, song.artist,
                   ts_rank_cd(CAST(:w AS float4[]), song.tsv, q.tsq, :norm) AS score
            FROM song, q
            WHERE song.tsv @@ q.tsq
            ORDER BY score DESC, song.id ASC
            LIMIT :lim
        """),
        {"tsq": tsq, "w": weights, "norm": norm, "lim": limit},
    ).fetchall()


def target_rank(rows, targets):
    if targets is None:  # control: first Cranberries row
        for i, r in enumerate(rows, 1):
            if "cranberries" in (r.artist or "").lower():
                return i
        return None
    for i, r in enumerate(rows, 1):
        if r.id in targets:
            return i
    return None


with engine.connect() as conn:
    term_df = dict(conn.execute(
        text("SELECT word, ndoc FROM ts_stat('SELECT tsv FROM song')")).fetchall())
    tsqs = {q: lexemes_for(conn, q, term_df) for q in TESTS}

    header = f"{'config':<34}" + "".join(f"{TESTS[q][0][:14]:>16}" for q in TESTS)
    print(header)
    print("-" * len(header))

    for wname, weights in WEIGHT_SETS.items():
        for nname, norm in NORMS.items():
            cells = []
            for q in TESTS:
                rows = ranked(conn, tsqs[q], weights, norm)
                r = target_rank(rows, TESTS[q][1])
                cells.append("miss" if r is None else f"#{r}")
            print(f"{wname + ' | n=' + nname:<34}" + "".join(f"{c:>16}" for c in cells))
