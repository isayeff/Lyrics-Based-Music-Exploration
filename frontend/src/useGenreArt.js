import { useEffect, useState } from 'react'
import { getGenreArt } from './api'

/* Artwork for exactly the genre tiles being rendered. Failure resolves to no
   art and the tiles fall back to their own colour blocks. */
export default function useGenreArt(genres) {
  const [art, setArt] = useState({})
  const key = genres.join(',')

  useEffect(() => {
    if (!key) {
      setArt({})
      return
    }
    let cancelled = false
    getGenreArt(key.split(','))
      .then((data) => { if (!cancelled) setArt(data.genre_art || {}) })
      .catch(() => { if (!cancelled) setArt({}) })
    return () => { cancelled = true }
  }, [key])

  return art
}
