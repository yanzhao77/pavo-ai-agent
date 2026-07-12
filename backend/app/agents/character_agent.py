from app.agents.base import BaseAgent

CHARACTER_PROMPT = """You are a character designer. Based on the story input, create character settings.
For each character provide: name, role (main/supporting), age, gender, appearance (build, face, eyes, hair, clothing, distinctive), personality (list), voice, relationship, consistencyKey (a short English description for T2V model).
Return a JSON array."""

class CharacterAgent(BaseAgent):
    def __init__(self):
        super().__init__("character", CHARACTER_PROMPT)

    async def generate(self, input_text: str) -> list:
        result = await self._call_structured([
            {"role": "user", "content": f"Create character settings for this story:\n\n{input_text}\n\nReturn a JSON array of characters."}
        ])
        if isinstance(result, dict) and "raw" in result:
            return []
        return result if isinstance(result, list) else []
