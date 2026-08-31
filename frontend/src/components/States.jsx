/* Loading uses skeletons, never spinners. Every fetch also gets an explicit
   empty state and an error state with a retry. */

export function SongRowSkeleton() {
  return (
    <div className="flex items-center gap-3 px-3 py-2.5 border-b border-border">
      <div className="skeleton w-12 h-12 rounded shrink-0" />
      <div className="flex-1 min-w-0 space-y-2">
        <div className="skeleton h-3.5 rounded w-1/3" />
        <div className="skeleton h-3 rounded w-1/5" />
      </div>
      <div className="skeleton h-3 rounded w-10 shrink-0" />
    </div>
  )
}

export function SongListSkeleton({ rows = 8 }) {
  return (
    <div aria-busy="true" aria-label="Loading results">
      {Array.from({ length: rows }, (_, i) => <SongRowSkeleton key={i} />)}
    </div>
  )
}

export function TileSkeleton({ count = 8 }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3" aria-busy="true">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="skeleton h-20 rounded-lg" />
      ))}
    </div>
  )
}

export function DetailSkeleton() {
  return (
    <div className="space-y-4" aria-busy="true">
      <div className="flex gap-4">
        <div className="skeleton w-32 h-32 rounded-lg shrink-0" />
        <div className="flex-1 space-y-3 pt-2">
          <div className="skeleton h-6 rounded w-1/2" />
          <div className="skeleton h-4 rounded w-1/3" />
          <div className="skeleton h-4 rounded w-1/4" />
        </div>
      </div>
      <div className="skeleton h-[152px] rounded-lg" />
    </div>
  )
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="text-center py-16 px-4">
      <p className="text-text font-medium">{title}</p>
      {hint && <p className="text-muted text-sm mt-1.5 max-w-md mx-auto">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="text-center py-16 px-4">
      <p className="text-text font-medium">Something went wrong</p>
      <p className="text-muted text-sm mt-1.5 max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 px-4 py-2 rounded-md bg-accent hover:bg-accentHover text-white text-sm font-medium transition"
        >
          Try again
        </button>
      )}
    </div>
  )
}
