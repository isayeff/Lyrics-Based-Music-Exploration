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


## D19 — Eval set = Dataset Full, one interpretation per song, no vote filter  (2026-08-06)
Decision: Use the downloaded dataset_full_256_clean.json (= paper's "Dataset Full": 279,283 train + 31,032 valid = 310,315 interpretations). Already length-filtered (256-char min removes meaningless short ones). No vote field in this release; vote-filtered subsets are separate smaller files. Sample one interpretation per song (~20,672 queries) as the held-out evaluation set.
Why: Length-cleaning already removes the main quality risk; vote filtering unavailable in this file and not required. Confirmed against Zhang et al. (ISMIR 2022), whose §5.3 runs the same SBERT+MRR description→song retrieval — our evaluation follows established methodology and can benchmark against their ~26–32% MRR.
Status: active

## D20 — Ethics self-declaration submitted  (2026-08-08)
Decision: Self-declaration (Application 076709) submitted and signed via the Ethics Application System. Route: re-use of existing secondary data. Questionnaire answers: no primary collection; public-repository exemption applied; no re-identification; consent not originally sought but data anonymised/uncontactable (acceptable per policy); no offence risk. Awaiting supervisor countersign + Ethics Administrator check → confirmation letter for the dissertation appendix.
Why: Confirms the ethics route Varvara advised; unblocks reporting evaluation results as final once the letter is issued.
Status: active — pending confirmation letter

## D21 — Dense-only baseline measured  (2026-08-06)
Decision: `backend/evaluate.py` — one interpretation per song sampled with fixed seed (42) as query (20,672 queries), embedded with `all-MiniLM-L6-v2`, searched against `song.embedding` via pgvector cosine distance (`SET LOCAL ivfflat.probes = 100`, i.e. near-exhaustive since `lists=100`), top-20 retrieved. Result: Recall@1=0.099, Recall@5=0.152, Recall@10=0.176, MRR=0.124, nDCG@10=0.135. Saved to `backend/results/dense_baseline.json`.
Why: Establishes the dense-only number the D17 hybrid architecture is meant to beat. Confirms D17's diagnostic finding at full scale, not just spot-checked queries — dense embeddings alone recover the source song for only ~18% of real user interpretations within the top 10, well short of ceiling.
Alternatives considered: Vote-filtering interpretations to a "best" one per song — dataset has no vote/score field (this "Dataset Full" length-cleaned variant excludes it by design), so selection is a fixed-seed random pick per song instead.
Status: active

## D22 — Baseline sanity check passed  (2026-08-10)
Decision: Manually verified 5 random queries — all correct songs present in table with embeddings; misses are genuine ranking misses, not data gaps. Baseline (D21) confirmed trustworthy. Observed failure modes: vague/emotional interpretations (low signal) and title-bearing interpretations missed by dense (e.g. "Wild Wood" ranked 17 despite title in query) — the latter is the hybrid target.
Status: active

## D23 — Ethics approval received  (2026-08-20)
Decision: Self-declaration approved 11/08/2026 (Application 076709, Eden Fowler, Departmental Ethics Administrator). Letter saved for dissertation appendix alongside the application PDF.
Note: Any significant deviation from the approved documentation (e.g. adding human participants) requires informing the Ethics Administrator; full review may then be needed.
Status: closed — supersedes D20

## D24 — Typo tolerance deferred to further work  (2026-08-26)
Decision: No fuzzy string matching on artist/title. Postgres full-text is exact-token; SBERT degrades gracefully but unreliably on misspellings.
Why: The SID evaluation set contains no meaningful typo cases, so this would not affect measured results. pg_trgm on artist/song is the natural fix if pursued.
Status: active — logged as further work

## D25 — User accounts with synthetic credentials  (date)
Decision: Implement real auth (Postgres user table, hashed passwords, JWT) using fabricated emails/passwords only. Enables listening history, taste onboarding, and personalised home screen.
Why: No real personal data is collected, so no data subjects exist and the ethics self-declaration (D23) is unaffected. Only recruiting real users and reporting their data would constitute a deviation requiring notification.
Status: active

## D26 — Sparse queries filtered to K rarest lexemes  (date)
Decision: For each query, keep only the ~15-20 lowest document-frequency lexemes (df precomputed corpus-wide via ts_stat) before OR-joining into the tsquery.
Why: OR-of-all-lexemes matched 61,451/84,103 songs (73% of corpus) per query, and ts_rank_cd applies no IDF weighting — so ubiquitous terms ("love", "never") contributed as much as distinctive ones, diluting ranking quality. Restricting to rare lexemes approximates the IDF weighting that BM25 provides natively, making the sparse baseline a fairer stand-in for BM25. Also reduces runtime from ~3.3h to tractable.
Status: active

## D27 — Sparse (lexical FTS) baseline measured; dense vs sparse overlap  (2026-08-30)
Decision: Added `song.tsv tsvector` (weighted: artist+title = A, full lyrics = B via `setweight`) built by `backend/index_sparse.py`, GIN-indexed (`idx_song_tsv_gin`), resumable/idempotent (`WHERE tsv IS NULL`). `backend/evaluate_sparse.py` reuses the exact same query set as `evaluate.py` (same file, same `random.seed(42)` sampling) for direct comparability, then ranks candidates with `ts_rank_cd` over an OR-of-rarest-20-lexemes tsquery (D26). Result: Recall@1=0.007, Recall@5=0.026, Recall@10=0.044, MRR=0.017, nDCG@10=0.022 — well below dense (D21: nDCG@10=0.135). Overlap (correct song in top 10): both=466, dense-only=3173, sparse-only=435, neither=16598. Saved to `backend/results/sparse_baseline.json`, `sparse_per_query.json`, `dense_vs_sparse_overlap.json`; dense per-query ranks also now saved to `backend/results/dense_per_query.json` (added to evaluate.py) so overlap could be computed without re-running dense retrieval.
Why: A first spec-literal attempt used `plainto_tsquery`/`websearch_to_tsquery` as named in the original plan — both AND every query lexeme together. Interpretation-comment queries run 50-300+ words, so requiring the full vocabulary in one song's tsvector matched only 3/20,672 queries (recall@10 ≈ 0.0001), which is a broken query, not a real measurement of lexical retrieval quality. Fixed by building the tsquery as an OR of lexemes instead (`to_tsquery` from `tsvector_to_array`, lexemes quoted to survive stray punctuation) — this OR-of-everything then matched ~73% of the corpus per query, which is what D26's rarest-lexeme filter fixes.
Sparse alone is markedly weaker than dense, consistent with D17: user interpretations paraphrase meaning in their own words rather than reusing lyric/title vocabulary. But sparse uniquely recovers 435 songs dense misses entirely — real complementary signal, supporting D17's hybrid/RRF direction rather than dense-alone.
Observed data-quality wrinkle (not fixed, just noted): for some queries the "rarest" lexemes chosen were scraper/forum boilerplate fragments (e.g. `linkno`, `replyther`, `movedand` — leftover HTML/page-chrome text in the interpretation comments), not meaningful content words. Worth a cleaning pass before this number is treated as more than a baseline.
Status: active

## D28 — Why sparse wins where dense misses: lexical leakage, not semantic strength  (2026-08-30)
Decision: `backend/analyze_sparse_only.py` isolated the 435 D27 sparse-only queries (correct song in sparse top 10, not dense top 10), saved a 30-example sample (seed 42) to `backend/results/sparse_only_examples.json` (query text, artist, title, both ranks), then measured over all 435 whether the query text contains the song title, the artist name, or a verbatim 5+ word contiguous span of that song's own lyrics (case-insensitive). Result: title in query 58.6% (255/435), artist in query 28.3% (123/435), 5+ word lyric span 46.2% (201/435).
Why: Confirms sparse's 435 wins over dense (D27) are not evidence of general lexical-retrieval strength — they're overwhelmingly queries that leak the answer verbatim (commenters naming the title/artist directly, or quoting a lyric line as evidence for their interpretation, e.g. "Apply Some Pressure" quoted almost verbatim in its own interpretation). Dense SBERT is comparatively weak on these because near-verbatim short quoted spans don't dominate a mean-pooled sentence embedding of a long paraphrasing comment the way an exact keyword match dominates `ts_rank_cd`. This sharpens the hybrid case from D17/D27: sparse's contribution isn't "different semantic coverage," it's "exact-match recovery when the user happens to quote the answer" — a real, complementary, but narrower signal than raw overlap numbers suggested.
Status: active

## D29 — Passage-level embedding deferred to further work  (2026-08-30)
Decision: Retain whole-song embedding. Passage-level (chunk) embedding is documented as further work rather than implemented. A pilot on a ~5,000-song subset remains optional if the write-up is ahead of schedule after 10 September.
Why: D28 showed 46.2% of sparse-only wins contained a verbatim 5+ word lyric span, and dense misses these because mean-pooling over a full lyric text dilutes any single line (the same mechanism behind the "Hurry hurry, step right up" probe failure). Passage-level embedding addresses this directly, and — since misremembered lyrics tend to preserve semantic and rhythmic structure — would also cover lexical-substitution errors that sparse retrieval cannot handle. However, chunking 84,103 songs yields roughly 0.5-1M passages: ~10x the original embedding cost, plus new schema, index, fusion logic and evaluation. With the dissertation due 16 September, writing is the binding constraint, not implementation.
Important qualification: passage-level is not superior to whole-song, only better on different query types (quotation and heterogeneous-content songs vs holistic thematic description). The correct framing is a third complementary retriever fused alongside dense and sparse, not a replacement.
Also noted: aggregating passage scores by counting matches introduces a length bias (longer songs accumulate more matches); max-pooling is the standard alternative. And the D27 rarest-lexeme filter may select a misremembered rare word as a key search term, directing sparse retrieval toward a term present in no correct document — a plausible failure mode under realistic queries.
Full reasoning and literature in `notes-chunking-and-error-tolerance.md`.
Status: active — further work

## D30 — Hybrid RRF fusion measured over top-50 candidate lists  (2026-08-31)
Decision: `backend/evaluate.py` and `backend/evaluate_sparse.py` were extended to also save each retriever's full top-50 (song_id, rank) candidate list per query to new files (`results/dense_top50.json`, `results/sparse_top50.json`), leaving the original top-20 baseline/per-query files untouched. Both were rerun over the identical query set (same file, same `random.seed(42)`) to produce these. `backend/evaluate_hybrid.py` fuses the two lists per query with Reciprocal Rank Fusion — score(song) = Σ 1/(k+rank) over retrievers where present, k=60 primary — ranks by fused score descending, and computes Recall@1/5/10, MRR, nDCG@10.
Result (k=60, fused over top-50): Recall@1=0.109, Recall@5=0.160, Recall@10=0.180, MRR=0.134, nDCG@10=0.142 — beats both dense (nDCG@10=0.135, D19) and sparse (nDCG@10=0.022, D27) on all five metrics. k-sensitivity (k∈{10,60,200}): nDCG@10 = 0.138 / 0.142 / 0.142 — fusion is materially better than k=10 but saturates by k=60 (k=200 ≈ k=60), so k=60 is a reasonable default, not a knife-edge choice. Against the parents: hybrid solves 191 queries neither dense nor sparse solved alone (top 10), but loses 387 queries dense alone had solved (fusion demotes them below rank 10) — a real, non-trivial cost of fusion, not a pure win. Saved to `results/hybrid_baseline.json`, `hybrid_per_query.json`, `hybrid_k_sensitivity.json`, `dense_sparse_hybrid_comparison.json`, `hybrid_vs_parents.json`.
Why: A prior attempt at this same task discovered the existing per-query files (`dense_per_query.json`/`sparse_per_query.json`, from D19/D27) only recorded the ground-truth song's own rank per query, not each retriever's full candidate identities — insufficient for genuine RRF, which needs to know every candidate that could out-rank the truth after fusion. Flagged to the user rather than approximating; user chose to re-run retrieval once more (rather than accept an unreliable heuristic), and specifically asked for top-50 (not top-20) so fusion has a deeper candidate pool, at the cost of a second sparse run (~3h, since sparse's per-query cost is dominated by candidate-set size after the D26 rarest-lexeme filter, not by final LIMIT). Numbers are explicitly labelled a lower bound relative to fusing deeper/full-corpus candidate sets, since a song ranked outside top-50 by both retrievers can never surface via this fusion regardless of how well it would have scored.
This result upgrades D17's hybrid-architecture case from diagnostic-plus-D27/D28-overlap-evidence to a directly measured net improvement — the first number in the pipeline that actually beats dense outright rather than just complementing it unevenly.
Status: active

## D31 — Retrieval logic extracted to a shared module  (2026-08-31)
Decision: Dense, sparse and RRF retrieval now live in `backend/retrieval.py`. `evaluate_hybrid.py` imports `rrf_fuse` from it instead of holding its own copy, and the API calls the same functions. Constants (`RRF_K=60`, `FUSION_DEPTH=50`, `PROBES=100`, `MAX_QUERY_LEXEMES=20`) are defined once there.
Why: The served system and the reported dissertation numbers must not diverge — if the API's fusion drifted from `evaluate_hybrid.py`, the evaluation chapter would no longer describe the thing that was built, which is exactly the kind of gap a viva probes. Verified by re-running `evaluate_hybrid.py` after the refactor: output is byte-identical to the D30 results (`diff` clean on both `hybrid_baseline.json` and `hybrid_k_sensitivity.json`).
Note: `rrf_score_map` also returns which retriever contributed each hit and at what rank, which the API exposes per result — that is what makes the dense/sparse/hybrid toggle in the UI legible rather than a black box.
Status: active

## D32 — spotify_id backfilled into the song table  (2026-08-31)
Decision: Added `song.spotify_id`, populated from `id_metadata.csv` via `backend/add_spotify_ids.py` (idempotent, resumable via `WHERE spotify_id IS NULL`).
Why: D6 recorded that Spotify track IDs were already available in `id_metadata.csv`, but `ingest.py` never loaded that file — the column simply did not exist, so the embed player and album art had nothing to resolve against. Caught when building the API's response payload.
Status: active

## D33 — Frontend architecture  (2026-08-31)
Decision: React + Vite + **Tailwind v4** + react-router-dom, JavaScript (no TypeScript, per stack decision). Structure: `api.js` (single fetch layer), `auth.jsx` (auth context), `useArtwork.js` (artwork hook), `components/` (Layout, SearchBar, SongRow, Artwork, Spotify, States), `pages/` (Home, Results, SongDetail, Genres, Login, PersonalisedHome).
Why (non-obvious choices):
- **Tailwind v4 `@theme`, not `tailwind.config.js`.** The installed Tailwind is v4, which is CSS-first; the specified palette is declared as `--color-*` custom properties in `index.css` and generates the same utility names (`bg-surface`, `text-muted`, `bg-accent`) a v3 `colors: {}` block would. Same design system, correct idiom for the installed version.
- **Accent discipline enforced structurally.** `#E80003` appears only on button fills, active toggle/pill/nav state, focus rings and play icons. Hover moves `surface -> surfaceHover`; no hover state adds red. Never used for body text.
- **Recent searches and auth state are in React state, not localStorage.** Nothing about what a user searched for or who they are is written to disk. This keeps the app clear of persisted personal data (relevant to D23/D25), and reload gives a clean slate.
- **Skeletons, not spinners**, and every fetch has an explicit loading / empty / error branch with retry. Empty states are mode-aware — a zero-result sparse search explains that lexical search needs literal lyric words and points at hybrid, rather than saying "no results" and stopping.
- **Explicit submit only.** Search never fires on keystroke: each query costs an SBERT encode plus a pgvector scan, and search-as-you-type would multiply that per character for no user benefit.
- **Auth built as a seam.** `auth.jsx` exposes the exact shape the real JWT client will (`login`/`signup`/`logout`/`tasteGenres`/`viewed`), currently backed by in-memory state with `TODO(D25)` markers at the two call sites that become HTTP requests. Signup already collects taste genres and the logged-in home already consumes them, so adding the real backend is wiring, not a redesign.
Status: active

## D34 — Spotify display compliance is structural, not cosmetic  (2026-08-31)
Decision: Album art is fetched server-side (`GET /artwork?ids=`) through a client-credentials app-only token, batched 50 track ids per Spotify call, cached in an in-memory TTL cache (24h) and never written to Postgres. Artwork is fetched only for results actually rendered — never a corpus backfill. In the UI: artwork renders with `object-contain` (resize permitted, cropping is not), carries no overlay/gradient/text/logo, always links to the track on Spotify, and the play affordance sits *beside* it. Any view showing Spotify-sourced content renders the Spotify attribution mark. Missing `spotify_id` or a failed fetch falls back to a deterministic colour block derived from the song id.
Why: Spotify's developer terms constrain presentation, so these are correctness constraints rather than styling preferences — encoding them in the `Artwork`/`Spotify` components makes them hard to violate accidentally later. Not caching artwork in Postgres keeps their content out of our persistent store, consistent with the D5 posture on third-party content. The colour-block fallback is deterministic (hash of song id) so a given song always looks the same, and no third-party placeholder service ever sees our song ids.
Open item: `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` are not yet in `.env`, so `/artwork` currently returns `{}` and the UI shows colour blocks throughout. The code path is built and degrades cleanly; adding credentials switches artwork on with no code change.
Status: active — pending Spotify credentials

## D35 — Spotify batch /tracks is refused; per-track fallback  (2026-09-01)
Decision: `backend/spotify.py` attempts the batch `GET /v1/tracks?ids=` endpoint (50 ids per call) and, the first time Spotify answers 403, latches a module-level flag and switches to concurrent single-track `GET /v1/tracks/{id}` fetches (8-worker thread pool) for the rest of the process's life. Credentials are now configured and artwork resolves — verified 8/8 for a real search result set in 0.94s.
Why: Spotify refuses the *batch* tracks endpoint for newly created apps while permitting the *single* track endpoint on the identical client-credentials token — confirmed directly: token exchange 200, `/v1/search` 200, `GET /v1/tracks/{id}` 200 for the same id that `GET /v1/tracks?ids=` rejected with 403. So the planned "batch up to 50 per call" is not available to this app and could not be implemented as specified. Latching rather than retrying avoids paying a guaranteed-403 round trip on every request; preferring batch first means the app upgrades itself automatically if extended access is ever granted, with no code change.
Cost of the fallback: N HTTP calls instead of N/50 for N rendered results. Mitigated by the existing 24h in-memory TTL cache (each song is fetched at most once a day), by fetching only for results actually rendered (never a corpus backfill — D34), and by the thread pool keeping wall-clock latency under a second for a full result page. This is acceptable because artwork is presentational: it is not on the retrieval path and its failure degrades to the deterministic colour block rather than breaking the page.
Note for the write-up: this is a genuine third-party platform constraint discovered at integration time, not a design preference — worth a sentence in the implementation chapter as an example of external API limits shaping architecture.
Status: active — supersedes the "pending Spotify credentials" open item in D34

## D36 — Sparse ranking bug: title/artist weight swamped by lyric term frequency  (2026-09-01)
Decision: Changed the `ts_rank_cd` call in the shared sparse retriever (`backend/retrieval.py`) to pass an explicit weight array `{D,C,B,A} = {0.02, 0.05, 0.05, 1.0}`, normalisation flag `1` (divide by `1 + log(document length)`), and a deterministic `song.id ASC` tiebreak. Query-time only — the stored tsvector is unchanged, so no re-indexing. `evaluate_sparse.py` now calls `retrieval.sparse_search` instead of holding its own copy of the query.
How it was found: manual UI testing after the frontend was built, not offline evaluation. Reported failures: `eminem killshot` returned "Brainless" above "KILLSHOT"; `The Cranberries Ridiculous Thoughts` did not return the exact matching record anywhere in the top 20; `The Cranberries Zombie` returned the target only at rank 8.
Diagnosis (measured, not assumed): the tsvector sets weight A for artist+title and B for lyrics (D26), but Postgres' default `ts_rank_cd` weights `{0.1, 0.2, 0.4, 1.0}` make an A hit worth only 2.5x a B hit. Decomposing the failing case: "Brainless" contains the lexeme `eminem` ten times — once in the artist field (A) and **nine times inside its own lyrics** (B) — while "KILLSHOT" contains `eminem` once (A) plus `killshot` twice (one A). Nine lyric repetitions therefore outscored an exact title match. A second effect compounds it: `killshot` has document frequency 2 in an 84,103-song corpus (maximally discriminative) yet is worth no more per occurrence than `eminem` at df 145, because `ts_rank_cd` has no IDF term at all.
Config chosen on evidence, in two stages, and both stages overturned an initial guess:
(1) A sweep of weight arrays x normalisation flags against the four failing queries showed `B<=0.05` fixes all four, but that **normalisation flag 2 (divide by raw document length) is actively harmful** — it over-penalises long lyric bodies and pushed KILLSHOT from rank 2 down to rank 12. Flag 2 had been the recommended option going in; it was rejected on measurement.
(2) A 300-query sample of the real evaluation set then separated the survivors: flag 1 (nDCG@10 0.0403) > flag 0 (0.0388) > flag 16 (0.0324), against the old configuration's 0.0166. Flag 16 was the initial pick after stage 1 and was dropped after stage 2.
Verified: all four reported queries now return the target at rank 1, and the `cranberries` control is unchanged. Before/after top-5 tables saved to `results/sparse_before_after.json`.
Why this matters methodologically (and is worth stating in the write-up): the offline evaluation never surfaced this bug, because every one of its 20,672 queries is a long free-text interpretation, while the failures occur on short known-item queries containing a title or artist name. **The evaluation's query distribution did not match the query distribution the deployed system actually receives.** Manual interaction with the built UI was what exposed it — an argument for building the interface rather than reporting metrics alone.
Notable: the fix was expected to trade short-query accuracy against the offline metric. It did not. On the 300-query sample nDCG@10 rose ~2.4x (0.0166 -> 0.0403), consistent with D28's finding that 58.6% of sparse-only wins already had the song title present in the query text — so raising the title/artist weight helps both query types, and there was no tradeoff to accept.
Status: active — full-corpus metrics pending, see the follow-up entry

## D37 — Near-duplicate records quantified  (2026-09-01)
Decision: Measured, not yet fixed. `backend/analyze_duplicates.py` groups the catalogue by normalised artist + title with version/edition qualifiers stripped ("Zombie", "Zombie (Acoustic Version)", "Zombie - Acoustic Version" collapse to one key). Result: 1,419 duplicate groups covering 2,972 songs (3.5% of the catalogue); group sizes 2 (x1300), 3 (x104), 4 (x15). **949 of the 20,672 evaluation songs (4.6%) sit in a duplicate group.** Saved to `results/duplicate_analysis.json`.
Why: if the ground-truth `song_id` is one record and retrieval returns its twin, the harness scores a miss, so duplicates depress the reported numbers for all three retrievers. This bounds that effect: correcting for it would raise the reported figures by at most a few percent, so it is a real caveat but not an explanation for the overall recall level. Worth one sentence in the evaluation chapter as a known measurement limitation rather than a pending fix.
Status: active — quantified, deliberately not fixed before the presentation

## D38 — Correction: the sparse arm is not BM25  (2026-09-01)
Decision: Wording correction to D17 ("Postgres full-text/BM25") and D26 ("a fairer stand-in for BM25"). The sparse retriever is Postgres `ts_rank_cd`, which is **not** BM25 and has no IDF component whatsoever — it scores weighted term frequency and cover density only. The dissertation and presentation should describe it as "Postgres full-text search (`ts_rank_cd`)", never as BM25.
Why: the claim is inaccurate and would not survive a viva question. D26's rarest-lexeme filter and D36's weight array together approximate *some* of what BM25 provides (term selectivity, field weighting, length normalisation), but approximating parts of BM25 is not implementing it. A genuine BM25 or BM25F implementation remains the principled fix and is a candidate for further work.
Status: active — corrects wording in D17 and D26, which stand unedited per the append-only rule

## D39 — D36 fix measured on the full corpus: sparse ~2x, hybrid +8%  (2026-09-01)
Decision: Re-ran the full evaluation with the D36 sparse ranking fix. Identical query set, `random.seed(42)`, one interpretation per song, 20,672 queries; the dense arm is untouched. Results written to `*_v2.json` so the D27/D30 figures survive for comparison.

| system | R@1 | R@5 | R@10 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| dense | 0.0991 | 0.1521 | 0.1760 | 0.1241 | 0.1349 |
| sparse-old | 0.0071 | 0.0263 | 0.0437 | 0.0176 | 0.0221 |
| sparse-new | 0.0180 | 0.0529 | 0.0751 | 0.0354 | 0.0431 |
| hybrid-old | 0.1091 | 0.1600 | 0.1802 | 0.1342 | 0.1420 |
| hybrid-new | 0.1149 | 0.1721 | 0.1988 | 0.1439 | 0.1534 |

Sparse improved by roughly 2x on every metric (nDCG@10 1.95x, Recall@1 2.55x). Hybrid improved ~8% (nDCG@10 0.1420 -> 0.1534) with no change to the dense arm or to the fusion itself — purely from better sparse input. Hybrid-new is the best configuration measured so far. Sparse-only top-10 wins more than doubled (435 -> 939, D27 overlap re-run), "both" rose 466 -> 613, and "neither" fell 16,598 -> 16,094. k-sensitivity is unchanged in shape: k=60 remains the best of {10, 60, 200} and still saturates by 60 (k=200 is within 0.0002).
Why this is worth stating plainly: the concern going in was that suppressing lyric weight would fix short known-item queries at the cost of the long interpretation queries the evaluation is built from. It did not — both improved, and the offline metric improved substantially. The mechanism is D28's: 58.6% of sparse-only wins already contained the song title in the query text, so weighting title/artist correctly helps the interpretation queries too. There was no tradeoff to report.
Method note: the ranking configuration was chosen from a 300-query sample (predicted nDCG@10 0.0403) before committing to the full run, which measured 0.0431. The sample was a reliable guide, which is what made it affordable to compare four configurations instead of guessing one and spending 3.5h per candidate.
Cost: the fix is query-time only, but it is not free — the full sparse run took 3h26m against ~3h before, because normalisation flag 1 requires document length and the explicit weight array adds per-row work over the ~6,000 candidate rows a typical query ranks. Interactive latency is still ~0.2s, so this matters only to the batch harness.
Status: active — supersedes the sparse and hybrid figures in D27 and D30, which stand unedited per the append-only rule

## D40 — Open: RRF consensus penalises single-retriever known-item hits  (2026-09-01)
Decision: Recorded, deliberately not acted on. With sparse fixed, hybrid is now *worse than sparse alone* on short known-item queries: `eminem killshot` returns KILLSHOT at sparse rank 1 but hybrid rank 6; `The Cranberries Zombie` returns the targets at sparse ranks 1-3 but hybrid ranks 8/10/12.
Cause: RRF rewards cross-retriever agreement. For `eminem killshot`, "'Till I Collapse" appears in both lists (dense 1, sparse 21) and scores 1/61 + 1/81 = 0.0287, beating KILLSHOT's sparse-only 1/61 = 0.0164. Dense cannot retrieve an exact title match it has no semantic signal for, so on known-item queries only one retriever *can* be right, and consensus-weighting actively buries the correct answer. This is the same mechanism as D30's "hybrid loses 352 queries dense had solved", observed in the opposite direction.
Why not fixed now: every plausible remedy — per-retriever weighting in the fusion, query-adaptive routing (short keyword-like query -> favour sparse; long descriptive query -> favour dense), or a score-based rather than rank-based fusion — changes the headline hybrid numbers and would require another full re-run to report honestly. Hybrid is the UI default, so this is user-visible and should be named in the presentation as a known limitation rather than discovered by an examiner.
Note the tension worth stating: hybrid is the best system on the offline metric (D39) while being the worst of the three on exactly the short known-item queries a demo audience is most likely to type. That is a query-distribution argument, not a contradiction — and it is the same lesson as D36.
Status: open — candidate for the 5-16 September window

## D41 — Real authentication: Postgres + bcrypt + JWT  (2026-09-01)
Decision: Replaced the in-memory auth seam (D33) with real authentication. `backend/auth.py` adds an `app_user` table (email unique, bcrypt `password_hash`, `taste_genres text[]`) and a `user_view` history table, both created idempotently at startup. Endpoints: `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `PUT /auth/taste`, `POST /history/{song_id}`, `GET /recommendations`. Sessions are JWT (HS256, 7-day expiry) sent as a Bearer token; the frontend keeps the token in `sessionStorage`, so it survives a reload but not closing the browser.
Why: enables the taste-driven home page. Per D25 the table holds fabricated test accounts only, so no real personal data exists and the ethics self-declaration (D23) is unaffected. Passwords are bcrypt-hashed (cost 12) and never logged; login returns an identical error whether the email is unknown or the password is wrong, so the endpoint does not disclose which accounts exist.
Note: `pydantic.EmailStr` was deliberately *not* used. It rejects reserved test domains (`.local`, `.test`) as undeliverable, which is precisely what fabricated accounts should use — so email is validated with a plain format check instead. Strict deliverability validation would have fought the design rather than supported it.
Recommendations are intentionally simple: a random sample of songs in the user's taste genres, excluding anything already viewed, plus recent history. Collaborative filtering and taste vectors remain further work (D3).
Outstanding for production (not for the dissertation demo): `JWT_SECRET` falls back to an insecure development default when unset, and the API logs a warning saying so. There is no rate limiting on login.
Status: active — supersedes the in-memory auth described in D33

## D42 — UI: ranks over scores, and making retrieval legible  (2026-09-01)
Decision: Result rows now lead with rank rather than raw fusion score. The top three carry gold/silver/bronze medals, and each row shows which retriever(s) found it and at what rank — `D#1` (blue) for dense, `S#21` (amber) for sparse, plus a `both` marker when the two agree. Genre tiles became 2x2 mosaics of real album art. The play control now opens our own song detail page with autoplay requested, instead of leaving for Spotify. Song detail was rebuilt as two columns: player and lyric snippet on the left, a sticky song card on the right.
Why: a fused RRF score of `0.0164` is meaningless to a user and communicates nothing about the system. Showing `D#1 + S#21 -> fused #1` makes the hybrid architecture visible on screen — the interface now demonstrates the retrieval contribution rather than merely consuming it, which is worth more in a demo than any amount of styling.
Spotify constraint retained: genre mosaics place the label *below* the artwork, never over it, because their terms forbid text or gradients drawn on their images (D34). Autoplay is passed as a parameter and honestly documented as a request rather than a guarantee — browsers block sound-on autoplay without a gesture in the destination document.
Rejected: displaying full lyrics on the song detail page. We hold all 109,269 lyric files locally, so this was technically trivial, but the UK research exception (s29A CDPA) covers computational analysis, not communication to the public, and ethics approval cannot grant a copyright licence. D5's snippet-only stance stands. The detail page is filled with tags/themes and the licensed Spotify player instead.
Status: active

## D43 — Renamed to NoLyric.find; profile, about, and UI refinement  (2026-09-02)
Decision: App renamed from Lyric.find to **NoLyric.find** — the point being that the user needs no lyrics, title or artist to find a song. Added a user profile page (avatar, taste-genre editor, listening history, log out) and an About page explaining the three retrieval modes, data provenance and evaluation method. Log out moved off the navbar into the profile page; the navbar now carries an avatar link to the profile instead.
Other refinements: rank medals redesigned (gold/silver/bronze with gradient, bevel, ribbon and glow, replacing flat circles); genre cards rebuilt as rounded mosaics with hover lift and chevron; a shared `SectionHeader` with accent rule and subtitle; and a password strength meter (four colour bars, contextual next-step hint) on signup.
Naming caveat worth being aware of: "NoLyric" can be misread as "this app has no lyrics". The system does use lyrics — it embeds them to build the index; it is the *user* who needs none. Flagged to the author, who kept the name.
Bug fixed along the way: genre tiles were showing the same album covers across different genres. The `/genre-art` query ordered by `song.id`, which is deterministic, and because one song belongs to several genres, neighbouring genres drew the same low-id rows. Now ordered by `md5(genre || song.id)`, so each genre draws its own pseudo-random sample — verified zero shared images across rock/pop/metal/jazz.
Note on the strength meter: it is advisory only. The 8-character minimum is enforced server-side in the pydantic model, because any client-side check can be bypassed.
Status: active

## D44 — Published SID figures are not comparable with ours: candidate pool is ~800, not 84,103  (2026-09-29)
Decision: Report our figures against their own random baseline, and state explicitly that they cannot be compared with Zhang et al.'s reported MRR.
Why: Zhang et al. (ISMIR 2022) report MRR 25.3-32.5% on the Song Interpretation Dataset, which looks far above our 14.4%. They also state a random ranking gives MRR "about 0.9%". Expected MRR of a uniform random ranking over n items is H_n/n, which equals 0.908% at n = 800, the size of their held-out test set. Their candidate pool is therefore the ~800-song test set, not the 27k corpus. Our pool is 84,103, where random MRR is 0.0142%. Relative to chance, ours is ~1,000x and theirs ~36x. This is our own derivation from their stated baseline (the pool size is not stated directly in their paper), and the arithmetic is shown in Chapter 4 so a reader can check it. Framed as "the numbers cannot be compared", not as a claim to outperform them, since the inputs and task differ.
Also verified during this pass: Zhang et al. do not discuss the single-relevant-document limitation of the protocol. Supporting literature added (all read at source): Buckley & Voorhees 2004 (measures not robust to incomplete judgements); Arabzadeh et al. 2022 (on a single-label benchmark, assessors preferred the system's unlabelled top result ~59% of the time).
Status: active
