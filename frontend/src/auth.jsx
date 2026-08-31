import { createContext, useContext, useMemo, useState } from 'react'

/* Auth seam.
 *
 * Real JWT auth against Postgres with hashed passwords is the planned next step
 * (D25 — fabricated test accounts only, so no real personal data and the ethics
 * self-declaration is unaffected). Until that backend exists, this context holds
 * the same shape the real one will (user, login, signup, logout, taste genres),
 * backed by in-memory state. Swapping in the API means rewriting the three
 * functions below, not the components that consume them.
 *
 * Deliberately in-memory: no credentials in localStorage, and nothing persists
 * across reload, so no fabricated account data lingers on disk.
 */

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [viewed, setViewed] = useState([])

  const value = useMemo(() => ({
    user,

    async login(email, password) {
      if (!email.trim() || !password) throw new Error('Email and password are required')
      // TODO(D25): POST /auth/login -> { token, user }; store token, send as Bearer.
      setUser({ email: email.trim(), tasteGenres: [] })
    },

    async signup(email, password, tasteGenres = []) {
      if (!email.trim() || !password) throw new Error('Email and password are required')
      if (password.length < 8) throw new Error('Password must be at least 8 characters')
      // TODO(D25): POST /auth/signup with hashed-password storage server-side.
      setUser({ email: email.trim(), tasteGenres })
    },

    logout() {
      setUser(null)
      setViewed([])
    },

    setTasteGenres(genres) {
      setUser((prev) => (prev ? { ...prev, tasteGenres: genres } : prev))
    },

    /** Viewed-song history feeds the personalised home (D25). */
    viewed,
    recordView(song) {
      if (!song?.song_id) return
      setViewed((prev) => [song, ...prev.filter((s) => s.song_id !== song.song_id)].slice(0, 20))
    },
  }), [user, viewed])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
