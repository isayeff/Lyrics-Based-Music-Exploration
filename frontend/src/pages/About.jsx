import { Link } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader'

const RETRIEVERS = [
  {
    name: 'Dense',
    tag: 'D',
    tone: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
    headline: 'Matches on meaning',
    body: 'Every song\'s lyrics are turned into a 384-dimension vector with a Sentence-BERT model (all-MiniLM-L6-v2). Your description becomes a vector too, and the system finds the songs whose vectors point in the most similar direction. It can match a song that shares no words at all with your query.',
  },
  {
    name: 'Sparse',
    tag: 'S',
    tone: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    headline: 'Matches on literal words',
    body: 'Postgres full-text search over artist, title and lyrics. Strong when you remember an exact phrase, a title or an artist name; useless when you only remember what a song felt like.',
  },
  {
    name: 'Hybrid',
    tag: 'H',
    tone: 'border-accent/40 bg-accent/10 text-accent',
    headline: 'Both, fused',
    body: 'Runs both retrievers and merges their rankings with Reciprocal Rank Fusion. A song ranked well by both rises to the top. This is the default, and it scores highest in offline evaluation.',
  },
]

export default function About() {
  return (
    <div className="space-y-10 max-w-3xl">
      <section className="space-y-3 pt-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Find a song by describing it
        </h1>
        <p className="text-muted text-sm leading-relaxed">
          Most music search assumes you already know what you are looking for — a title, an
          artist, a lyric you can quote. This system is built for the opposite case: you
          remember what a song was <em>about</em>, and nothing else. Describe it in your own
          words and it searches 84,103 songs by meaning rather than by keyword.
        </p>
      </section>

      <section className="space-y-4">
        <SectionHeader title="How the search works" subtitle="Three retrieval modes, switchable on any results page." />
        <div className="grid gap-3 sm:grid-cols-3">
          {RETRIEVERS.map((r) => (
            <div key={r.name} className="rounded-xl border border-border bg-surface p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className={`px-1.5 py-0.5 rounded border text-[10px] font-semibold ${r.tone}`}>
                  {r.tag}
                </span>
                <span className="text-sm font-semibold">{r.name}</span>
              </div>
              <p className="text-xs text-text/80 font-medium">{r.headline}</p>
              <p className="text-xs text-muted leading-relaxed">{r.body}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted">
          On a results page each row shows which retriever found the song and at what position —
          so <span className="text-sky-300">D#1</span> plus{' '}
          <span className="text-amber-300">S#21</span> means dense ranked it first, sparse ranked
          it twenty-first, and fusion decided the final order.
        </p>
      </section>

      <section className="space-y-4">
        <SectionHeader title="Where the data comes from" />
        <dl className="grid gap-3 sm:grid-cols-2 text-sm">
          <div className="rounded-xl border border-border bg-surface p-4">
            <dt className="font-medium">Catalogue</dt>
            <dd className="text-xs text-muted mt-1 leading-relaxed">
              84,103 English-language songs from the music4all research dataset, with artist,
              title, album, genres and tags.
            </dd>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <dt className="font-medium">Lyrics</dt>
            <dd className="text-xs text-muted mt-1 leading-relaxed">
              Used to build the search index only. Full lyrics are never stored in the database
              or displayed — you see a short opening snippet and a link to the licensed source.
            </dd>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <dt className="font-medium">Playback &amp; artwork</dt>
            <dd className="text-xs text-muted mt-1 leading-relaxed">
              Album art and the 30-second player come from Spotify, shown unmodified and always
              linking back to the track.
            </dd>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <dt className="font-medium">Accounts</dt>
            <dd className="text-xs text-muted mt-1 leading-relaxed">
              Test accounts only. No real personal data is collected. Passwords are stored as
              bcrypt hashes, never in readable form.
            </dd>
          </div>
        </dl>
      </section>

      <section className="space-y-4">
        <SectionHeader title="How it was evaluated" />
        <p className="text-muted text-sm leading-relaxed">
          20,672 real fan-written song interpretations were used as search queries, with the song
          each one describes as the correct answer. Retrieval is scored on how often the right
          song appears near the top — Recall@1, Recall@10, MRR and nDCG@10. Hybrid retrieval
          currently scores highest, ahead of dense alone and well ahead of keyword search.
        </p>
        <p className="text-xs text-muted">
          MSc dissertation project, University of Sheffield.
        </p>
      </section>

      <section>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent hover:bg-accentHover
            text-white text-sm font-medium transition"
        >
          Try a search
        </Link>
      </section>
    </div>
  )
}
