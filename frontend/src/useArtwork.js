import { useEffect, useState } from 'react'
import { getArtwork } from './api'

/* Fetches artwork for exactly the songs passed in - the ones being rendered.
   Never backfills the corpus. Failures resolve to no artwork, and the UI falls
   back to its deterministic colour block. */
export default function useArtwork(songs) {
  const [art, setArt] = useState({})
  const ids = songs.map((s) => s.song_id).join(',')

  useEffect(() => {
    if (!ids) {
      setArt({})
      return
    }
    let cancelled = false
    getArtwork(ids.split(','))
      .then((data) => { if (!cancelled) setArt(data.artwork || {}) })
      .catch(() => { if (!cancelled) setArt({}) })
    return () => { cancelled = true }
  }, [ids])

  return art
}
