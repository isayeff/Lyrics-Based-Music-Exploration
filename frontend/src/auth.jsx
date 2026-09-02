import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as api from './api'

/* Real JWT auth against Postgres with bcrypt-hashed passwords (D25, D41).
 *
 * Accounts are fabricated test accounts only — no real personal data — so the
 * ethics self-declaration (D23) is unaffected.
 *
 * The token is kept in sessionStorage rather than localStorage: it survives a
 * page reload during a demo but does not persist after the browser closes. */

const AuthContext = createContext(null)
const TOKEN_KEY = 'lyricfind_token'

function readToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null // private mode / storage blocked
  }
}

function writeToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable — session simply won't survive reload
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(readToken)
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  // restore the session on load if a token is present
  useEffect(() => {
    if (!token) {
      setUser(null)
      setReady(true)
      return
    }
    let cancelled = false
    api.getMe(token)
      .then((data) => { if (!cancelled) setUser(data) })
      .catch(() => {
        if (cancelled) return
        writeToken(null)   // expired or invalid
        setToken(null)
        setUser(null)
      })
      .finally(() => { if (!cancelled) setReady(true) })
    return () => { cancelled = true }
  }, [token])

  const adopt = useCallback((data) => {
    writeToken(data.token)
    setToken(data.token)
    setUser({ id: data.id, email: data.email, taste_genres: data.taste_genres })
  }, [])

  const value = useMemo(() => ({
    user,
    token,
    ready,

    async login(email, password) {
      adopt(await api.login(email.trim(), password))
    },

    async signup(email, password, tasteGenres = []) {
      adopt(await api.signup(email.trim(), password, tasteGenres))
    },

    logout() {
      writeToken(null)
      setToken(null)
      setUser(null)
    },

    async setTasteGenres(genres) {
      if (!token) return
      setUser(await api.updateTaste(token, genres))
    },

    /** Viewed-song history feeds the personalised home (D25). */
    recordView(song) {
      if (!token || !song?.song_id) return
      api.recordHistory(token, song.song_id).catch(() => {
        // history is a nicety; never block or surface a failure here
      })
    },
  }), [user, token, ready, adopt])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
