import os
import re
import json
import random
from collections import defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATASET_PATH = "../data/songInterpretation/dataset_full_256_clean.json"
LYRICS_DIR = "../data/music4all/lyrics"
SEED = 42
SAMPLE_SIZE = 30
SPAN_LEN = 5

DENSE_PER_QUERY_PATH = "results/dense_per_query.json"
SPARSE_PER_QUERY_PATH = "results/sparse_per_query.json"
EXAMPLES_PATH = "results/sparse_only_examples.json"

random.seed(SEED)

# identical query sampling to evaluate.py / evaluate_sparse.py: same file, same
# seed -> same (song_id -> query_text) picks
with open(DATASET_PATH, encoding="utf-8") as f:
    records = json.load(f)

by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])

query_text_by_id = {
    song_id: random.choice(comments) for song_id, comments in by_song.items()
}

with open(DENSE_PER_QUERY_PATH, encoding="utf-8") as f:
    dense_by_id = json.load(f)
with open(SPARSE_PER_QUERY_PATH, encoding="utf-8") as f:
    sparse_by_id = json.load(f)

sparse_only_ids = [
    song_id
    for song_id in query_text_by_id
    if sparse_by_id.get(song_id) is not None
    and sparse_by_id[song_id] <= 10
    and (dense_by_id.get(song_id) is None or dense_by_id[song_id] > 10)
]
print(f"sparse-only (correct song in top10 for sparse, not dense): {len(sparse_only_ids)}")

with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT id, artist, song FROM song WHERE id = ANY(:ids)"),
        {"ids": sparse_only_ids},
    ).fetchall()
meta_by_id = {r[0]: {"artist": r[1], "title": r[2]} for r in rows}


def read_lyrics(song_id):
    with open(f"{LYRICS_DIR}/{song_id}.txt", encoding="utf-8") as f:
        return f.read().strip()


def tokenize(s):
    return re.findall(r"\w+", s.lower())


def ngrams(tokens, n):
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


# 30-example sample, independent RNG so it doesn't perturb the query-sampling
# random stream above
sampler = random.Random(SEED)
sample_ids = sampler.sample(sparse_only_ids, SAMPLE_SIZE)

examples = []
for song_id in sample_ids:
    meta = meta_by_id[song_id]
    examples.append({
        "song_id": song_id,
        "query_text": query_text_by_id[song_id],
        "artist": meta["artist"],
        "title": meta["title"],
        "sparse_rank": sparse_by_id[song_id],
        "dense_rank": dense_by_id.get(song_id),
    })

os.makedirs("results", exist_ok=True)
with open(EXAMPLES_PATH, "w", encoding="utf-8") as f:
    json.dump(examples, f, indent=2)
print(f"saved {len(examples)} examples to {EXAMPLES_PATH}")

# leakage check over all 435: does the query text contain the title, the
# artist, or a verbatim 5+ word span of the song's own lyrics?
title_hits = artist_hits = lyric_span_hits = 0
for song_id in sparse_only_ids:
    meta = meta_by_id[song_id]
    query_text = query_text_by_id[song_id]
    q_lower = query_text.lower()

    if meta["title"] and meta["title"].lower() in q_lower:
        title_hits += 1
    if meta["artist"] and meta["artist"].lower() in q_lower:
        artist_hits += 1

    lyrics = read_lyrics(song_id)
    lyric_grams = ngrams(tokenize(lyrics), SPAN_LEN)
    query_grams = ngrams(tokenize(query_text), SPAN_LEN)
    if lyric_grams & query_grams:
        lyric_span_hits += 1

n = len(sparse_only_ids)
print(f"\n{'signal':<25}{'count':>8}{'pct':>8}")
print(f"{'title in query':<25}{title_hits:>8}{title_hits/n*100:>7.1f}%")
print(f"{'artist in query':<25}{artist_hits:>8}{artist_hits/n*100:>7.1f}%")
print(f"{'5+ word lyric span':<25}{lyric_span_hits:>8}{lyric_span_hits/n*100:>7.1f}%")
