import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import SongRow from '../components/SongRow'
import SectionHeader from '../components/SectionHeader'
import { SongListSkeleton, EmptyState, ErrorState } from '../components/States'
import { SpotifyLogo } from '../components/Spotify'
import useArtwork from '../useArtwork'
import { getRecommendations, getGenres } from '../api'
import { useAuth } from '../auth'

export default function Profile() {
  const { user, token, ready, logout, setTasteGenres } = useAuth()

  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [allGenres, setAllGenres] = useState([])
  const [saving, setSaving] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    setData(null)
    setError(null)
    getRecommendations(token, 20)
      .then((res) => { if (!cancelled) setData(res) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [token, reloadKey])

  useEffect(() => {
    let cancelled = false
    getGenres(18)
      .then((res) => { if (!cancelled) setAllGenres(res.genres) })
      .catch(() => { if (!cancelled) setAllGenres([]) })
    return () => { cancelled = true }
  }, [])

  const viewed = data?.recently_viewed || []
  const viewedArt = useArtwork(viewed)
  const taste = user?.taste_genres || []

  if (ready && !user) return <Navigate to="/login" replace />
  if (!user) return <SongListSkeleton rows={4} />

  async function toggleGenre(genre) {
    const next = taste.includes(genre) ? taste.filter((g) => g !== genre) : [...taste, genre]
    setSaving(true)
    try {
      await setTasteGenres(next)
      setReloadKey((k) => k + 1)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-border bg-surface p-5">
        <div className="flex items-center gap-4">
          <span className="grid place-items-center w-14 h-14 rounded-full bg-accent/15 border border-accent/30
            text-xl font-semibold uppercase text-accent shrink-0">
            {user.email.slice(0, 1)}
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold tracking-tight truncate">{user.email}</h1>
            <p className="text-xs text-muted mt-0.5">
              {taste.length} genre{taste.length === 1 ? '' : 's'} in your taste profile
              {' · '}{viewed.length} song{viewed.length === 1 ? '' : 's'} viewed
            </p>
          </div>

          <button
            type="button"
            onClick={logout}
            className="shrink-0 flex items-center gap-2 px-4 py-2 rounded-lg border border-border
              bg-bg text-sm font-medium text-muted transition
              hover:border-accent/50 hover:text-accent hover:bg-accent/5"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor"
                 strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <path d="M16 17l5-5-5-5" />
              <path d="M21 12H9" />
            </svg>
            Log out
          </button>
        </div>
      </section>

      <section className="space-y-3">
        <SectionHeader
          title="Your taste"
          subtitle="Recommendations on your home page come from these genres."
        />
        <div className="flex flex-wrap gap-2">
          {allGenres.map((g) => {
            const active = taste.includes(g.genre)
            return (
              <button
                key={g.genre}
                type="button"
                disabled={saving}
                onClick={() => toggleGenre(g.genre)}
                className={`px-3 py-1.5 rounded-full text-xs border transition capitalize disabled:opacity-50 ${
                  active
                    ? 'bg-accent border-accent text-white font-medium'
                    : 'bg-surface border-border text-muted hover:bg-surfaceHover hover:text-text'
                }`}
              >
                {g.genre}
              </button>
            )
          })}
        </div>
      </section>

      <section className="space-y-3">
        <SectionHeader title="Listening history" subtitle="Songs you have opened, most recent first." />

        {error ? (
          <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
        ) : data === null ? (
          <SongListSkeleton rows={5} />
        ) : viewed.length === 0 ? (
          <EmptyState
            title="No history yet"
            hint="Open a song and it will appear here."
          />
        ) : (
          <>
            <div className="rounded-xl border border-border overflow-hidden bg-surface">
              {viewed.map((song) => (
                <SongRow key={song.song_id} song={song} art={viewedArt[song.song_id]} showRank={false} />
              ))}
            </div>
            <SpotifyLogo />
          </>
        )}
      </section>
    </div>
  )
}
