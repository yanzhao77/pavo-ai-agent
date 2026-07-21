import json
import logging
from app.services.agnes_client import agnes_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a professional AI film director and screenwriter. Respond in Chinese."

class BaseAgent:
    def __init__(self, name: str, system_prompt: str = SYSTEM_PROMPT):
        self.name = name
        self.system_prompt = system_prompt

    async def _call(self, messages, temperature=0.7, max_tokens=4096, stream=False):
        full = [{"role": "system", "content": self.system_prompt}] + messages
        return await agnes_client.chat(full, temperature=temperature, max_tokens=max_tokens, stream=stream)

    async def _call_structured(self, messages, temperature=0.3, max_tokens=4096):
        full = [{"role": "system", "content": self.system_prompt}] + messages
        result = await agnes_client.chat(full, temperature=temperature, max_tokens=max_tokens)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning(f"{self.name}: failed to parse JSON, returning raw text")
            return {"raw": result}

    async def _stream(self, messages, temperature=0.7, max_tokens=4096):
        full = [{"role": "system", "content": self.system_prompt}] + messages
        async for chunk in agnes_client.chat_stream(full, temperature=temperature, max_tokens=max_tokens):
            yield chunk
