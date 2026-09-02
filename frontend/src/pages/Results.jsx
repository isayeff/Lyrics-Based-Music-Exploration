import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import SongRow from '../components/SongRow'
import { SongListSkeleton, EmptyState, ErrorState } from '../components/States'
import { SpotifyLogo } from '../components/Spotify'
import useArtwork from '../useArtwork'
import { search } from '../api'

const MODES = ['dense', 'sparse', 'hybrid']

const MODE_HINT = {
  dense: 'Semantic similarity (SBERT embeddings).',
  sparse: 'Lexical keyword matching (Postgres full-text).',
  hybrid: 'Both, fused with Reciprocal Rank Fusion (k=60).',
}

export default function Results({ recent, onSearch }) {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const query = params.get('q') || ''
  const mode = MODES.includes(params.get('mode')) ? params.get('mode') : 'hybrid'

  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [genreFilter, setGenreFilter] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!query) return
    let cancelled = false
    setData(null)
    setError(null)
    setGenreFilter(null)
    search({ query, mode, limit: 20 })
      .then((res) => { if (!cancelled) setData(res) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [query, mode, reloadKey])

  const results = useMemo(() => data?.results || [], [data])

  const genreOptions = useMemo(() => {
    const counts = new Map()
    for (const song of results) {
      for (const g of song.genres || []) counts.set(g, (counts.get(g) || 0) + 1)
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8)
  }, [results])

  const visible = genreFilter
    ? results.filter((s) => (s.genres || []).includes(genreFilter))
    : results

  const art = useArtwork(visible)

  function runSearch(q) {
    onSearch(q)
    navigate(`/results?q=${encodeURIComponent(q)}&mode=${mode}`)
  }

  function setMode(next) {
    setParams({ q: query, mode: next })
  }

  return (
    <div className="space-y-5">
      <SearchBar initialValue={query} recent={recent} onSubmit={runSearch} />

      {!query ? (
        <EmptyState title="No query yet" hint="Describe a song above to search." />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <p className="text-sm text-muted min-w-0">
              Results for <span className="text-text">“{query}”</span>
            </p>

            <div
              role="tablist"
              aria-label="Retrieval mode"
              className="flex rounded-md border border-border bg-surface p-0.5"
            >
              {MODES.map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  title={MODE_HINT[m]}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1.5 rounded text-xs font-medium capitalize transition ${
                    mode === m ? 'bg-accent text-white' : 'text-muted hover:text-text hover:bg-surfaceHover'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted -mt-2">
            <span>{MODE_HINT[mode]}</span>
            {mode === 'hybrid' && data && (
              <span className="flex items-center gap-1.5">
                <span className="px-1.5 py-0.5 rounded border border-sky-500/40 bg-sky-500/10 text-sky-300 text-[10px] font-medium">D#</span>
                <span>dense rank</span>
                <span className="px-1.5 py-0.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300 text-[10px] font-medium">S#</span>
                <span>sparse rank</span>
              </span>
            )}
          </div>

          {genreOptions.length > 0 && !error && data && (
            <div className="flex flex-wrap gap-2">
              <FilterPill active={!genreFilter} onClick={() => setGenreFilter(null)}>
                All ({results.length})
              </FilterPill>
              {genreOptions.map(([genre, count]) => (
                <FilterPill
                  key={genre}
                  active={genreFilter === genre}
                  onClick={() => setGenreFilter(genreFilter === genre ? null : genre)}
                >
                  {genre} ({count})
                </FilterPill>
              ))}
            </div>
          )}

          {error ? (
            <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
          ) : data === null ? (
            <SongListSkeleton rows={8} />
          ) : results.length === 0 ? (
            <EmptyState
              title="No matches"
              hint={
                mode === 'sparse'
                  ? 'Lexical search needs words that literally appear in the lyrics. Try hybrid mode.'
                  : 'Try describing the song differently, or use fewer specific details.'
              }
            />
          ) : visible.length === 0 ? (
            <EmptyState
              title={`No ${genreFilter} results`}
              hint="No songs in this result set match that genre filter."
              action={
                <button
                  type="button"
                  onClick={() => setGenreFilter(null)}
                  className="px-4 py-2 rounded-md bg-accent hover:bg-accentHover text-white text-sm font-medium transition"
                >
                  Clear filter
                </button>
              }
            />
          ) : (
            <>
              <div className="rounded-lg border border-border overflow-hidden bg-surface">
                {visible.map((song) => (
                  <SongRow key={song.song_id} song={song} art={art[song.song_id]} />
                ))}
              </div>
              <SpotifyLogo />
            </>
          )}
        </>
      )}
    </div>
  )
}

function FilterPill({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-xs border transition capitalize ${
        active
          ? 'bg-accent border-accent text-white font-medium'
          : 'bg-surface border-border text-muted hover:bg-surfaceHover hover:text-text'
      }`}
    >
      {children}
    </button>
  )
}
