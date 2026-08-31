import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import Artwork from '../components/Artwork'
import { SpotifyEmbed, SpotifyLogo, PlayButton } from '../components/Spotify'
import { DetailSkeleton, ErrorState } from '../components/States'
import useArtwork from '../useArtwork'
import { getSong } from '../api'
import { useAuth } from '../auth'

export default function SongDetail() {
  const { songId } = useParams()
  const { recordView } = useAuth()
  const [song, setSong] = useState(null)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setSong(null)
    setError(null)
    getSong(songId)
      .then((data) => {
        if (cancelled) return
        setSong(data)
        recordView(data)
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
    // recordView is intentionally omitted: it changes identity on every view push
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [songId, reloadKey])

  const art = useArtwork(song ? [song] : [])

  if (error) {
    return <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
  }
  if (!song) {
    return <DetailSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-4 items-start">
        <Artwork songId={song.song_id} art={art[song.song_id]} size={128} title={song.title} />

        <div className="min-w-0 flex-1">
          <div className="flex items-start gap-2">
            <div className="min-w-0">
              <h1 className="text-2xl font-semibold tracking-tight truncate">{song.title}</h1>
              <p className="text-muted mt-1 truncate">{song.artist}</p>
              {song.album_name && (
                <p className="text-muted text-sm mt-0.5 truncate">{song.album_name}</p>
              )}
            </div>
            <PlayButton spotifyId={song.spotify_id} title={song.title} />
          </div>

          {song.genres?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {song.genres.map((g) => (
                <Link
                  key={g}
                  to={`/genres/${encodeURIComponent(g)}`}
                  className="px-2.5 py-1 rounded-full border border-border bg-surface text-xs text-muted
                    hover:bg-surfaceHover hover:text-text transition capitalize"
                >
                  {g}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-medium">Listen</h2>
        <SpotifyEmbed spotifyId={song.spotify_id} />
        <SpotifyLogo />
      </section>

      {song.lyric_snippet && (
        <section className="space-y-2">
          <h2 className="text-sm font-medium">Lyric snippet</h2>
          <div className="rounded-lg border border-border bg-surface p-4">
            <p className="text-sm text-text whitespace-pre-line leading-relaxed">
              {song.lyric_snippet}
            </p>
          </div>
          <p className="text-xs text-muted">
            Snippet only — full lyrics are not stored or shown. Open the track on Spotify for the licensed source.
          </p>
        </section>
      )}

      {song.tags?.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-sm font-medium">Tags</h2>
          <div className="flex flex-wrap gap-1.5">
            {song.tags.map((t) => (
              <span key={t} className="px-2.5 py-1 rounded-full border border-border bg-surface text-xs text-muted">
                {t}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
