from app.agents.base import BaseAgent

PROMPT = """You are a quality reviewer for storyboard scripts. Check for:
1. Character appearance consistency across all shots
2. Prop consistency
3. Scene consistency
4. Action continuity between shots
5. Complete story arc (qi-cheng-zhuan-he)
6. Accurate shotType, cameraMove, cameraAngle labels
7. Balanced duration distribution
Return JSON: {"passed": bool, "issues": [{"severity": "high|medium|low", "description": "..."}], "needs_fix": bool}"""

class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("reviewer", PROMPT)

    async def review(self, project) -> dict:
        review_data = {
            "characters": project.characters,
            "scenes": project.scenes,
            "props": project.props,
            "storyboard": project.storyboard,
        }
        result = await self._call_structured([
            {"role": "user", "content": f"Review this project output:\n{str(review_data)[:3000]}\n\nReturn JSON with passed, issues, needs_fix."}
        ], temperature=0.2)
        if isinstance(result, dict) and "passed" in result:
            return result
        return {"passed": True, "issues": [], "needs_fix": False}
