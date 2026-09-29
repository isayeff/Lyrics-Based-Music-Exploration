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

// Embedded player. Browsers may still block autoplay, so the user might need
// to press play once.
export function SpotifyEmbed({ spotifyId, autoplay = false }) {
  if (!spotifyId) {
    return (
      <div className="rounded-lg border border-border bg-surface p-4 text-sm text-muted">
        No Spotify track linked for this song.
      </div>
    )
  }
  const src = `https://open.spotify.com/embed/track/${spotifyId}${autoplay ? '?autoplay=1' : ''}`
  return (
    <iframe
      title="Spotify player"
      src={src}
      width="100%"
      height="152"
      frameBorder="0"
      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
      className="rounded-lg"
    />
  )
}
