import { useEffect, useState } from 'react'
import SongRow from '../components/SongRow'
import { SongListSkeleton, EmptyState, ErrorState } from '../components/States'
import { SpotifyLogo } from '../components/Spotify'
import useArtwork from '../useArtwork'
import { getRecommendations } from '../api'
import { useAuth } from '../auth'

// Logged-in home: songs from the user's taste genres, plus recently viewed.
export default function PersonalisedHome({ onSearch }) {
  const { user, token } = useAuth()

  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    setData(null)
    setError(null)
    getRecommendations(token, 8)
      .then((res) => { if (!cancelled) setData(res) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [token, reloadKey])

  const recs = data?.recommendations || []
  const viewed = data?.recently_viewed || []
  const tasteGenres = data?.taste_genres || user?.taste_genres || []

  const recsArt = useArtwork(recs)
  const viewedArt = useArtwork(viewed.slice(0, 5))

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-sm font-medium">
          For you
          {tasteGenres.length > 0 && (
            <span className="text-muted font-normal">
              {' '}· based on {tasteGenres.slice(0, 3).join(', ')}
            </span>
          )}
        </h2>

        {error ? (
          <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
        ) : data === null ? (
          <SongListSkeleton rows={5} />
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
        ) : recs.length === 0 ? (
          <EmptyState title="Nothing to recommend" hint="No unseen songs found for your picked genres." />
        ) : (
          <>
            <div className="rounded-lg border border-border overflow-hidden bg-surface">
              {recs.map((song) => (
                <SongRow key={song.song_id} song={song} art={recsArt[song.song_id]} showRank={false} />
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
              <SongRow key={song.song_id} song={song} art={viewedArt[song.song_id]} showRank={false} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
