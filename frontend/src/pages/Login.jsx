import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../auth'
import { getGenres } from '../api'
import PasswordStrength from '../components/PasswordStrength'

/* Login / signup. Signup includes the taste-onboarding genre picks that feed the
   personalised home (D25). Accounts are fabricated test accounts only — no real
   personal data — and auth is currently client-side until the JWT backend lands. */
export default function Login() {
  const navigate = useNavigate()
  const { login, signup } = useAuth()

  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [picked, setPicked] = useState([])
  const [genres, setGenres] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    getGenres(18)
      .then((data) => { if (!cancelled) setGenres(data.genres) })
      .catch(() => { if (!cancelled) setGenres([]) })
    return () => { cancelled = true }
  }, [])

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (tab === 'login') await login(email, password)
      else await signup(email, password, picked)
      navigate('/')
    } catch (err) {
      // shown both inline (persistent, next to the form) and as a toast
      setError(err.message)
      toast.error(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-md mx-auto space-y-5 pt-6">
      <div className="flex rounded-md border border-border bg-surface p-0.5">
        {['login', 'signup'].map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => { setTab(t); setError(null) }}
            className={`flex-1 px-3 py-2 rounded text-sm font-medium transition ${
              tab === t ? 'bg-accent text-white' : 'text-muted hover:text-text hover:bg-surfaceHover'
            }`}
          >
            {t === 'login' ? 'Log in' : 'Sign up'}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="space-y-3">
        <div className="space-y-1.5">
          <label htmlFor="email" className="block text-xs text-muted">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md bg-surface border border-border px-3 py-2 text-sm outline-none focus:border-accent transition"
          />
        </div>

        <div className="space-y-1.5">
          <label htmlFor="password" className="block text-xs text-muted">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            autoComplete={tab === 'signup' ? 'new-password' : 'current-password'}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md bg-surface border border-border px-3 py-2 text-sm outline-none focus:border-accent transition"
          />
          {tab === 'signup' && <PasswordStrength password={password} />}
        </div>

        {tab === 'signup' && (
          <div className="space-y-2 pt-1">
            <p className="text-xs text-muted">Pick a few genres you like</p>
            {genres === null ? (
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: 10 }, (_, i) => (
                  <div key={i} className="skeleton h-7 w-20 rounded-full" />
                ))}
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {genres.map((g) => {
                  const active = picked.includes(g.genre)
                  return (
                    <button
                      key={g.genre}
                      type="button"
                      onClick={() => setPicked((p) =>
                        active ? p.filter((x) => x !== g.genre) : [...p, g.genre]
                      )}
                      className={`px-3 py-1.5 rounded-full text-xs border transition capitalize ${
                        active
                          ? 'bg-accent border-accent text-white font-medium'
                          : 'bg-surface border-border text-muted hover:bg-surfaceHover hover:text-text'
                      }`}
                    >
                      {g.genre}
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {error && <p className="text-sm text-text bg-surface border border-border rounded-md px-3 py-2">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-md bg-accent hover:bg-accentHover disabled:opacity-40 text-white text-sm font-medium py-2.5 transition"
        >
          {busy ? 'Working…' : tab === 'login' ? 'Log in' : 'Create account'}
        </button>
      </form>

      <p className="text-xs text-muted text-center">
        Test accounts only. Any email and an 8+ character password will work — no real
        personal data is collected or stored.
      </p>
    </div>
  )
}
