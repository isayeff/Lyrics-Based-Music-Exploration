import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import { TileSkeleton, ErrorState } from '../components/States'
import { getGenres } from '../api'
import { useAuth } from '../auth'
import PersonalisedHome from './PersonalisedHome'

const EXAMPLES = [
  'a song about heartbreak and losing someone you love',
  'driving at night with the windows down',
  'someone questioning their purpose in life',
  'a defiant anthem about proving people wrong',
  'quiet song about missing home',
]

export default function Home({ recent, onSearch }) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [genres, setGenres] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setGenres(null)
    setError(null)
    getGenres(12)
      .then((data) => { if (!cancelled) setGenres(data.genres) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [reloadKey])

  function runSearch(query) {
    onSearch(query)
    navigate(`/results?q=${encodeURIComponent(query)}`)
  }

  return (
    <div className="space-y-10">
      <section className="pt-8 sm:pt-14 text-center space-y-5">
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">
          Describe a song. Find it.
        </h1>
        <p className="text-muted text-sm max-w-xl mx-auto">
          Search 84,000 songs by not just by title or artist also <b>search what they’re about.</b>
        </p>
        <div className="max-w-2xl mx-auto pt-1">
          <SearchBar recent={recent} onSubmit={runSearch} autoFocus size="lg" />
        </div>

        <div className="flex flex-wrap gap-2 justify-center pt-1">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => runSearch(ex)}
              className="px-3 py-1.5 rounded-full border border-border bg-surface text-muted text-xs
                hover:bg-surfaceHover hover:text-text transition"
            >
              {ex}
            </button>
          ))}
        </div>
      </section>

      {user && <PersonalisedHome onSearch={runSearch} />}

      <section className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-medium">Browse by genre</h2>
          <Link to="/genres" className="text-xs text-muted hover:text-text transition">See all</Link>
        </div>

        {error ? (
          <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
        ) : genres === null ? (
          <TileSkeleton count={12} />
        ) : genres.length === 0 ? (
          <p className="text-muted text-sm">No genres available.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {genres.map((g) => (
              <Link
                key={g.genre}
                to={`/genres/${encodeURIComponent(g.genre)}`}
                className="rounded-lg border border-border bg-surface hover:bg-surfaceHover transition p-3.5"
              >
                <p className="text-sm font-medium capitalize truncate">{g.genre}</p>
                <p className="text-xs text-muted mt-0.5">{g.count.toLocaleString()} songs</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
