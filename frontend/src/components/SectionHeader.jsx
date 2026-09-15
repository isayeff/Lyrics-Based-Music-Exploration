import { Link } from 'react-router-dom'

/* Section heading with an accent rule, an optional subtitle and an optional
   trailing link. Used to give the home/browse sections structure rather than a
   bare bold line. */
export default function SectionHeader({ title, subtitle, actionLabel, actionTo }) {
  return (
    <div className="flex items-end justify-between gap-4 pb-1">
      <div className="min-w-0">
        <div className="flex items-center gap-2.5">
          <span className="w-1 h-5 rounded-full bg-accent shrink-0" aria-hidden="true" />
          <h2 className="text-[17px] font-semibold tracking-tight">{title}</h2>
        </div>
        {subtitle && <p className="text-xs text-muted mt-1 ml-3.5">{subtitle}</p>}
      </div>

      {actionLabel && actionTo && (
        <Link
          to={actionTo}
          className="shrink-0 text-xs text-muted hover:text-accent transition-colors
            flex items-center gap-1 group"
        >
          {actionLabel}
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor"
               strokeWidth="2.2" className="group-hover:translate-x-0.5 transition-transform"
               aria-hidden="true">
            <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
      )}
    </div>
  )
}
