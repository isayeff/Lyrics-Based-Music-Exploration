/* Spotify developer terms constrain this component:
 *   - artwork is displayed UNMODIFIED (resize only, never cropped)
 *   - nothing is drawn on top: no overlays, gradients, logos or text
 *   - the play affordance lives BESIDE the artwork (see PlayButton), never on it
 *   - every artwork thumbnail links to the track on Spotify
 * If there is no spotify_id, or the fetch failed, we render a deterministic
 * colour block derived from the song id — never a broken image, never a
 * third-party placeholder. */

function hueFromId(songId) {
  let hash = 0
  for (let i = 0; i < songId.length; i++) {
    hash = (hash * 31 + songId.charCodeAt(i)) % 360
  }
  return hash
}

function FallbackBlock({ songId, size }) {
  const hue = hueFromId(songId)
  return (
    <div
      className="shrink-0 rounded"
      style={{
        width: size,
        height: size,
        background: `linear-gradient(135deg, hsl(${hue} 32% 26%), hsl(${(hue + 40) % 360} 30% 16%))`,
      }}
      aria-hidden="true"
    />
  )
}

export default function Artwork({ songId, art, size = 48, title }) {
  if (!art?.url) {
    return <FallbackBlock songId={songId} size={size} />
  }

  return (
    <a
      href={art.spotify_url}
      target="_blank"
      rel="noopener noreferrer"
      className="shrink-0 rounded overflow-hidden block"
      style={{ width: size, height: size }}
      title={title ? `${title} on Spotify` : 'Open on Spotify'}
    >
      {/* object-contain, not object-cover: resizing is permitted, cropping is not */}
      <img
        src={art.url}
        alt=""
        width={size}
        height={size}
        className="w-full h-full object-contain"
        loading="lazy"
      />
    </a>
  )
}
