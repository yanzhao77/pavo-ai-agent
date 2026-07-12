from app.agents.base import BaseAgent

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner", "You are a creative story analyst. Analyze the user input and extract key elements.")

    async def plan(self, input_text: str) -> dict:
        result = await self._call_structured([
            {"role": "user", "content": f"Analyze this story idea and extract: characters, setting, theme, emotion, suggested duration (30-60s).\n\nStory: {input_text}\n\nReturn JSON with keys: characters (list), scene, theme, emotion, duration"}
        ])
        return result
