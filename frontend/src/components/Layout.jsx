import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAuth } from '../auth'

function navClass({ isActive }) {
  return `px-3 py-1.5 rounded-lg text-sm transition-colors ${
    isActive
      ? 'bg-surfaceHover text-accent font-medium'
      : 'text-muted hover:text-text hover:bg-surfaceHover'
  }`
}

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 mr-4 shrink-0 group" title="Home">
      <span className="grid place-items-center w-8 h-8 rounded-xl bg-accent shrink-0
        shadow-[0_0_16px_-4px_rgba(232,0,3,0.7)] group-hover:shadow-[0_0_20px_-2px_rgba(232,0,3,0.85)]
        transition-shadow">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="#fff" aria-hidden="true">
          <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z" />
        </svg>
      </span>
      <span className="font-semibold tracking-tight text-[15px] leading-none">
        NoLyrics<span className="text-accent">.</span>find
      </span>
    </Link>
  )
}

export default function Layout() {
  const { user } = useAuth()

  return (
    <div className="min-h-full flex flex-col bg-bg">
      <header className="border-b border-border bg-surface/70 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-1">
          <Logo />

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navClass}>Home</NavLink>
            <NavLink to="/genres" className={navClass}>Genres</NavLink>
            <NavLink to="/about" className={navClass}>About</NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <NavLink
                to="/profile"
                title={user.email}
                className={({ isActive }) =>
                  `grid place-items-center w-9 h-9 rounded-full text-sm font-semibold uppercase
                   border transition ${
                     isActive
                       ? 'bg-accent border-accent text-white'
                       : 'bg-surfaceHover border-border text-muted hover:text-text hover:border-white/20'
                   }`
                }
              >
                {user.email.slice(0, 1)}
                <span className="sr-only">Your profile</span>
              </NavLink>
            ) : (
              <NavLink
                to="/login"
                className="group relative flex items-center gap-2 h-9 pl-4 pr-4 rounded-full
                  bg-accent hover:bg-accentHover text-white text-sm font-semibold tracking-tight
                  shadow-[0_0_18px_-5px_rgba(232,0,3,0.9)]
                  hover:shadow-[0_0_24px_-4px_rgba(232,0,3,1)]
                  hover:-translate-y-px active:translate-y-0
                  transition-all duration-200"
              >
                <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor"
                     strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
                     className="shrink-0" aria-hidden="true">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                  <path d="M10 17l5-5-5-5" />
                  <path d="M15 12H3" />
                </svg>
                Log in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-border mt-10">
        <div className="max-w-5xl mx-auto px-4 py-7 grid gap-6 sm:grid-cols-3 text-xs text-muted">
          <div className="space-y-2">
            <p className="text-text font-semibold tracking-tight">NoLyrics.find</p>
            <p className="leading-relaxed">
              Describe a song in your own words and find it - no title, artist or lyrics needed.
              84,103 songs searched by meaning.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-text font-medium">How it works</p>
            <p><span className="text-sky-300 font-medium">Dense</span> - SBERT embeddings, matched on meaning.</p>
            <p><span className="text-amber-300 font-medium">Sparse</span> - Postgres full-text, matched on words.</p>
            <p><span className="text-accent font-medium">Hybrid</span> - both, fused with Reciprocal Rank Fusion.</p>
            <Link to="/about" className="inline-block hover:text-accent transition-colors">Read more →</Link>
          </div>

          <div className="space-y-2">
            <p className="text-text font-medium">Data &amp; rights</p>
            <p className="leading-relaxed">
              Catalogue from the music4all dataset. Lyrics are indexed but never redistributed -
              short snippets only, linking to the licensed source. Album art and playback by Spotify.
            </p>
          </div>
        </div>
        <div className="border-t border-border/60">
          <div className="max-w-5xl mx-auto px-4 py-3.5 text-[11px] text-muted/70">
            MSc dissertation project · University of Sheffield
          </div>
        </div>
      </footer>
    </div>
  )
}
