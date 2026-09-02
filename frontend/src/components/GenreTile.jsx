import { Link } from 'react-router-dom'

/* Genre tile = 2x2 mosaic of unmodified album covers, with the genre label
 * BELOW the images. Spotify's display terms forbid text, logos or gradients
 * drawn over their artwork (D34), so the label never overlaps the mosaic.
 * Falls back to deterministic colour blocks derived from the genre name when
 * artwork is unavailable. */

function hueFrom(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = (hash * 31 + str.charCodeAt(i)) % 360
  return hash
}

function FallbackCell({ seed, index }) {
  const hue = (hueFrom(seed) + index * 34) % 360
  return <div style={{ background: `hsl(${hue} 30% ${18 + index * 4}%)` }} aria-hidden="true" />
}

export default function GenreTile({ genre, count, images = [] }) {
  const cells = Array.from({ length: 4 }, (_, i) => images[i] || null)

  return (
    <Link
      to={`/genres/${encodeURIComponent(genre)}`}
      className="group rounded-xl border border-border bg-surface overflow-hidden
        hover:bg-surfaceHover transition block"
    >
      <div className="grid grid-cols-2 grid-rows-2 aspect-square w-full">
        {cells.map((url, i) =>
          url ? (
            <img
              key={i}
              src={url}
              alt=""
              loading="lazy"
              className="w-full h-full object-contain bg-bg"
            />
          ) : (
            <FallbackCell key={i} seed={genre} index={i} />
          )
        )}
      </div>

      <div className="px-3 py-2.5">
        <p className="text-sm font-medium capitalize truncate group-hover:text-accent transition">
          {genre}
        </p>
        {count != null && (
          <p className="text-xs text-muted mt-0.5">{count.toLocaleString()} songs</p>
        )}
      </div>
    </Link>
  )
}
