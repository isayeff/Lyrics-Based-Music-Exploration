# CLAUDE.md

Context and working rules for this repository. Read every session.

---

## PART A — Project-specific (this dissertation)

### What this is
MSc dissertation: a **free-text, description-based music exploration system**. A user describes a song in natural language; the system retrieves relevant matches using dense sentence embeddings, plus artist-level profiling via NER. This is a **marked academic project** — every methodological choice must be explainable and defensible in a viva. Prefer explaining *why* over cleverness.

Full plan lives in `Architecture-and-Plan_v1.md` (the north star). Decisions are logged in `DECISIONS.md`.

### ETHICS — flag, don't block
- **Build freely.** Writing code and processing the secondary datasets (music4all, Song Interpretation Dataset) offline is software development, not participant research, and needs no approval to proceed. Do not block or stall build tasks on ethics grounds.
- **Flag, don't block.** When a task will need ethics cover, note it (and add it to the flagged list in `DECISIONS.md`) so we can cover it in one application — but keep building.
- **The one real gate:** a *live user study* (recruiting real people, logging their behaviour for the dissertation) must not run until approval is in place. It is not in core scope.
- **Offline evaluation** on the Song Interpretation Dataset: build and run it in development freely; just have the self-declaration confirmed before treating the results as final dissertation numbers (already in progress, runs in parallel).

### COPYRIGHT — how we handle lyrics
Fetching/processing lyrics for non-commercial research is fine (UK research text-and-data-mining exception); redistributing full lyrics is not.
- Fetch lyrics (Genius/lyrics.ovh) -> compute embeddings / NER features. OK.
- Cache raw lyrics **locally, git-ignored**. **Never commit full lyric text.**
- Persist only **derived representations** (embeddings, extracted entities) + **short snippets** (a couple of lines) for the UI, with a link out to the licensed source.
- No feature whose purpose is displaying complete lyrics.

### Secrets & data
- Never commit API keys — use `.env` (git-ignored).
- Never commit large dataset files — datasets live in a git-ignored `data/` dir or outside the repo.

### Stack (don't guess — use these)
- Backend: **Python 3.11+**, **FastAPI**, venv.
- Database: **PostgreSQL + pgvector** — metadata *and* vector similarity search in one store (run via Docker). (FAISS only if we later add an exact-vs-approximate retrieval comparison.)
- Embeddings: **sentence-transformers** (SBERT); baseline **TF-IDF** via scikit-learn.
- NER: **spaCy** (`en_core_web_trf`).
- Frontend: **React + TailwindCSS + Vite**, **JavaScript** (not TypeScript).
- Player: **Spotify embed (oEmbed iframe)** + Web API client-credentials (app-only token, no user login).
- Notebooks: **Jupyter** for data exploration and evaluation runs (lab bench, not part of the app).

### Reproducibility (this is an experiment)
- Set and record random seeds anywhere sampling/splitting happens.
- Pin dependencies (`requirements.txt`). State exact model names (e.g. `all-MiniLM-L6-v2`).
- DB setup reproducible: commit `docker-compose.yml` + schema/migration so the database is one command to stand up.
- Evaluation must be re-runnable end-to-end from a script, not hand-steps.

### Decision-log habit
On any non-trivial choice (a model, a data approach, a metric, a tradeoff), append a short entry to `DECISIONS.md`. Capture the **why**. This feeds Chapters 3-4.

---

## PART B — General coding guardrails (reusable across projects)

*Bias toward caution over speed. For trivial tasks, use judgment.*

### 1. Think before coding
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name it, ask.

### 2. Simplicity first
- Minimum code that solves the problem. Nothing speculative.
- No abstractions for single-use code. No error handling for impossible scenarios.
- If 200 lines could be 50, rewrite it. "Would a senior engineer call this overcomplicated?" If yes, simplify.

### 3. Surgical changes
- Touch only what you must. Don't refactor what isn't broken. Match existing style.
- Remove imports/variables/functions that *your* changes made unused.
- Every changed line should trace to the request.

### 4. Goal-driven execution — two modes
**Software mode** (APIs, UI, data plumbing): turn tasks into verifiable goals.
- "Add validation" -> write tests for invalid inputs, make them pass.
- "Fix the bug" -> write a test that reproduces it, then fix.
- Multi-step: state a brief plan, each step with a `verify:` check.

**Data/ML mode** (embeddings, retrieval, NER, evaluation): you can't unit-test "is it good." Verify by:
- Running on a small sample and inspecting outputs directly (eyeball top-k results, NER spans).
- Sanity-checking shapes, counts, distributions (no silent empty joins, no all-zero vectors).
- Reporting the metric (Recall@k / MRR / nDCG / F1) rather than asserting success.
- Comparing against the baseline, not just checking the new thing runs.

---

**Working if:** fewer unnecessary diffs, fewer over-built rewrites, questions come *before* implementation, Part A constraints are respected, and `DECISIONS.md` grows as the code does.
