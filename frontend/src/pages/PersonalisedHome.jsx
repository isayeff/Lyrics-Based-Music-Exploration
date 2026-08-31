import { useEffect, useState } from 'react'
import SongRow from '../components/SongRow'
import { SongListSkeleton, EmptyState, ErrorState } from '../components/States'
import { SpotifyLogo } from '../components/Spotify'
import useArtwork from '../useArtwork'
import { getGenreSongs } from '../api'
import { useAuth } from '../auth'

/* Logged-in home: recommendations from the taste genres picked at signup, plus
   recently viewed songs (D25). Recommendations are currently a genre sample;
   once auth is server-side this is where a taste-vector query would go. */
export default function PersonalisedHome({ onSearch }) {
  const { user, viewed } = useAuth()
  const tasteGenres = user?.tasteGenres || []
  const tasteKey = tasteGenres.join(',')

  const [recs, setRecs] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const taste = tasteKey ? tasteKey.split(',') : []
    if (taste.length === 0) {
      setRecs([])
      return
    }
    let cancelled = false
    setRecs(null)
    setError(null)

    Promise.all(taste.slice(0, 3).map((g) => getGenreSongs(g, 4)))
      .then((responses) => {
        if (cancelled) return
        const seen = new Set()
        const merged = []
        for (const res of responses) {
          for (const song of res.songs) {
            if (!seen.has(song.song_id)) {
              seen.add(song.song_id)
              merged.push(song)
            }
          }
        }
        setRecs(merged.slice(0, 8))
      })
      .catch((err) => { if (!cancelled) setError(err.message) })

    return () => { cancelled = true }
  }, [tasteKey, reloadKey])

  const recsArt = useArtwork(recs || [])
  const viewedArt = useArtwork(viewed.slice(0, 5))

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-sm font-medium">
          For you
          {tasteGenres.length > 0 && (
            <span className="text-muted font-normal"> · based on {tasteGenres.slice(0, 3).join(', ')}</span>
          )}
        </h2>

        {error ? (
          <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
        ) : tasteGenres.length === 0 ? (
          <EmptyState
            title="No taste profile yet"
            hint="Pick genres when you sign up to get recommendations here, or just search for something."
            action={
              <button
                type="button"
                onClick={() => onSearch?.('a song about starting over')}
                className="px-4 py-2 rounded-md bg-accent hover:bg-accentHover text-white text-sm font-medium transition"
              >
                Try a search
              </button>
            }
          />
        ) : recs === null ? (
          <SongListSkeleton rows={5} />
        ) : recs.length === 0 ? (
          <EmptyState title="Nothing to recommend" hint="No songs found for your picked genres." />
        ) : (
          <>
            <div className="rounded-lg border border-border overflow-hidden bg-surface">
              {recs.map((song) => (
                <SongRow key={song.song_id} song={song} art={recsArt[song.song_id]} showScore={false} />
              ))}
            </div>
            <SpotifyLogo />
          </>
        )}
      </section>

      {viewed.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium">Recently viewed</h2>
          <div className="rounded-lg border border-border overflow-hidden bg-surface">
            {viewed.slice(0, 5).map((song) => (
              <SongRow key={song.song_id} song={song} art={viewedArt[song.song_id]} showScore={false} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
