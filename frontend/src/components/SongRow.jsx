import { useNavigate } from 'react-router-dom'
import Artwork from './Artwork'
import { PlayButton } from './Spotify'

/* Row-based result item (dense list, not cards). Hover lifts the surface —
   no red on hover; accent is reserved for interactive/active state. */
export default function SongRow({ song, art, showScore = true }) {
  const navigate = useNavigate()
  const genres = song.genres || []

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/song/${song.song_id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          navigate(`/song/${song.song_id}`)
        }
      }}
      className="group flex items-center gap-3 px-3 py-2.5 border-b border-border hover:bg-surfaceHover transition cursor-pointer"
    >
      {song.rank != null && (
        <span className="w-6 shrink-0 text-right text-xs text-muted tabular-nums">{song.rank}</span>
      )}

      <Artwork songId={song.song_id} art={art} size={48} title={song.title} />

      <div className="flex-1 min-w-0">
        <p className="text-text text-sm font-medium truncate">{song.title}</p>
        <p className="text-muted text-xs truncate">
          {song.artist}
          {genres.length > 0 && <span className="mx-1.5">·</span>}
          {genres.slice(0, 2).join(', ')}
        </p>
      </div>

      {showScore && song.score != null && (
        <span
          className="shrink-0 text-xs text-muted tabular-nums"
          title={retrieverTitle(song.retrievers)}
        >
          {formatScore(song.score)}
        </span>
      )}

      <PlayButton spotifyId={song.spotify_id} title={song.title} />
    </div>
  )
}

function formatScore(score) {
  return score >= 1 ? score.toFixed(1) : score.toFixed(3)
}

function retrieverTitle(retrievers) {
  if (!retrievers) return undefined
  const parts = Object.entries(retrievers).map(([name, rank]) => `${name} #${rank}`)
  return parts.length ? `Matched by ${parts.join(', ')}` : undefined
}
