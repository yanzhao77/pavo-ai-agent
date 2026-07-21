from app.agents.base import BaseAgent

PROMPT = "You are a prop designer. Create anchor props for the story. For each prop provide: name, type (anchor/prop), appearance, interaction, scene, characters, significance. Return a JSON array."

class PropAgent(BaseAgent):
    def __init__(self):
        super().__init__("prop", PROMPT)

    async def generate(self, input_text: str, characters: list, scenes: list) -> list:
        result = await self._call_structured([
            {"role": "user", "content": f"Create props for this story:\n{input_text}\nCharacters: {str(characters)}\nScenes: {str(scenes)}\n\nReturn a JSON array."}
        ])
        return result if isinstance(result, list) else []
