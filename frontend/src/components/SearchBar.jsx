import { useEffect, useRef, useState } from 'react'

/* Explicit submit only — never search-as-you-type. Recent searches (held in
   React state, see App.jsx) drop down on focus. */
export default function SearchBar({ initialValue = '', recent = [], onSubmit, autoFocus = false, size = 'md' }) {
  const [value, setValue] = useState(initialValue)
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)

  useEffect(() => setValue(initialValue), [initialValue])

  useEffect(() => {
    function onClickAway(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickAway)
    return () => document.removeEventListener('mousedown', onClickAway)
  }, [])

  function submit(query) {
    const q = query.trim()
    if (!q) return
    setOpen(false)
    onSubmit(q)
  }

  const big = size === 'lg'

  return (
    <div ref={wrapRef} className="relative w-full">
      <form
        onSubmit={(e) => { e.preventDefault(); submit(value) }}
        className="flex gap-2"
        role="search"
      >
        <input
          type="text"
          value={value}
          autoFocus={autoFocus}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => { if (e.key === 'Escape') setOpen(false) }}
          placeholder="Describe a song in your own words…"
          aria-label="Describe a song"
          className={`flex-1 min-w-0 rounded-md bg-surface border border-border text-text placeholder:text-muted
            focus:border-accent outline-none transition ${big ? 'px-4 py-3.5 text-base' : 'px-3 py-2 text-sm'}`}
        />
        <button
          type="submit"
          disabled={!value.trim()}
          className={`shrink-0 rounded-md bg-accent hover:bg-accentHover disabled:opacity-40 disabled:hover:bg-accent
            text-white font-medium transition ${big ? 'px-6 py-3.5' : 'px-4 py-2 text-sm'}`}
        >
          Search
        </button>
      </form>

      {open && recent.length > 0 && (
        <div className="absolute z-20 mt-1.5 w-full rounded-md border border-border bg-surface shadow-xl overflow-hidden">
          <p className="px-3 pt-2.5 pb-1.5 text-xs text-muted">Recent searches</p>
          <ul>
            {recent.map((q) => (
              <li key={q}>
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => { setValue(q); submit(q) }}
                  className="w-full text-left px-3 py-2 text-sm text-text hover:bg-surfaceHover transition truncate"
                >
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
