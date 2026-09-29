// Rank medals for the top three, and D#/S# badges showing which retriever
// found each result and at what rank.

const MEDALS = {
  1: {
    label: 'Best match',
    face: '#F4D03F', faceDark: '#C9971B', edge: '#8A6A12', text: '#4A3708',
    glow: 'rgba(244, 208, 63, 0.35)',
  },
  2: {
    label: '2nd best match',
    face: '#D8DDE4', faceDark: '#A3AAB4', edge: '#6F757E', text: '#3A3E44',
    glow: 'rgba(216, 221, 228, 0.28)',
  },
  3: {
    label: '3rd best match',
    face: '#E0955E', faceDark: '#B06A34', edge: '#7A4620', text: '#432408',
    glow: 'rgba(224, 149, 94, 0.28)',
  },
}

export function RankBadge({ rank }) {
  if (rank == null) return null

  const medal = MEDALS[rank]
  if (!medal) {
    return (
      <span className="w-8 shrink-0 text-center text-[13px] text-muted/70 tabular-nums font-medium">
        {rank}
      </span>
    )
  }

  const gid = `medal${rank}`
  return (
    <span
      className="w-8 shrink-0 grid place-items-center"
      title={medal.label}
      aria-label={`${medal.label}, rank ${rank}`}
    >
      <svg viewBox="0 0 28 28" width="26" height="26" aria-hidden="true"
           style={{ filter: `drop-shadow(0 0 5px ${medal.glow})` }}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0.35" y2="1">
            <stop offset="0%" stopColor={medal.face} />
            <stop offset="55%" stopColor={medal.face} />
            <stop offset="100%" stopColor={medal.faceDark} />
          </linearGradient>
        </defs>

        {/* ribbon tails behind the disc */}
        <path d="M9.5 17.5 L6.5 26 L10.6 23.6 L12.6 26.5 L14.4 19.5 Z" fill={medal.faceDark} opacity="0.85" />
        <path d="M18.5 17.5 L21.5 26 L17.4 23.6 L15.4 26.5 L13.6 19.5 Z" fill={medal.edge} opacity="0.85" />

        <circle cx="14" cy="12" r="9.4" fill={medal.edge} />
        <circle cx="14" cy="12" r="8.4" fill={`url(#${gid})`} />
        {/* inner bevel ring */}
        <circle cx="14" cy="12" r="6.6" fill="none" stroke={medal.edge} strokeOpacity="0.35" strokeWidth="0.9" />
        {/* highlight */}
        <ellipse cx="11.2" cy="8.4" rx="3.1" ry="2.1" fill="#fff" opacity="0.32" />

        <text x="14" y="12.4" textAnchor="middle" dominantBaseline="central"
              fontSize="9.5" fontWeight="800" fill={medal.text}
              fontFamily="ui-sans-serif, system-ui, sans-serif">
          {rank}
        </text>
      </svg>
    </span>
  )
}

/* Dense and sparse are visually distinct so the user can tell which arm of the
   system produced a hit - dense = semantic match, sparse = literal word match. */
const RETRIEVER_STYLE = {
  dense: {
    className: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
    title: 'Dense retrieval (SBERT embeddings) - matched on meaning',
    short: 'D',
  },
  sparse: {
    className: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    title: 'Sparse retrieval (Postgres full-text) - matched on literal words',
    short: 'S',
  },
}

export function RetrieverBadges({ retrievers }) {
  const entries = Object.entries(retrievers || {})
  if (entries.length === 0) return null

  return (
    <span className="hidden sm:flex shrink-0 items-center gap-1">
      {entries.map(([name, rank]) => {
        const style = RETRIEVER_STYLE[name]
        if (!style) return null
        return (
          <span
            key={name}
            title={`${style.title} (rank ${rank})`}
            className={`px-1.5 py-0.5 rounded border text-[10px] font-medium tabular-nums ${style.className}`}
          >
            {style.short}#{rank}
          </span>
        )
      })}
      {entries.length > 1 && (
        <span
          className="px-1.5 py-0.5 rounded border border-accent/40 bg-accent/10 text-accent text-[10px] font-medium"
          title="Found by both retrievers - Reciprocal Rank Fusion ranked it higher for agreeing"
        >
          both
        </span>
      )}
    </span>
  )
}
