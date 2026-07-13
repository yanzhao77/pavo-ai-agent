from app.agents.base import BaseAgent

PROMPT = "You are a fixer agent. Given review feedback and the original storyboard, fix the identified issues. Return the corrected storyboard in the same JSON format."

class FixerAgent(BaseAgent):
    def __init__(self):
        super().__init__("fixer", PROMPT)

    async def fix(self, project, review_result: dict) -> dict:
        storyboard = project.storyboard
        issues = review_result.get("issues", [])
        result = await self._call_structured([
            {"role": "user", "content": f"Fix these issues in the storyboard:\nIssues: {str(issues)}\n\nOriginal storyboard:\n{str(storyboard)[:3000]}\n\nReturn the fixed storyboard JSON."}
        ], temperature=0.3)
        if isinstance(result, dict) and "scenes" in result:
            return result
        return storyboard
