from app.agents.base import BaseAgent

STORYBOARD_PROMPT = """
You are a professional storyboard artist and screenwriter. Create a shot-by-shot storyboard.

IMPORTANT: Return ONLY a valid JSON object with this exact structure:

EXAMPLE 1 (family story):
{
  "projectName": "The Lost Kite",
  "globalBGM": "Gentle piano, warm",
  "scenes": [
    {
      "title": "Act 1 - Setup",
      "duration": "12s",
      "mood": "Warm",
      "music": "BGM: Piano | SFX: Birds",
      "keyframe": "Child looking up at kite",
      "shots": [
        {
          "shotNumber": 1,
          "shotType": "全景",
          "cameraMove": "固定",
          "cameraAngle": "平视",
          "description": "A wide shot of a park. A red kite is stuck in a tree.",
          "dialogue": "-",
          "duration": "0-6s",
          "characters": ["Xiao Ming"]
        }
      ]
    }
  ]
}

EXAMPLE 2 (romantic):
See the JSON structure with fields: projectName, globalBGM, scenes[].title/duration/mood/music/keyframe/shots[].shotNumber/shotType/cameraMove/cameraAngle/description/dialogue/duration/characters

Requirements:
- 3-4 acts following qi-cheng-zhuan-he structure
- Total duration 30-60 seconds
- Each scene has BGM and SFX text descriptions
- Each shot has ALL required fields
- Chinese for shotType/cameraMove/cameraAngle
- shotType: 远景,全景,中景,中近景,近景,特写
- cameraMove: 固定,横移,推近,拉远,摇移,跟拍
- cameraAngle: 平视,平视微俯,平视侧面
VERIFICATION CHECKLIST:
1. Sum of shot durations equals scene duration
2. Shot numbers are sequential
3. Listed characters exist in character data
4. shotType/cameraMove/cameraAngle from allowed list
5. Valid parseable JSON (test with json.loads before returning)
"""

class StoryboardAgent(BaseAgent):
    def __init__(self):
        super().__init__("storyboard", STORYBOARD_PROMPT)

    async def generate(self, input_text, characters, scenes, props):
        result = await self._call_structured([
            {"role": "user", "content": f"Create a storyboard for: {input_text}\n\nCharacters: {str(characters)}\nScenes: {str(scenes)}\nProps: {str(props)}\n\nReturn valid JSON storyboard."}
        ], temperature=0.4)
        if isinstance(result, dict) and "scenes" in result:
            return result
        return {"projectName": "", "globalBGM": "", "scenes": []}
