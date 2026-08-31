"""Spotify Web API album art via client-credentials (app-only token, no user login — D6).

Artwork is fetched only for tracks actually being rendered and held in an in-memory
TTL cache; nothing is written to Postgres. If credentials are absent or a call
fails, callers get no entry for that song and the UI falls back to its own
deterministic colour block (never a broken image, never a third-party placeholder).
"""
import os
import time
import base64
import logging

import requests

log = logging.getLogger("spotify")

TOKEN_URL = "https://accounts.spotify.com/api/token"
TRACKS_URL = "https://api.spotify.com/v1/tracks"
BATCH_SIZE = 50       # Spotify's max ids per /tracks call
CACHE_TTL = 24 * 3600  # 24h

_token = {"value": None, "expires_at": 0}
_art_cache = {}  # song_id -> (expires_at, {"url":..., "spotify_url":...} | None)


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
    entry = _art_cache.get(song_id)
    if entry and time.time() < entry[0]:
        return entry[1]
    return None


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
        hit = _cached(song_id)
        if hit is not None:
            out[song_id] = hit
        elif song_id not in _art_cache:
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
    for i in range(0, len(spotify_ids), BATCH_SIZE):
        batch = spotify_ids[i:i + BATCH_SIZE]
        try:
            resp = requests.get(
                TRACKS_URL,
                params={"ids": ",".join(batch)},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            resp.raise_for_status()
            tracks = resp.json().get("tracks") or []
        except Exception as exc:  # network/rate-limit/malformed — degrade, don't fail the request
            log.warning("Spotify artwork fetch failed for %d ids: %s", len(batch), exc)
            continue

        for spotify_id, track in zip(batch, tracks):
            images = (track or {}).get("album", {}).get("images") or []
            art = None
            if images:
                # smallest image at least 200px wide, else the smallest available;
                # displayed unmodified (resize only) per Spotify's terms
                sized = sorted(images, key=lambda im: im.get("width") or 0)
                art = {
                    "url": next((im["url"] for im in sized if (im.get("width") or 0) >= 200), sized[0]["url"]),
                    "spotify_url": (track.get("external_urls") or {}).get(
                        "spotify", f"https://open.spotify.com/track/{spotify_id}"
                    ),
                }
            expires = time.time() + CACHE_TTL
            for song_id in by_spotify_id[spotify_id]:
                _art_cache[song_id] = (expires, art)
                if art:
                    out[song_id] = art

    return out
