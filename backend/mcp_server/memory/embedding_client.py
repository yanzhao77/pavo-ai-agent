"""Embedding client with caching and batch support."""

import hashlib
import logging
import time
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Embedding vectorization client with cache."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
        batch_size: int = 100,
        max_retries: int = 3,
        timeout: float = 30.0,
        cache_ttl: int = 3600,
    ):
        self.model = model
        self.dimension = dimension
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[list[float], float]] = {}
        self._stats = {"hits": 0, "misses": 0, "api_calls": 0}

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    async def embed(self, text: str) -> list[float]:
        """Single text vectorization (with cache)."""
        key = self._cache_key(text)
        now = time.time()

        # Check cache
        if key in self._cache:
            cached_time, cached_vec = self._cache[key]
            if now - cached_time < self.cache_ttl:
                self._stats["hits"] += 1
                return cached_vec

        self._stats["misses"] += 1
        vectors = await self._call_embedding_api([text])
        self._cache[key] = (now, vectors[0])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch vectorization."""
        results = []
        uncached_texts = []
        uncached_indices = []

        now = time.time()
        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self._cache:
                cached_time, cached_vec = self._cache[key]
                if now - cached_time < self.cache_ttl:
                    results.append(cached_vec)
                    self._stats["hits"] += 1
                    continue
            uncached_texts.append(text)
            uncached_indices.append(i)

        if uncached_texts:
            self._stats["misses"] += len(uncached_texts)
            vectors = await self._call_embedding_api(uncached_texts)
            for idx, vec in zip(uncached_indices, vectors):
                key = self._cache_key(uncached_texts[idx])
                self._cache[key] = (now, vec)
                results.insert(idx, vec)

        return results

    async def _call_embedding_api(self, texts: list[str]) -> list[list[float]]:
        """
        Call embedding API.
        For development: returns mock vectors.
        For production: replace with actual API call (OpenAI / Agnes AI compatible).
        """
        for attempt in range(self.max_retries):
            try:
                self._stats["api_calls"] += 1
                # Placeholder: generate deterministic mock vectors for development
                import hashlib
                dimension = self.dimension
                result = []
                for t in texts:
                    seed = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
                    import random
                    rng = random.Random(seed)
                    vec = [rng.gauss(0, 0.1) for _ in range(dimension)]
                    norm = sum(x * x for x in vec) ** 0.5
                    vec = [x / norm for x in vec]  # unit vector
                    result.append(vec)
                return result
            except Exception as e:
                logger.warning(f"Embedding API attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "hit_rate": self._stats["hits"] / total if total > 0 else 0,
        }

    def clear_cache(self):
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "api_calls": 0}


# Singleton instance
_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client
