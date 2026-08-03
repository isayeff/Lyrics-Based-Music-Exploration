# Lyrics-Based Music Exploration — Architecture & Plan (v1)

*Working reference document. Everything here is a proposal to confirm with Varvara — items she should sign off on are flagged in section 10.*

---

## 1. Research framing & positioning

**One-sentence thesis.** A free-text, description-based music retrieval and exploration system that matches natural-language descriptions of songs to a lyrics catalogue using dense sentence embeddings, with artist-level entity profiling, evaluated offline against user-written song interpretations.

**Where it sits in the literature (Chapter 2 spine).**
- Frame the whole project as **Lyrics Information Processing (LIP)** — the bridge between NLP and MIR (Watanabe & Goto, 2020). Your system is a *lyrics-centred application* (exploration + retrieval).
- Use the ISMIR three-phase arc (Knees, Schedl & Goto, 2020) for historical context: content-based (audio) -> semantic/community-metadata description -> interaction-based recommenders. Your work modernises the *semantic description* phase.

**Closest prior systems — position against these (do not reinvent them):**
- **LyricsRadar** (Sasaki et al., 2014) — lyrics retrieval via LDA topic visualisation.
- **Lyric Jumper** (Tsukuda et al., 2017) — lyrics exploration modelling an *artist's lyric-topic profile*. Nearest prior art to your artist-profiling idea.
- **Query-by-Blending** (Watanabe & Goto, 2019) — flexible queries over a unified latent space of lyrics + audio + artist tags. Nearest to your free-text search.
- **Your two predecessor Sheffield projects** — TF-IDF / Word2Vec / LDA content-based filtering, and embedding-similarity genre classification.

**The gap = your novelty.** All of the above rely on topic models (LDA), self-organising maps, or word-level latent spaces; the LIP survey notes unsupervised topic quality is hard to evaluate. None support **free-text natural-language description queries** matched via **modern sentence embeddings**. Contribution, three parts:
1. **Free-text description -> song retrieval** with Sentence-BERT (vs. TF-IDF / LDA / Word2Vec).
2. **Artist profiling via NER** — extends Lyric Jumper's topic-profile concept to named entities and themes.
3. **Rigorous offline evaluation** using the Song Interpretation Dataset (interpretation -> known song), sidestepping the topic-evaluation problem.

---

## 2. Scope decision

| Tier | Features | Rationale |
|---|---|---|
| **Core (must build)** | Free-text semantic search over lyrics catalogue; artist-NER profiling; offline evaluation vs. classic baselines; minimal React UI (search -> ranked results -> song detail page) | This *is* the dissertation. |
| **Nice-to-have** | UMAP/Plotly 2D exploration map; offline LLM lyric summarisation as an embedding signal; genre-descriptor matching | Adds value + lit-review tie-ins, none load-bearing. |
| **Further work (write, don't build)** | RL taste model; collaborative filtering; hybrid recommendation; like/dislike loop | Need many users + interaction logs; heavy participant ethics. "Further work" is a marked section. |

**Principle:** ship a small, clean, *fully evaluated* core before touching tier 2.

---

## 3. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ (backend), JavaScript (frontend) | — |
| Backend | **FastAPI** + venv | — |
| Database | **PostgreSQL + pgvector** (via Docker) | Metadata + embeddings + vector search in one store |
| Embeddings | **Sentence-BERT** (`all-MiniLM-L6-v2`, compare `all-mpnet-base-v2`) | Core novelty |
| Baseline | **TF-IDF** (scikit-learn) | Turns predecessors' method into your baseline |
| NER | **spaCy** `en_core_web_trf` | Artist-profiling feature |
| Frontend | **React + TailwindCSS + Vite (JavaScript)** | — |
| Player | **Spotify embed (oEmbed)** + Web API client-credentials | App-only token, no personal data |
| Dim. reduction (viz) | UMAP + Plotly | Nice-to-have |
| Summarisation | local HF model / Gemini free tier, **offline only** | Nice-to-have |
| Notebooks | Jupyter | Exploration + evaluation lab bench |
| Writing | LaTeX (School template) + BibTeX on Overleaf | Set up now |
| References | Zotero / JabRef / Mendeley | Over-collect early |

---

## 4. System architecture

### 4a. Offline pipeline (build the index)
1. **Ingest** music4all CSVs -> Postgres catalogue tables: `song(song_id, title, artist, genres, tags, lang)`.
2. **Filter** to a workable subset (e.g. `lang = 'en'`).
3. **Lyrics** — *verify whether the shared zip contains lyrics.* If not, fetch per song from **Genius / lyrics.ovh** (artist + title). Cache raw lyrics locally (git-ignored); **store embeddings + short snippets only**.
4. **Song document** = lyrics (+ optional summary + tags + genres) -> embed with SBERT -> write vectors to a **pgvector** column (with an index for similarity search).
5. **Artist profiling** — NER over lyrics -> per-song entities/themes -> aggregate -> `artist_profile` table.
6. *(Optional)* LLM summarisation -> `description`; genre-descriptor text -> embeddings.
7. *(Optional)* UMAP projection -> 2D coords for the exploration view.
8. **Spotify mapping** — resolve `song -> track_id` (app-only token) for the embed player.

### 4b. Online (FastAPI)
- `POST /search {query}` -> embed query -> pgvector nearest-neighbour search -> join metadata -> ranked results.
- `GET /song/{id}` -> metadata + artist profile + Spotify track_id + lyric snippet.
- `GET /explore` -> 2D coords + clusters (nice-to-have).
- Facet filters over metadata (genre / artist / language).

### 4c. Frontend (React)
- Free-text search bar -> ranked results list -> song detail page (metadata, genres, artist profile, Spotify embed, lyric snippet). Optional exploration map.

---

## 5. Datasets

| Role | Dataset | Notes |
|---|---|---|
| Catalogue + metadata + tags + genres + listening history | **music4all** (shared) | Confirm lyrics presence |
| Full lyrics | **Genius / lyrics.ovh** (API, on demand) | Cache locally; features/snippets only |
| Free-text descriptions (novelty + evaluation) | **Song Interpretation Dataset** | Interpretation -> known song = ground truth |
| Player + track mapping | **Spotify Web API** (client-credentials) | App-only, no user login |
| Tag enrichment (optional) | **Last.fm** | — |
| *Not using* | MSD (bag-of-words), Word2Vec as primary | Word2Vec -> baseline only |

**Note:** SID and music4all overlap only partially — intersect by artist + title. Check the intersection size early; it caps your evaluation set.

---

## 6. Evaluation plan (the experimental core)

- **Task:** held-out interpretations as queries; ground truth = the song each describes.
- **Primary metrics:** Recall@{1,5,10}, MRR, nDCG.
- **Comparison (your experiment):** TF-IDF baseline vs. SBERT (and SBERT variants).
- **Ablation (optional):** effect of adding LLM summaries / tags / genres to the embedded document.
- **Secondary:** BERTScore (query vs retrieved lyrics); F1 for NER / any genre classifier.
- **No human participants** -> offline, reproducible, self-declaration ethics route.

---

## 7. Ethics summary

- Primary evaluation is **offline** on secondary datasets -> not the participant-study path.
- SID is scraped user content -> run the questionnaire; likely **self-declaration**.
- **Build fully, flag, apply once** — software and offline secondary-data processing need no prior approval; only a live user study (out of scope) must wait.
- Do the three mandatory training courses in parallel.
- Chapter 3 carries an explicit legal + ethical statement (incl. lyric-copyright handling). Final dissertation appends application, supporting docs, and approval letter.

---

## 8. Key references (anchor set)

- Watanabe, K. & Goto, M. (2020). *Lyrics Information Processing: Analysis, Generation, and Applications.* NLP4MuSA.
- Knees, P., Schedl, M. & Goto, M. (2020). *Intelligent User Interfaces for Music Discovery.* TISMIR 3(1).
- Tsukuda, K., Ishida, K. & Goto, M. (2017). *Lyric Jumper.* ISMIR.
- Sasaki, S. et al. (2014). *LyricsRadar.* ISMIR.
- Watanabe, K. & Goto, M. (2019). *Query-by-Blending.* ISMIR.
- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT.* EMNLP.
- Plus: Tsaptsinos (2017) lyrics genre classification; Fell et al. (2019) lyrics summarisation. Prefer published venues over arXiv where both exist.

---

## 9. Open questions to confirm with Varvara

1. **Ethics route** — self-declaration vs. full, given music4all + SID.
2. **Project type** — Experimental (expected for advanced MSc) vs. Design & Build.
3. **Scope sign-off** — core (free-text retrieval + artist NER + offline evaluation) acceptable, rest as further work?
4. **Lyrics source** — does shared music4all include lyrics? If not, is Genius/lyrics.ovh enrichment + snippet-only storage acceptable?
5. **LLM use** — is offline summarisation acceptable under the programme's AI policy (enrichment, not writing)?
