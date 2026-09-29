import { Link } from 'react-router-dom'

// 2x2 cover mosaic with the label underneath, not on top (Spotify terms, D34).

function hueFrom(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) hash = (hash * 31 + str.charCodeAt(i)) % 360
  return hash
}

function FallbackCell({ seed, index }) {
  const hue = (hueFrom(seed) + index * 34) % 360
  return <div style={{ background: `hsl(${hue} 28% ${16 + index * 3}%)` }} aria-hidden="true" />
}

export default function GenreTile({ genre, count, images = [] }) {
  const cells = Array.from({ length: 4 }, (_, i) => images[i] || null)

  return (
    <Link
      to={`/genres/${encodeURIComponent(genre)}`}
      className="group relative rounded-2xl bg-surface border border-border overflow-hidden
        transition-all duration-200 hover:border-white/15 hover:-translate-y-0.5
        hover:shadow-[0_8px_28px_-8px_rgba(0,0,0,0.65)] block"
    >
      <div className="grid grid-cols-2 grid-rows-2 aspect-square w-full gap-px bg-border/40">
        {cells.map((url, i) =>
          url ? (
            <img
              key={i}
              src={url}
              alt=""
              loading="lazy"
              className="w-full h-full object-contain bg-bg transition duration-300
                group-hover:brightness-110"
            />
          ) : (
            <FallbackCell key={i} seed={genre} index={i} />
          )
        )}
      </div>

      <div className="px-3.5 py-3 flex items-center gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-semibold capitalize truncate tracking-tight
            group-hover:text-accent transition-colors">
            {genre}
          </p>
          {count != null && (
            <p className="text-[11px] text-muted mt-0.5 tabular-nums">
              {count.toLocaleString()} songs
            </p>
          )}
        </div>
        <span className="shrink-0 text-muted group-hover:text-accent group-hover:translate-x-0.5
          transition-all duration-200" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </div>
    </Link>
  )
}
