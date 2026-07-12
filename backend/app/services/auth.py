import secrets
import hashlib
import time
from typing import Optional

# In-memory token store: token_hash -> {user_id, expires_at}
_token_store: dict[str, dict] = {}

TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(user_id: str) -> str:
    """Create a new auth token for the given user."""
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    _token_store[token_hash] = {
        "user_id": user_id,
        "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
    }
    return token


def verify_token(token: str) -> Optional[str]:
    """Verify a token and return user_id, or None if invalid."""
    token_hash = _hash_token(token)
    entry = _token_store.get(token_hash)
    if not entry:
        return None
    if time.time() > entry["expires_at"]:
        del _token_store[token_hash]
        return None
    return entry["user_id"]


def revoke_token(token: str) -> bool:
    """Revoke a token."""
    token_hash = _hash_token(token)
    return bool(_token_store.pop(token_hash, None))


def clean_expired():
    """Remove expired tokens."""
    now = time.time()
    expired = [h for h, e in _token_store.items() if now > e["expires_at"]]
    for h in expired:
        del _token_store[h]
    return len(expired)
