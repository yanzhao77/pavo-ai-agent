import asyncio
import time
import json
import logging
from typing import Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AgnesAIError(Exception):
    """Base exception for Agnes AI API errors."""
    def __init__(self, message, status_code=None, original=None):
        self.status_code = status_code
        self.original = original
        super().__init__(message)


class AgnesAIRateLimitError(AgnesAIError):
    """Rate limited (429)."""
    pass


class AgnesAIModelNotFoundError(AgnesAIError):
    """Model not found (503)."""
    pass


class AgnesAITimeoutError(AgnesAIError):
    """Request timeout."""
    pass


def _classify_error(e, status_code=None):
    if status_code == 429:
        return AgnesAIRateLimitError(f"Rate limited: {e}", status_code=429, original=e)
    if status_code == 503:
        return AgnesAIModelNotFoundError(f"Model unavailable: {e}", status_code=503, original=e)
    if isinstance(e, httpx.TimeoutException):
        return AgnesAITimeoutError(f"Request timed out: {e}", original=e)
    return AgnesAIError(f"API error: {e}", status_code=status_code, original=e)


async def _retry_with_backoff(fn, max_retries=3, base_delay=1.0, max_delay=30.0):
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except (AgnesAIRateLimitError, AgnesAIModelNotFoundError) as e:
            last_exc = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Retry {attempt+1}/{max_retries} after {delay:.1f}s: {e}")
                await asyncio.sleep(delay)
        except AgnesAIError:
            raise
    raise last_exc


class AgnesAIClient:
    """Agnes AI Unified Model Gateway client using httpx directly."""

    def __init__(self):
        self.base_url = settings.agnes_api_base_url
        self.api_key = settings.agnes_api_key
        self._last_call = 0.0
        self._min_interval = 0.5
        self._timeout = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=10.0)
        self._client = httpx.AsyncClient(timeout=self._timeout)
        self.max_retries = 3
        self.retry_base_delay = 1.0
        self.retry_max_delay = 30.0

    async def _rate_limit(self):
        now = time.time()
        if now - self._last_call < self._min_interval:
            await asyncio.sleep(self._min_interval - (now - self._last_call))
        self._last_call = time.time()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(self, method, path, payload):
        await self._rate_limit()
        try:
            resp = await self._client.request(
                method, f"{self.base_url}{path}", headers=self._headers(), json=payload)
            if resp.status_code == 429:
                raise _classify_error(f"HTTP 429", status_code=429)
            if resp.status_code == 503:
                raise _classify_error(f"HTTP 503", status_code=503)
            resp.raise_for_status()
            return resp
        except httpx.TimeoutException as e:
            raise _classify_error(e)
        except httpx.HTTPStatusError as e:
            raise _classify_error(e, status_code=e.response.status_code)
        except AgnesAIError:
            raise
        except Exception as e:
            raise _classify_error(e)

    async def chat(self, messages, model="agnes-2.0-flash", temperature=0.7, max_tokens=4096, stream=False):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        async def _do_chat():
            resp = await self._request("POST", "/chat/completions", payload)
            if stream:
                chunks = []
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            if d.get("choices") and d["choices"][0].get("delta", {}).get("content"):
                                chunks.append(d["choices"][0]["delta"]["content"])
                        except json.JSONDecodeError:
                            pass
                return "".join(chunks)
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        try:
            return await _retry_with_backoff(_do_chat, self.max_retries, self.retry_base_delay, self.retry_max_delay)
        except AgnesAIError as e:
            logger.error(f"Agnes AI chat error (final): {e}")
            raise

    async def chat_stream(self, messages, model="agnes-2.0-flash", temperature=0.7, max_tokens=4096):
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async def _stream_attempt():
            async with self._client.stream(
                "POST", f"{self.base_url}/chat/completions",
                headers=self._headers(), json=payload,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            d = json.loads(line[6:])
                            if d.get("choices") and d["choices"][0].get("delta", {}).get("content"):
                                yield d["choices"][0]["delta"]["content"]
                        except json.JSONDecodeError:
                            pass

        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                async for chunk in _stream_attempt():
                    yield chunk
                return
            except (AgnesAIRateLimitError, AgnesAIModelNotFoundError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    delay = min(self.retry_base_delay * (2 ** attempt), self.retry_max_delay)
                    logger.warning(f"Stream retry {attempt+1}/{self.max_retries}")
                    await asyncio.sleep(delay)
            except Exception as e:
                yield f"\n[STREAM ERROR: {e}]"
                return
        yield f"\n[STREAM ERROR: {last_exc}]"

    async def generate_video(self, prompt, model="agnes-video-v2.0", n=1):
        payload = {"model": model, "prompt": prompt, "n": n}

        async def _do_video():
            resp = await self._request("POST", "/images/generations", payload)
            data = resp.json()
            return data.get("data", [{}])[0]

        try:
            return await _retry_with_backoff(_do_video, self.max_retries, self.retry_base_delay, self.retry_max_delay)
        except AgnesAIError as e:
            logger.error(f"Agnes AI video error (final): {e}")
            raise


agnes_client = AgnesAIClient()
