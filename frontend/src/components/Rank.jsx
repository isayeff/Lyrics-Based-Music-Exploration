/* Rank presentation for result rows.
 *
 * Raw fusion scores (0.0164...) are meaningless to a user, so the list leads
 * with position instead. The top three get medals, and each row shows which
 * retriever(s) found it and at what rank — which is what makes the hybrid
 * fusion legible: "dense #1 + sparse #21 -> fused #1". */

const MEDALS = {
  1: { fill: '#D4AF37', ring: '#8C6F1F', label: 'Best match' },
  2: { fill: '#B8BCC4', ring: '#7C8189', label: '2nd best match' },
  3: { fill: '#C2703F', ring: '#8B5A2B', label: '3rd best match' },
}

export function RankBadge({ rank }) {
  if (rank == null) return null

  const medal = MEDALS[rank]
  if (!medal) {
    return (
      <span className="w-7 shrink-0 text-center text-xs text-muted tabular-nums">
        {rank}
      </span>
    )
  }

  return (
    <span
      className="w-7 shrink-0 grid place-items-center"
      title={medal.label}
      aria-label={medal.label}
    >
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
        <circle cx="12" cy="12" r="9" fill={medal.fill} stroke={medal.ring} strokeWidth="1.5" />
        <text
          x="12" y="12" textAnchor="middle" dominantBaseline="central"
          fontSize="10" fontWeight="700" fill="#0A0A0B"
        >
          {rank}
        </text>
      </svg>
    </span>
  )
}

/* Dense and sparse are visually distinct so the user can tell which arm of the
   system produced a hit — dense = semantic match, sparse = literal word match. */
const RETRIEVER_STYLE = {
  dense: {
    className: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
    title: 'Dense retrieval (SBERT embeddings) — matched on meaning',
    short: 'D',
  },
  sparse: {
    className: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    title: 'Sparse retrieval (Postgres full-text) — matched on literal words',
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
          title="Found by both retrievers — Reciprocal Rank Fusion ranked it higher for agreeing"
        >
          both
        </span>
      )}
    </span>
  )
}
