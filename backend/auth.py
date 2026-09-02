"""Authentication: Postgres-backed accounts, bcrypt password hashes, JWT sessions.

Per D25 this is populated with fabricated test accounts only — no real personal
data — so the ethics self-declaration (D23) is unaffected. Passwords are never
stored or logged in plaintext; only the bcrypt hash is persisted.
"""
import os
import time
import logging

import jwt
import bcrypt
from sqlalchemy import text

log = logging.getLogger("auth")

JWT_ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 7 * 24 * 3600  # 7 days

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_user (
    id            bigserial PRIMARY KEY,
    email         text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    taste_genres  text[] NOT NULL DEFAULT '{}',
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS user_view (
    user_id    bigint NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    song_id    text NOT NULL,
    viewed_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, song_id)
);
"""


def jwt_secret():
    """Dev fallback keeps the app runnable without config; production must set it."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        log.warning("JWT_SECRET not set — using an insecure development default")
        return "dev-only-insecure-secret-change-me"
    return secret


def init_schema(engine):
    with engine.begin() as conn:
        for statement in filter(None, (s.strip() for s in SCHEMA.split(";"))):
            conn.execute(text(statement))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def make_token(user_id: int, email: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": str(user_id), "email": email, "iat": now, "exp": now + TOKEN_TTL_SECONDS},
        jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str):
    """Returns the payload, or None if the token is invalid or expired."""
    try:
        return jwt.decode(token, jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def create_user(conn, email: str, password: str, taste_genres):
    row = conn.execute(
        text("""
            INSERT INTO app_user (email, password_hash, taste_genres)
            VALUES (:email, :hash, :genres)
            RETURNING id, email, taste_genres
        """),
        {"email": email, "hash": hash_password(password), "genres": list(taste_genres or [])},
    ).fetchone()
    return row


def get_user_by_email(conn, email: str):
    return conn.execute(
        text("SELECT id, email, password_hash, taste_genres FROM app_user WHERE email = :email"),
        {"email": email},
    ).fetchone()


def get_user(conn, user_id: int):
    return conn.execute(
        text("SELECT id, email, taste_genres FROM app_user WHERE id = :id"),
        {"id": user_id},
    ).fetchone()


def set_taste_genres(conn, user_id: int, genres):
    conn.execute(
        text("UPDATE app_user SET taste_genres = :g WHERE id = :id"),
        {"g": list(genres or []), "id": user_id},
    )


def record_view(conn, user_id: int, song_id: str):
    conn.execute(
        text("""
            INSERT INTO user_view (user_id, song_id, viewed_at)
            VALUES (:uid, :sid, now())
            ON CONFLICT (user_id, song_id) DO UPDATE SET viewed_at = now()
        """),
        {"uid": user_id, "sid": song_id},
    )


def recent_views(conn, user_id: int, limit: int = 20):
    return conn.execute(
        text("""
            SELECT song_id FROM user_view
            WHERE user_id = :uid
            ORDER BY viewed_at DESC
            LIMIT :lim
        """),
        {"uid": user_id, "lim": limit},
    ).fetchall()
