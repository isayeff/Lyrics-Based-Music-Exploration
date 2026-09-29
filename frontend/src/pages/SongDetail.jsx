import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import Artwork from '../components/Artwork'
import { SpotifyEmbed, SpotifyLogo } from '../components/Spotify'
import { DetailSkeleton, ErrorState } from '../components/States'
import useArtwork from '../useArtwork'
import { getSong } from '../api'
import { useAuth } from '../auth'

export default function SongDetail() {
  const { songId } = useParams()
  const [params] = useSearchParams()
  const autoplay = params.get('play') === '1'
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
    // recordView identity changes on every view push; including it would loop
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [songId, reloadKey])

  const art = useArtwork(song ? [song] : [])

  if (error) return <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />
  if (!song) return <DetailSkeleton />

  return (
    <div className="space-y-6">
      {/* lyrics left, song card right */}
      <div className="grid lg:grid-cols-[1fr_20rem] gap-6 items-start">
        <div className="space-y-5 order-2 lg:order-1">
          <section className="space-y-2">
            <h2 className="text-sm font-medium">Listen</h2>
            <SpotifyEmbed spotifyId={song.spotify_id} autoplay={autoplay} />
          </section>

          {song.lyric_snippet && (
            <section className="space-y-2">
              <h2 className="text-sm font-medium">Lyric snippet</h2>
              <div className="rounded-xl border border-border bg-linear-to-br from-[#1a1a2e] to-[#14141c] p-5">
                <p className="text-[15px] text-text/90 whitespace-pre-line leading-[1.9] font-medium">
                  {song.lyric_snippet}
                </p>
              </div>
              <p className="text-xs text-muted">
                Opening lines only. Full lyrics are never stored or displayed - they are used
                to build the search index, and the licensed source is a click away on Spotify.
              </p>
            </section>
          )}

          {song.tags?.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-sm font-medium">Themes &amp; tags</h2>
              <div className="flex flex-wrap gap-1.5">
                {song.tags.map((t) => (
                  <span
                    key={t}
                    className="px-2.5 py-1 rounded-full border border-border bg-surface text-xs text-muted"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>

        <aside className="order-1 lg:order-2 lg:sticky lg:top-20">
          <div className="rounded-xl border border-border bg-surface p-4 space-y-3">
            <div className="flex justify-center">
              <Artwork songId={song.song_id} art={art[song.song_id]} size={224} title={song.title} />
            </div>

            <div className="space-y-1 pt-1">
              <h1 className="text-lg font-semibold tracking-tight leading-snug">{song.title}</h1>
              <p className="text-muted text-sm">{song.artist}</p>
              {song.album_name && <p className="text-muted text-xs">{song.album_name}</p>}
            </div>

            {song.genres?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {song.genres.map((g) => (
                  <Link
                    key={g}
                    to={`/genres/${encodeURIComponent(g)}`}
                    className="px-2.5 py-1 rounded-full border border-border bg-bg text-xs text-muted
                      hover:bg-surfaceHover hover:text-text transition capitalize"
                  >
                    {g}
                  </Link>
                ))}
              </div>
            )}

            {song.spotify_id && (
              <a
                href={`https://open.spotify.com/track/${song.spotify_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center px-4 py-2 rounded-md bg-accent hover:bg-accentHover
                  text-white text-sm font-medium transition"
              >
                Open on Spotify
              </a>
            )}

            <SpotifyLogo />
          </div>
        </aside>
      </div>
    </div>
  )
}
