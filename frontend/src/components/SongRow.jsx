import { useNavigate } from 'react-router-dom'
import Artwork from './Artwork'
import { RankBadge, RetrieverBadges } from './Rank'

/* Row-based result item (dense list, not cards). Hover lifts the surface —
   no red on hover; accent is reserved for interactive/active state.

   Play sends the user to our own song detail page with autoplay requested,
   rather than leaving for Spotify. The artwork itself still links out to the
   track on Spotify, which is what their display terms require. */
export default function SongRow({ song, art, showRank = true }) {
  const navigate = useNavigate()
  const genres = song.genres || []

  const open = (autoplay = false) =>
    navigate(`/song/${song.song_id}${autoplay ? '?play=1' : ''}`)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => open(false)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          open(false)
        }
      }}
      className="group flex items-center gap-3 px-3 py-2.5 border-b border-border last:border-b-0 hover:bg-surfaceHover transition cursor-pointer"
    >
      {showRank && <RankBadge rank={song.rank} />}

      <Artwork songId={song.song_id} art={art} size={48} title={song.title} />

      <div className="flex-1 min-w-0">
        <p className="text-text text-sm font-medium truncate">{song.title}</p>
        <p className="text-muted text-xs truncate">
          {song.artist}
          {genres.length > 0 && <span className="mx-1.5">·</span>}
          {genres.slice(0, 2).join(', ')}
        </p>
      </div>

      {showRank && <RetrieverBadges retrievers={song.retrievers} />}

      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); open(true) }}
        title={`Play ${song.title}`}
        className="shrink-0 grid place-items-center w-9 h-9 rounded-full text-accent
          hover:text-accentHover hover:bg-bg/60 transition opacity-70 group-hover:opacity-100"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
          <path d="M8 5v14l11-7z" />
        </svg>
        <span className="sr-only">Play {song.title}</span>
      </button>
    </div>
  )
}
