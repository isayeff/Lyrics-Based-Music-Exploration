import os, glob
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
DATA = "../data/music4all"

# CSVs are TAB-separated despite .csv extension
info   = pd.read_csv(f"{DATA}/id_information.csv", sep="\t")
lang   = pd.read_csv(f"{DATA}/id_lang.csv", sep="\t")
genres = pd.read_csv(f"{DATA}/id_genres.csv", sep="\t")
tags   = pd.read_csv(f"{DATA}/id_tags.csv", sep="\t")

print("columns:", list(info.columns))   # check names on first run

df = (info
      .merge(lang, on="id")
      .merge(genres, on="id", how="left")
      .merge(tags, on="id", how="left"))

df = df[df["lang"] == "en"].copy()

def snippet(song_id):
    path = f"{DATA}/lyrics/{song_id}.txt"
    if not os.path.exists(path):
        return None
    txt = open(path, encoding="utf-8").read().strip()
    if not txt or txt.upper() == "INSTRUMENTAL":
        return None
    return "\n".join(txt.splitlines()[:4])   # snippet only (copyright)

df["lyric_snippet"] = df["id"].map(snippet)
df = df[df["lyric_snippet"].notna()].copy()

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

df.to_sql("song", engine, if_exists="replace", index=False)
print("loaded", len(df), "songs")