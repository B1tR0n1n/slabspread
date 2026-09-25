"""Owner authentication (plan §6): a single owner account, no public signup.

Two production modes, one test mode:
  local     — owner email + pbkdf2 password hash from env; signed session cookie.
  supabase  — the login page uses supabase-js with the anon key; the resulting access token
              is POSTed to /login/token, verified here with the project's JWT secret (HS256),
              and accepted only if its email equals SLABSPREAD_OWNER_EMAIL.
  off       — no auth; allowed only with SLABSPREAD_DEBUG=1 (tests).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

import jwt
from fastapi import HTTPException, Request

from config import settings

SESSION_KEY = "owner"


def make_hash(password: str, *, iterations: int = 200_000, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def check_hash(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, dk_b64 = stored.split("$")
        assert algo == "pbkdf2_sha256"
    except (ValueError, AssertionError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(iters))
    return hmac.compare_digest(dk, base64.b64decode(dk_b64))


def verify_local(email: str, password: str) -> bool:
    return bool(settings.owner_email and settings.owner_password_hash) and (
        hmac.compare_digest(email.strip().lower(), settings.owner_email.lower())
        and check_hash(password, settings.owner_password_hash)
    )


def verify_supabase_token(token: str) -> str:
    """Return the email inside a valid Supabase access token, or raise."""
    if not settings.supabase_jwt_secret:
        raise HTTPException(500, "supabase_jwt_secret not configured")
    try:
        claims = jwt.decode(
            token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated"
        )
    except jwt.PyJWTError as e:
        raise HTTPException(401, f"invalid token: {e}") from e
    email = (claims.get("email") or "").lower()
    if not email or email != settings.owner_email.lower():
        raise HTTPException(403, "not the owner")
    return email


def current_owner(request: Request) -> str | None:
    return request.session.get(SESSION_KEY)


def require_owner(request: Request) -> str:
    """FastAPI dependency for every private route."""
    if settings.auth_mode == "off":
        if not settings.debug:
            raise HTTPException(500, "auth_mode=off requires SLABSPREAD_DEBUG=1")
        return settings.owner_email or "owner@localhost"
    who = current_owner(request)
    if not who:
        raise HTTPException(status_code=303, headers={"Location": f"/login?next={request.url.path}"})
    return who


if __name__ == "__main__":  # python -m app.auth 'your password'  → hash for .env
    import sys

    print(make_hash(sys.argv[1]))
