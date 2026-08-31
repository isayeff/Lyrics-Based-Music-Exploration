const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      // non-JSON error body — keep the status-code message
    }
    throw new Error(detail)
  }
  return res.json()
}

export function search({ query, mode = 'hybrid', limit = 20 }) {
  return request('/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, mode, limit }),
  })
}

export function getSong(songId) {
  return request(`/song/${encodeURIComponent(songId)}`)
}

export function getGenres(limit = 60) {
  return request(`/genres?limit=${limit}`)
}

export function getGenreSongs(genre, limit = 50) {
  return request(`/genre/${encodeURIComponent(genre)}?limit=${limit}`)
}

/** Artwork only for songs actually being rendered — never a corpus backfill. */
export function getArtwork(songIds) {
  if (!songIds.length) return Promise.resolve({ artwork: {} })
  return request(`/artwork?ids=${songIds.map(encodeURIComponent).join(',')}`)
}
