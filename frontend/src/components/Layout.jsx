import { NavLink, Outlet, Link } from 'react-router-dom'
import { useAuth } from '../auth'

function navClass({ isActive }) {
  return `px-3 py-1.5 rounded-md text-sm transition ${
    isActive ? 'bg-surfaceHover text-accent font-medium' : 'text-muted hover:text-text hover:bg-surfaceHover'
  }`
}

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-full flex flex-col bg-bg">
      <header className="border-b border-border bg-surface/60 backdrop-blur sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-2">
          <Link to="/" className="font-semibold tracking-tight mr-2">
            Lyric<span className="text-accent">.</span>find
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navClass}>Home</NavLink>
            <NavLink to="/genres" className={navClass}>Genres</NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                <span className="text-xs text-muted hidden sm:inline truncate max-w-[16ch]">{user.email}</span>
                <button
                  type="button"
                  onClick={logout}
                  className="px-3 py-1.5 rounded-md text-sm text-muted hover:text-text hover:bg-surfaceHover transition"
                >
                  Log out
                </button>
              </>
            ) : (
              <NavLink to="/login" className={navClass}>Log in</NavLink>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-border py-4">
        <div className="max-w-5xl mx-auto px-4 text-xs text-muted">
          Lyrics shown as short snippets only, linking out to the licensed source.
        </div>
      </footer>
    </div>
  )
}
