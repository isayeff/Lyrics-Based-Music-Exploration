"""Album art from Spotify (client-credentials token, no user login).

Only fetched for songs being shown, cached in memory, never stored in the DB.
Missing art just means no entry; the frontend draws a colour block instead.
"""
import os
import time
import base64
import logging
from concurrent.futures import ThreadPoolExecutor

import requests

log = logging.getLogger("spotify")

TOKEN_URL = "https://accounts.spotify.com/api/token"
TRACKS_URL = "https://api.spotify.com/v1/tracks"
OEMBED_URL = "https://open.spotify.com/oembed"
BATCH_SIZE = 50       # Spotify's max ids per batch /tracks call
CACHE_TTL = 24 * 3600  # 24h for a successful lookup
MISS_TTL = 45         # seconds to remember a FAILED lookup
MAX_WORKERS = 3       # parallelism for the per-track fallback (Spotify rate-limits hard)

_token = {"value": None, "expires_at": 0}
_art_cache = {}  # song_id -> (expires_at, {"url":..., "spotify_url":...} | None)

# Batch /tracks?ids= returns 403 for new apps, single /tracks/{id} works (D35).
# Set on the first 403, then fetch tracks one by one.
_batch_blocked = False

# Quota errors (429 with a long Retry-After) last for hours, so switch to the
# oEmbed endpoint, which needs no token.
_api_quota_exhausted = False


def credentials_configured():
    return bool(os.environ.get("SPOTIFY_CLIENT_ID") and os.environ.get("SPOTIFY_CLIENT_SECRET"))


def _get_token():
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    if not credentials_configured():
        return None

    creds = f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}"
    auth = base64.b64encode(creds.encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {auth}"},
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()
    _token["value"] = payload["access_token"]
    _token["expires_at"] = time.time() + payload.get("expires_in", 3600)
    return _token["value"]


def _cached(song_id):
    """(is_fresh, art) - distinguishes 'not cached / expired' from 'known to have none'."""
    entry = _art_cache.get(song_id)
    if entry and time.time() < entry[0]:
        return True, entry[1]
    return False, None


def get_artwork(song_to_spotify):
    """{song_id: spotify_id} -> {song_id: {"url":..., "spotify_url":...}}.

    Songs with no spotify_id, no artwork, or a failed fetch are simply absent
    from the result.
    """
    out = {}
    pending = {}

    for song_id, spotify_id in song_to_spotify.items():
        if not spotify_id:
            continue
        fresh, art = _cached(song_id)
        if fresh:
            if art:
                out[song_id] = art
            # a fresh negative entry means "recently tried and failed" - skip it
        else:
            # never fetched, or the entry has expired: try again
            pending[song_id] = spotify_id

    if not pending:
        return out

    token = _get_token()
    if not token:
        log.warning("Spotify credentials not configured; artwork unavailable, UI falls back")
        return out

    by_spotify_id = {}
    for song_id, spotify_id in pending.items():
        by_spotify_id.setdefault(spotify_id, []).append(song_id)

    spotify_ids = list(by_spotify_id)
    resolved = _fetch_tracks(spotify_ids, token)

    now = time.time()
    for spotify_id in spotify_ids:
        art = resolved.get(spotify_id)
        # A failed lookup (rate limit, network) must NOT be remembered for 24h,
        # or a single 429 burst blanks those songs for the rest of the day.
        expires = now + (CACHE_TTL if art else MISS_TTL)
        for song_id in by_spotify_id[spotify_id]:
            _art_cache[song_id] = (expires, art)
            if art:
                out[song_id] = art

    return out


def _art_from_track(track, spotify_id):
    images = (track or {}).get("album", {}).get("images") or []
    if not images:
        return None
    # smallest image at least 200px wide, else the smallest available;
    # displayed unmodified (resize only) per Spotify's terms
    sized = sorted(images, key=lambda im: im.get("width") or 0)
    return {
        "url": next((im["url"] for im in sized if (im.get("width") or 0) >= 200), sized[0]["url"]),
        "spotify_url": (track.get("external_urls") or {}).get(
            "spotify", f"https://open.spotify.com/track/{spotify_id}"
        ),
    }


def _fetch_tracks(spotify_ids, token):
    """{spotify_id: art|None} - batch where allowed, else concurrent single fetches."""
    global _batch_blocked
    headers = {"Authorization": f"Bearer {token}"}
    resolved = {}

    if not _batch_blocked:
        remaining = []
        for i in range(0, len(spotify_ids), BATCH_SIZE):
            batch = spotify_ids[i:i + BATCH_SIZE]
            try:
                resp = requests.get(
                    TRACKS_URL, params={"ids": ",".join(batch)}, headers=headers, timeout=10
                )
                if resp.status_code == 403:
                    log.info("Spotify batch /tracks refused (403); using per-track fetches")
                    _batch_blocked = True
                    remaining.extend(batch)
                    continue
                resp.raise_for_status()
                for spotify_id, track in zip(batch, resp.json().get("tracks") or []):
                    resolved[spotify_id] = _art_from_track(track, spotify_id)
            except Exception as exc:
                log.warning("Spotify batch fetch failed for %d ids: %s", len(batch), exc)

        if not _batch_blocked:
            return resolved
        spotify_ids = remaining + [s for s in spotify_ids if s not in resolved and s not in remaining]

    def fetch_via_oembed(spotify_id):
        """Unauthenticated fallback - no quota. Returns art or None."""
        try:
            resp = requests.get(
                OEMBED_URL,
                params={"url": f"https://open.spotify.com/track/{spotify_id}"},
                timeout=10,
            )
            resp.raise_for_status()
            thumb = resp.json().get("thumbnail_url")
            if not thumb:
                return None
            return {
                "url": thumb,
                "spotify_url": f"https://open.spotify.com/track/{spotify_id}",
            }
        except Exception as exc:
            log.warning("Spotify oEmbed failed for %s: %s", spotify_id, exc)
            return None

    def fetch_one(spotify_id):
        global _api_quota_exhausted
        if _api_quota_exhausted:
            return spotify_id, fetch_via_oembed(spotify_id)
        for attempt in (1, 2):
            try:
                resp = requests.get(f"{TRACKS_URL}/{spotify_id}", headers=headers, timeout=10)
                if resp.status_code == 429:
                    # A long Retry-After means the account quota is spent, not a
                    # momentary burst: switch the whole process to oEmbed rather
                    # than sleeping on every request.
                    wait = float(resp.headers.get("Retry-After", 1))
                    if wait > 30:
                        if not _api_quota_exhausted:
                            log.warning(
                                "Spotify Web API quota exhausted (Retry-After %.0fs); "
                                "falling back to oEmbed for artwork", wait
                            )
                        _api_quota_exhausted = True
                        return spotify_id, fetch_via_oembed(spotify_id)
                    if attempt == 1:
                        time.sleep(min(wait, 3.0))
                        continue
                resp.raise_for_status()
                return spotify_id, _art_from_track(resp.json(), spotify_id)
            except Exception as exc:
                if attempt == 2:
                    log.warning("Spotify track fetch failed for %s: %s", spotify_id, exc)
        return spotify_id, None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for spotify_id, art in pool.map(fetch_one, spotify_ids):
            resolved[spotify_id] = art

    return resolved
