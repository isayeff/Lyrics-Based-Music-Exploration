import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import SongRow from '../components/SongRow'
import { TileSkeleton, SongListSkeleton, EmptyState, ErrorState } from '../components/States'
import { SpotifyLogo } from '../components/Spotify'
import useArtwork from '../useArtwork'
import { getGenres, getGenreSongs } from '../api'

export function GenreList() {
  const [genres, setGenres] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setGenres(null)
    setError(null)
    getGenres(60)
      .then((data) => { if (!cancelled) setGenres(data.genres) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [reloadKey])

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Browse genres</h1>

      {error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
      ) : genres === null ? (
        <TileSkeleton count={16} />
      ) : genres.length === 0 ? (
        <EmptyState title="No genres" hint="The catalogue has no genre data loaded." />
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
    </div>
  )
}

export function GenreDetail() {
  const { genre } = useParams()
  const [songs, setSongs] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setSongs(null)
    setError(null)
    getGenreSongs(genre, 50)
      .then((data) => { if (!cancelled) setSongs(data.songs) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [genre, reloadKey])

  const art = useArtwork(songs || [])

  return (
    <div className="space-y-4">
      <div>
        <Link to="/genres" className="text-xs text-muted hover:text-text transition">← All genres</Link>
        <h1 className="text-xl font-semibold tracking-tight capitalize mt-1">{genre}</h1>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
      ) : songs === null ? (
        <SongListSkeleton rows={10} />
      ) : songs.length === 0 ? (
        <EmptyState title="No songs" hint={`Nothing in the catalogue is tagged “${genre}”.`} />
      ) : (
        <>
          <div className="rounded-lg border border-border overflow-hidden bg-surface">
            {songs.map((song) => (
              <SongRow key={song.song_id} song={song} art={art[song.song_id]} showScore={false} />
            ))}
          </div>
          <SpotifyLogo />
        </>
      )}
    </div>
  )
}
