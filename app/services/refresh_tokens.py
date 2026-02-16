import hashlib
import secrets
from datetime import datetime, timedelta, timezone

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def refresh_expires(days: int = 30) -> datetime:
    return utcnow() + timedelta(days=days)
