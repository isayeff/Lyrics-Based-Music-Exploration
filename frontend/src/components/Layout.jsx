import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAuth } from '../auth'

function navClass({ isActive }) {
  return `px-3 py-1.5 rounded-md text-sm transition ${
    isActive
      ? 'bg-surfaceHover text-accent font-medium'
      : 'text-muted hover:text-text hover:bg-surfaceHover'
  }`
}

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 mr-3 shrink-0" title="Home">
      <span className="grid place-items-center w-7 h-7 rounded-md bg-accent shrink-0">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="#fff" aria-hidden="true">
          <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
        </svg>
      </span>
      <span className="font-semibold tracking-tight text-[15px]">
        Lyric<span className="text-accent">.</span>find
      </span>
    </Link>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-full flex flex-col bg-bg">
      <header className="border-b border-border bg-surface/70 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-1">
          <Logo />

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navClass}>Home</NavLink>
            <NavLink to="/genres" className={navClass}>Genres</NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                <span
                  className="hidden sm:grid place-items-center w-7 h-7 rounded-full bg-surfaceHover
                    border border-border text-xs font-medium uppercase"
                  title={user.email}
                >
                  {user.email.slice(0, 1)}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="px-3 py-1.5 rounded-md text-sm text-muted hover:text-text hover:bg-surfaceHover transition"
                >
                  Log out
                </button>
              </>
            ) : (
              <NavLink
                to="/login"
                className="px-3.5 py-1.5 rounded-md bg-accent hover:bg-accentHover text-white text-sm font-medium transition"
              >
                Log in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-border mt-8">
        <div className="max-w-5xl mx-auto px-4 py-6 grid gap-4 sm:grid-cols-3 text-xs text-muted">
          <div className="space-y-1.5">
            <p className="text-text font-medium">Lyric.find</p>
            <p>Free-text music retrieval over 84,103 songs, matching natural-language
              descriptions to lyrics using sentence embeddings.</p>
          </div>

          <div className="space-y-1.5">
            <p className="text-text font-medium">How it works</p>
            <p><span className="text-sky-300">Dense</span> — SBERT embeddings, matched on meaning.</p>
            <p><span className="text-amber-300">Sparse</span> — Postgres full-text, matched on words.</p>
            <p><span className="text-accent">Hybrid</span> — both, fused with Reciprocal Rank Fusion.</p>
          </div>

          <div className="space-y-1.5">
            <p className="text-text font-medium">Data &amp; rights</p>
            <p>Catalogue from the music4all dataset. Lyrics are indexed but never
              redistributed — short snippets only, linking to the licensed source.</p>
            <p>Album art and playback provided by Spotify.</p>
          </div>
        </div>
        <div className="max-w-5xl mx-auto px-4 pb-6 text-[11px] text-muted/70">
          MSc dissertation project · University of Sheffield
        </div>
      </footer>
    </div>
  )
}
