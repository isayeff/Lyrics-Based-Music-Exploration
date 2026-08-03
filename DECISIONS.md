# DECISIONS.md

Running log of non-trivial decisions and their rationale. **Append-only** — don't rewrite history; if a decision changes, add a new entry that supersedes the old one. This is raw material for the Methodology and Results chapters (the "why we chose X" markers look for).

**Entry format:**
```
## D<n> — <short title>  (<date>)
Decision: <what was decided>
Why: <rationale that justifies it in the dissertation>
Alternatives considered: <what was rejected and why>
Status: active | superseded by D<n>
```

---

## Flagged for ethics application (running list)
Add anything here that will need ethics cover, so it goes in one application:
- Use of the Song Interpretation Dataset (user-written secondary content) — self-declaration route, in progress.
- [Any future user study / participant evaluation — currently out of scope.]

---

## D1 — Core thesis: free-text semantic retrieval  
Decision: Core system matches natural-language descriptions to songs using Sentence-BERT embeddings + vector retrieval, with artist-level NER profiling.
Why: Prior lyrics-exploration work (LyricsRadar, Lyric Jumper, Query-by-Blending) and both predecessor Sheffield projects rely on topic models / TF-IDF / Word2Vec, none supporting free-text natural-language description queries via modern sentence embeddings. That gap is the novelty.
Alternatives considered: Reproducing an LDA/topic-model explorer (already done in the literature; no contribution).
Status: active

## D2 — Offline evaluation via Song Interpretation Dataset  
Decision: Primary evaluation is offline: held-out interpretations as queries, correct song as ground truth. Metrics: Recall@k, MRR, nDCG.
Why: Rigorous and reproducible; sidesteps the known difficulty of evaluating unsupervised topics; involves no human participants, keeping the project on the lighter ethics route.
Alternatives considered: User study (needs full ethics approval + participants + time; deferred to further work).
Status: active

## D3 — Scope cuts to "further work"  
Decision: RL taste modelling, collaborative filtering, hybrid recommendation, like/dislike loops are written up as further work, not built.
Why: All need many users and interaction logs unavailable here, and trigger heavy participant-data ethics. Each is a separate project. "Further work" is a marked section, so the analysis still earns credit.
Alternatives considered: Building a hybrid recommender (scope explosion on a 6-week clock).
Status: active

## D4 — Storage: FAISS + SQLite  
Decision: Vectors in a FAISS index; metadata in SQLite.
Why: Simplest reproducible single-node setup.
Status: **superseded by D9**

## D5 — Lyrics source + copyright stance  
Decision: If music4all lacks lyrics, fetch per-song from Genius/lyrics.ovh; cache raw lyrics locally (git-ignored); persist only embeddings/features + short snippets; never commit or redistribute full lyric text.
Why: Non-commercial research processing is covered by the UK research text-and-data-mining exception; redistribution of full lyrics is not. Features + snippets keep us clean.
Alternatives considered: Storing full lyrics (copyright risk); MSD bag-of-words (too restrictive).
Status: active — CONFIRMED: 109,269 lyric .txt files present, filename = song id. No Genius/lyrics.ovh fetch needed. Filter out files containing only "INSTRUMENTAL"; light-clean ad-libs/section markers.

## D6 — Spotify embed for playback  
Decision: Spotify embed iframe for the 30-sec player; resolve track IDs via Web API client-credentials (app-only token).
Why: No user login -> no personal data -> clean for ethics; trivial to integrate.
Alternatives considered: Spotify Web Playback SDK (needs Premium + OAuth; no dissertation benefit).
Status: active — SIMPLIFIED: Spotify track IDs already present in id_metadata.csv; no Web API search needed for the player.

## D7 — LLM summarisation is offline & optional  
Decision: Any LLM lyric summarisation runs offline as batch enrichment, never at query time. Optional.
Why: Keeps the system reproducible and free of a runtime API dependency; core must work without it.
Status: active

## D8 — Project framed as Experimental  
Decision: Structure the dissertation as an Experimental project.
Why: Expected of an advanced MSc; the evaluation-driven SBERT-vs-baseline comparison is the experiment.
Alternatives considered: Design & Build (fits the web app but underweights the experimental contribution).
Status: active — **to confirm with supervisor**

## D9 — Storage: PostgreSQL + pgvector    [supersedes D4]
Decision: Single store — PostgreSQL with the pgvector extension holds both metadata and embeddings, and performs vector similarity search. Run via Docker.
Why: One system instead of two (drops the separate FAISS index); pgvector's exact search is fast enough at our scale (tens of thousands of songs); production-grade and cleaner to describe. FAISS kept only as an optional later comparison (exact vs approximate retrieval).
Alternatives considered: SQLite + FAISS (D4 — simpler to start but two stores, and SQLite has no vector search); MongoDB (predecessor used it; less natural for vector search).
Status: active

## D11 — Ethics approach: build fully, flag, apply once  
Decision: Build all components without ethics-based blocking. Maintain the flagged list above; cover all flagged items in a single application; remove any part that is rejected.
Why: Building software and processing secondary data offline is not participant research and needs no prior approval. The only activity that must wait for approval is a live user study, which is out of core scope.
Status: active

## D12 — music4all files are tab-separated  (date)
Decision: Load all id_*.csv and listening_history.csv with sep='\t'.
Why: Readme states columns are tab-delimited despite the .csv extension; default comma parsing collapses each row into one column.
Status: active

## D13 — Catalogue loaded  (date)
Decision: 84,103 English songs ingested into Postgres `song` table (instrumentals + empty lyrics dropped).
Why: Confirms music4all is sufficient as the catalogue; no external lyric fetching needed.
Status: active