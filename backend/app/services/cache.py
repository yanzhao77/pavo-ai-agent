"""In-memory cache with TTL - replaces Redis for Session Memory."""
import logging
from cachetools import TTLCache
logger = logging.getLogger(__name__)

class PavoCache:
    def __init__(self, maxsize=10000, ttl=1800):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
    def get(self, key): return self._cache.get(key)
    def set(self, key, value, ttl=1800): self._cache[key] = value
    def delete(self, key): return self._cache.pop(key, None) is not None
    def touch(self, key, ttl=1800):
        if key in self._cache:
            val = self._cache.pop(key); self._cache[key] = val
    def size(self): return len(self._cache)
    def clear(self): self._cache.clear()

pavo_cache = PavoCache()
