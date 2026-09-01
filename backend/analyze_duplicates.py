"""Quantify near-duplicate song records and how many evaluation songs they affect.

If the ground-truth song_id sits in a duplicate group and retrieval returns its
twin, the harness scores a miss — so duplicates may be depressing the reported
numbers for all three retrievers.
"""
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
OUT_PATH = "results/duplicate_analysis.json"
SEED = 42

# strip version/edition qualifiers so "Zombie", "Zombie (Acoustic Version)" and
# "Zombie - Acoustic Version" collapse to the same key
QUALIFIER = re.compile(
    r"\s*[-(\[]\s*(acoustic|live|remaster(ed)?|radio|single|album|deluxe|explicit|clean|"
    r"instrumental|demo|mono|stereo|remix|edit|version|mix|bonus|reprise|extended)\b.*$",
    re.I,
)


def norm_title(title):
    t = (title or "").lower()
    t = QUALIFIER.sub("", t)
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_artist(artist):
    a = (artist or "").lower()
    a = re.sub(r"^the\s+", "", a)
    a = re.sub(r"[^\w\s]", "", a)
    return re.sub(r"\s+", " ", a).strip()


with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, artist, song FROM song")).fetchall()
print(f"{len(rows)} songs in catalogue")

groups = defaultdict(list)
for r in rows:
    groups[(norm_artist(r.artist), norm_title(r.song))].append(r.id)

dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
songs_in_dup = {sid for ids in dup_groups.values() for sid in ids}

print(f"duplicate groups: {len(dup_groups)}")
print(f"songs sitting in a duplicate group: {len(songs_in_dup)} "
      f"({len(songs_in_dup) / len(rows) * 100:.1f}% of catalogue)")

# how many of the 20,672 evaluation songs are affected
random.seed(SEED)
with open(DATASET_PATH, encoding="utf-8") as f:
    records = json.load(f)
by_song = defaultdict(list)
for r in records:
    by_song[r["music4all_id"]].append(r["comment"])
eval_ids = [sid for sid, _ in [(s, random.choice(c)) for s, c in by_song.items()]]

affected = [sid for sid in eval_ids if sid in songs_in_dup]
print(f"evaluation songs in a duplicate group: {len(affected)}/{len(eval_ids)} "
      f"({len(affected) / len(eval_ids) * 100:.1f}%)")

sizes = defaultdict(int)
for ids in dup_groups.values():
    sizes[len(ids)] += 1
print("group sizes:", dict(sorted(sizes.items())))

examples = []
for (artist, title), ids in list(dup_groups.items())[:2000]:
    if len(ids) >= 3:
        by_id = {r.id: r for r in rows if r.id in ids}
        examples.append({"artist": artist, "key_title": title,
                         "records": [{"id": i, "song": by_id[i].song} for i in ids]})
    if len(examples) >= 5:
        break

out = {
    "catalogue_size": len(rows),
    "duplicate_groups": len(dup_groups),
    "songs_in_duplicate_group": len(songs_in_dup),
    "pct_catalogue_in_duplicate_group": round(len(songs_in_dup) / len(rows) * 100, 2),
    "eval_songs": len(eval_ids),
    "eval_songs_in_duplicate_group": len(affected),
    "pct_eval_in_duplicate_group": round(len(affected) / len(eval_ids) * 100, 2),
    "group_size_histogram": {str(k): v for k, v in sorted(sizes.items())},
    "examples": examples,
    "note": ("Grouping key is normalised artist + title with version/edition qualifiers "
             "stripped. This is an upper-bound estimate of the duplicate problem: some "
             "same-title pairs are genuinely different recordings."),
}
os.makedirs("results", exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"saved to {OUT_PATH}")
for ex in examples[:3]:
    print(" ", ex["artist"], "|", [r["song"] for r in ex["records"]])
