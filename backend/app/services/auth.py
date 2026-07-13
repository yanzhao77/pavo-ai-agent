"""Auth service — token creation, verification, and revocation.

Tokens are persisted in the SQLite system_config table under the key
"auth_tokens" as a JSON blob, so they survive process restarts.

The in-memory cache (_token_cache) avoids a DB round-trip on every request.
It is populated lazily on first access and invalidated on write.
"""
import asyncio
import hashlib
import json
import logging
import secrets
import time
from typing import Optional

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days
_CONFIG_KEY = "auth_tokens"

# In-memory write-through cache: token_hash -> {user_id, expires_at}
_token_cache: Optional[dict] = None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _load_tokens() -> dict:
    """Load token store from SQLite. Returns empty dict on any error."""
    try:
        from app.db.database import get_config
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In async context, we can't block; return empty and rely on cache
            return {}
        raw = loop.run_until_complete(get_config(_CONFIG_KEY, "{}"))
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Failed to load auth tokens from DB: {e}")
        return {}


def _save_tokens(store: dict) -> None:
    """Persist token store to SQLite asynchronously."""
    try:
        from app.db.database import set_config
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(set_config(_CONFIG_KEY, json.dumps(store)))
        else:
            loop.run_until_complete(set_config(_CONFIG_KEY, json.dumps(store)))
    except Exception as e:
        logger.warning(f"Failed to save auth tokens to DB: {e}")


def _get_store() -> dict:
    """Return the in-memory cache, loading from DB on first access."""
    global _token_cache
    if _token_cache is None:
        _token_cache = _load_tokens()
    return _token_cache


def create_token(user_id: str) -> str:
    """Create a new auth token for the given user and persist it."""
    token = secrets.token_hex(32)
    token_hash = _hash_token(token)
    store = _get_store()
    store[token_hash] = {
        "user_id": user_id,
        "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
    }
    _save_tokens(store)
    return token


def verify_token(token: str) -> Optional[str]:
    """Verify a token and return user_id, or None if invalid/expired."""
    token_hash = _hash_token(token)
    store = _get_store()
    entry = store.get(token_hash)
    if not entry:
        return None
    if time.time() > entry["expires_at"]:
        del store[token_hash]
        _save_tokens(store)
        return None
    return entry["user_id"]


def revoke_token(token: str) -> bool:
    """Revoke a token."""
    token_hash = _hash_token(token)
    store = _get_store()
    if token_hash in store:
        del store[token_hash]
        _save_tokens(store)
        return True
    return False


def clean_expired() -> int:
    """Remove expired tokens and persist the cleaned store.

    Called automatically on app startup (via app/main.py lifespan) and can
    also be triggered manually to prevent unbounded token store growth.
    """
    now = time.time()
    store = _get_store()
    expired = [h for h, e in store.items() if now > e["expires_at"]]
    if expired:
        for h in expired:
            del store[h]
        _save_tokens(store)
        logger.info(f"Cleaned {len(expired)} expired auth token(s)")
    return len(expired)
