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

## D14 — Lyric embeddings: SBERT + pgvector ivfflat  (2026-08-03)
Decision: `backend/embed.py` reads full lyrics from `data/music4all/lyrics/{id}.txt` (per-song files on disk — full text is never stored in Postgres, only in the git-ignored local cache), embeds each with `all-MiniLM-L6-v2` (384-dim) in batches of 128, stores vectors in a new `song.embedding vector(384)` column, then builds an `ivfflat` index with `vector_cosine_ops` and `lists = 100`. Resumable via `WHERE embedding IS NULL`.
Why: Matches D1/D9 — SBERT dense retrieval, single pgvector store. Cosine chosen over L2/inner-product since SBERT similarity is orientation-based, not magnitude-based. `lists=100` follows pgvector's own `rows/1000` guideline for ~84k rows. Storing only embeddings (not full lyric text) in the DB keeps D5's copyright stance intact.
Alternatives considered: HNSW index (better recall/speed at query time but slower to build and more memory; ivfflat is the documented default for this scale and simpler to justify in the write-up).
Status: active

## D15 — Ethics route confirmed by supervisor  (2026-08-03)
Decision: Self-declaration for the Song Interpretation Dataset; no full application (no human subjects in evaluation). Confirmed by Varvara via email, 2026-08-03.
Why: Offline evaluation uses only pre-existing secondary human data.
Status: active

## D16 — Embeddings complete + duplicate songs observed  (2026-08-03)
Decision: All 84,103 songs embedded (all-MiniLM-L6-v2, 384-dim); ivfflat cosine index built and verified. Nearest-neighbour sanity check passed. Noted: catalogue contains near-duplicate songs (e.g. same track with punctuation variants) — to consider when computing evaluation metrics.
Status: active

## D17 — Search is multi-modal; adopt hybrid retrieval + reranking  (date)
Decision: Move from pure dense (SBERT) retrieval to a hybrid architecture — dense (SBERT) + sparse (Postgres full-text/BM25 over metadata + lyrics), fused with Reciprocal Rank Fusion, with an optional cross-encoder (ms-marco-MiniLM) reranking stage. Genre = soft signal (optional). Listening-history personalisation = further work.
Why: Diagnostic testing showed dense retrieval fails known-item ("eminem lose yourself") and lyric-fragment ("hurry hurry step right up") queries — structurally, not fixably by tuning. Hybrid + rerank is the established fix; the dense/sparse/hybrid/rerank comparison becomes the core evaluation.
Status: active — to build after the evaluation harness so each stage is measured, not assumed.

## D18 — Song Interpretation Dataset sized against catalogue  (2026-08-06)
Decision: Counted `data/songInterpretation/dataset_full_256_clean.json` (not loaded into DB yet). 310,315 interpretation records over 20,672 distinct `music4all_id`s. All 20,672 dataset songs are present in the 84,103-song English-filtered `song` table (100% overlap) — so all 310,315 interpretations are usable as evaluation queries.
Why: Confirms the eval set (D2) is fully covered by the catalogue before building the query/ground-truth loading pipeline; no interpretations will be dropped for missing songs.
Status: active

## D19 — Dense-only baseline measured  (2026-08-06)
Decision: `backend/evaluate.py` — one interpretation per song sampled with fixed seed (42) as query (20,672 queries), embedded with `all-MiniLM-L6-v2`, searched against `song.embedding` via pgvector cosine distance (`SET LOCAL ivfflat.probes = 100`, i.e. near-exhaustive since `lists=100`), top-20 retrieved. Result: Recall@1=0.099, Recall@5=0.152, Recall@10=0.176, MRR=0.124, nDCG@10=0.135. Saved to `backend/results/dense_baseline.json`.
Why: Establishes the dense-only number the D17 hybrid architecture is meant to beat. Confirms D17's diagnostic finding at full scale, not just spot-checked queries — dense embeddings alone recover the source song for only ~18% of real user interpretations within the top 10, well short of ceiling.
Alternatives considered: Vote-filtering interpretations to a "best" one per song — dataset has no vote/score field (this "Dataset Full" length-cleaned variant excludes it by design), so selection is a fixed-seed random pick per song instead.
Status: active

## D19 — Eval set = Dataset Full, one interpretation per song, no vote filter  (2026-08-06)
Decision: Use the downloaded dataset_full_256_clean.json (= paper's "Dataset Full": 279,283 train + 31,032 valid = 310,315 interpretations). Already length-filtered (256-char min removes meaningless short ones). No vote field in this release; vote-filtered subsets are separate smaller files. Sample one interpretation per song (~20,672 queries) as the held-out evaluation set.
Why: Length-cleaning already removes the main quality risk; vote filtering unavailable in this file and not required. Confirmed against Zhang et al. (ISMIR 2022), whose §5.3 runs the same SBERT+MRR description→song retrieval — our evaluation follows established methodology and can benchmark against their ~26–32% MRR.
Status: active

## D20 — Ethics self-declaration submitted  (2026-08-08)
Decision: Self-declaration (Application 076709) submitted and signed via the Ethics Application System. Route: re-use of existing secondary data. Questionnaire answers: no primary collection; public-repository exemption applied; no re-identification; consent not originally sought but data anonymised/uncontactable (acceptable per policy); no offence risk. Awaiting supervisor countersign + Ethics Administrator check → confirmation letter for the dissertation appendix.
Why: Confirms the ethics route Varvara advised; unblocks reporting evaluation results as final once the letter is issued.
Status: active — pending confirmation letter