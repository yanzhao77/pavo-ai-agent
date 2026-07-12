from app.agents.base import BaseAgent

SCENE_PROMPT = """You are a scene designer. Based on the story and characters, create scene settings.
Provide: name, timeOfDay, environment (type, style, size, furniture, decor, flooring), lighting (type, color, mood), atmosphere, consistencyKey.
Return a JSON array."""

class SceneAgent(BaseAgent):
    def __init__(self):
        super().__init__("scene", SCENE_PROMPT)

    async def generate(self, input_text: str, characters: list) -> list:
        result = await self._call_structured([
            {"role": "user", "content": f"Create scene settings for this story:\n{input_text}\nCharacters: {str(characters)}\n\nReturn a JSON array of scenes."}
        ])
        return result if isinstance(result, list) else []
