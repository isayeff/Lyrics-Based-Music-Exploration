/* Attribution + playback affordances for Spotify-sourced content.
 * The logo must appear on any view that shows Spotify-sourced content. */

export function SpotifyLogo({ className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-muted text-xs ${className}`}>
      <svg viewBox="0 0 24 24" width="14" height="14" fill="#1DB954" aria-hidden="true">
        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.5 17.32c-.22.36-.68.47-1.03.25-2.82-1.72-6.37-2.11-10.55-1.16-.4.09-.8-.16-.89-.56-.09-.4.16-.8.56-.89 4.57-1.05 8.5-.6 11.66 1.33.36.22.47.68.25 1.03zm1.47-3.27c-.28.45-.86.59-1.31.32-3.23-1.98-8.15-2.56-11.97-1.4-.5.15-1.03-.13-1.18-.63-.15-.5.13-1.03.63-1.18 4.37-1.33 9.79-.68 13.5 1.59.45.28.59.86.32 1.3zm.13-3.4C15.23 8.42 8.85 8.2 5.2 9.3c-.6.18-1.24-.16-1.42-.76-.18-.6.16-1.24.76-1.42 4.19-1.27 11.24-1.02 15.67 1.61.54.32.72 1.02.4 1.56-.32.54-1.02.72-1.56.4z" />
      </svg>
      Content from Spotify
    </span>
  )
}

/* Play affordance sits BESIDE the artwork, never on top of it. */
export function PlayButton({ spotifyId, title }) {
  if (!spotifyId) return null
  return (
    <a
      href={`https://open.spotify.com/track/${spotifyId}`}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      title={title ? `Play ${title} on Spotify` : 'Play on Spotify'}
      className="shrink-0 grid place-items-center w-8 h-8 rounded-full text-accent hover:text-accentHover hover:bg-surfaceHover transition"
    >
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
        <path d="M8 5v14l11-7z" />
      </svg>
      <span className="sr-only">Play on Spotify</span>
    </a>
  )
}

/* oEmbed iframe player for the song detail page. */
export function SpotifyEmbed({ spotifyId }) {
  if (!spotifyId) {
    return (
      <div className="rounded-lg border border-border bg-surface p-4 text-sm text-muted">
        No Spotify track linked for this song.
      </div>
    )
  }
  return (
    <iframe
      title="Spotify player"
      src={`https://open.spotify.com/embed/track/${spotifyId}`}
      width="100%"
      height="152"
      frameBorder="0"
      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
      loading="lazy"
      className="rounded-lg"
    />
  )
}
