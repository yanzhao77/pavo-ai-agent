"""Embedding client — calls a real OpenAI-compatible embedding API.

Supported providers (configured via environment variables):
  - Agnes AI  (default): AGNES_API_KEY + AGNES_API_BASE_URL
  - OpenAI:              OPENAI_API_KEY  (set EMBEDDING_API_BASE to https://api.openai.com/v1)
  - Any OpenAI-compatible endpoint: EMBEDDING_API_KEY + EMBEDDING_API_BASE

Environment variables:
  EMBEDDING_API_KEY    — API key (falls back to AGNES_API_KEY then OPENAI_API_KEY)
  EMBEDDING_API_BASE   — Base URL (default: https://apihub.agnes-ai.com/v1)
  EMBEDDING_MODEL      — Model name (default: text-embedding-ada-002)
  EMBEDDING_DIMENSION  — Vector dimension (default: 1536)
"""

import asyncio
import hashlib
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Embedding vectorization client with cache."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[int] = None,
        batch_size: int = 100,
        max_retries: int = 3,
        timeout: float = 30.0,
        cache_ttl: int = 3600,
    ):
        # Resolve API credentials from environment with fallback chain
        self.api_key = api_key or self._resolve_api_key()
        self.api_base = (api_base or os.environ.get("EMBEDDING_API_BASE", "https://apihub.agnes-ai.com/v1")).rstrip("/")
        self.model = model or os.environ.get("EMBEDDING_MODEL", "text-embedding-ada-002")
        try:
            self.dimension = dimension or int(os.environ.get("EMBEDDING_DIMENSION", "1536"))
        except ValueError:
            self.dimension = 1536
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, list[float]]] = {}
        self._stats = {"hits": 0, "misses": 0, "api_calls": 0}

    @staticmethod
    def _resolve_api_key() -> str:
        """Resolve embedding API key from environment, with fallback chain."""
        for var in ("EMBEDDING_API_KEY", "AGNES_API_KEY", "OPENAI_API_KEY"):
            val = os.environ.get(var, "").strip()
            if val:
                return val
        return ""

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
        """Call the OpenAI-compatible /embeddings endpoint.

        If no API key is configured, falls back to deterministic mock vectors
        so development/testing can proceed without credentials.
        """
        if not self.api_key:
            logger.warning(
                "No embedding API key found (EMBEDDING_API_KEY / AGNES_API_KEY / OPENAI_API_KEY). "
                "Falling back to deterministic mock vectors. Set an API key for production use."
            )
            return self._mock_vectors(texts)

        url = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}

        for attempt in range(self.max_retries):
            try:
                self._stats["api_calls"] += 1
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                # Sort by index to preserve original order
                embeddings = sorted(data["data"], key=lambda x: x["index"])
                vectors = [item["embedding"] for item in embeddings]

                # Warn on dimension mismatch
                if vectors and len(vectors[0]) != self.dimension:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {self.dimension}, "
                        f"got {len(vectors[0])}. Update EMBEDDING_DIMENSION if needed."
                    )
                return vectors

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Embedding API HTTP error (attempt {attempt + 1}): "
                    f"{e.response.status_code} {e.response.text}"
                )
                if e.response.status_code in (401, 403):
                    raise  # No point retrying auth errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except Exception as e:
                logger.warning(f"Embedding API attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    def _mock_vectors(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic unit vectors for development/testing only."""
        import random
        result = []
        for t in texts:
            seed = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
            rng = random.Random(seed)
            vec = [rng.gauss(0, 0.1) for _ in range(self.dimension)]
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            result.append([x / norm for x in vec])
        return result

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "hit_rate": self._stats["hits"] / total if total > 0 else 0,
            "api_base": self.api_base,
            "model": self.model,
            "has_api_key": bool(self.api_key),
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
