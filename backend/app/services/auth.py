"""Auth service — token creation, verification, and revocation.

Design:
  - Primary store is an in-memory dict (_token_cache).  All synchronous
    callers (create_token / verify_token / revoke_token) operate on this
    cache only, so they are always fast and never block.
  - DB persistence is handled by two *async* helpers (load_tokens_from_db /
    save_tokens_to_db) that are called explicitly from async startup/shutdown
    hooks in app/main.py.  They are never invoked from synchronous code.
  - This avoids the asyncio.get_event_loop().run_until_complete() anti-pattern
    which caused deadlocks when called from inside a running event loop
    (e.g. pytest-asyncio tests).
"""
import hashlib
import json
import logging
import secrets
import time
from typing import Optional

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days
_CONFIG_KEY = "auth_tokens"

# Primary in-memory store: sha256(token) -> {"user_id": str, "expires_at": float}
_token_cache: dict = {}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Async DB persistence (called from app lifespan, never from sync code)
# ─────────────────────────────────────────────────────────────────────────────

async def load_tokens_from_db() -> None:
    """Populate in-memory cache from SQLite on startup.

    Safe to call only from an async context (e.g. FastAPI lifespan).
    Silently skips if the table does not exist yet.
    """
    global _token_cache
    try:
        from app.db.database import get_config
        raw = await get_config(_CONFIG_KEY, "{}")
        loaded = json.loads(raw)
        _token_cache.update(loaded)
        logger.info(f"Loaded {len(loaded)} auth token(s) from DB")
    except Exception as e:
        logger.warning(f"Could not load auth tokens from DB (non-fatal): {e}")


async def save_tokens_to_db() -> None:
    """Persist in-memory cache to SQLite.

    Safe to call only from an async context.
    """
    try:
        from app.db.database import set_config
        await set_config(_CONFIG_KEY, json.dumps(_token_cache))
        logger.debug(f"Persisted {len(_token_cache)} auth token(s) to DB")
    except Exception as e:
        logger.warning(f"Could not save auth tokens to DB (non-fatal): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Public synchronous API (always fast — memory only)
# ─────────────────────────────────────────────────────────────────────────────

def create_token(user_id: str) -> str:
    """Create a new auth token for *user_id* and store it in memory."""
    token = secrets.token_hex(32)
    _token_cache[_hash_token(token)] = {
        "user_id": user_id,
        "expires_at": time.time() + TOKEN_EXPIRY_SECONDS,
    }
    return token


def verify_token(token: str) -> Optional[str]:
    """Return *user_id* for a valid, non-expired token, or ``None``."""
    if not token:
        return None
    h = _hash_token(token)
    entry = _token_cache.get(h)
    if not entry:
        return None
    if time.time() > entry["expires_at"]:
        del _token_cache[h]
        return None
    return entry["user_id"]


def revoke_token(token: str) -> bool:
    """Remove a token from the store.  Returns ``True`` if it existed."""
    h = _hash_token(token)
    if h in _token_cache:
        del _token_cache[h]
        return True
    return False


def clean_expired() -> int:
    """Remove all expired tokens from memory.  Returns the count removed."""
    now = time.time()
    expired = [h for h, e in list(_token_cache.items()) if now > e["expires_at"]]
    for h in expired:
        del _token_cache[h]
    if expired:
        logger.info(f"Cleaned {len(expired)} expired auth token(s)")
    return len(expired)
