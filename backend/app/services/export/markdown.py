"""Export converters for storyboard data."""

def storyboard_to_markdown(project) -> str:
    sb = project.storyboard or {}
    lines = []
    lines.append("# " + sb.get("projectName", "Untitled"))
    lines.append("")
    if sb.get("globalBGM"):
        lines.append("**BGM:** " + sb["globalBGM"])
        lines.append("")
    for scene in sb.get("scenes", []):
        title = scene.get("title", "Scene")
        lines.append("## " + title)
        lines.append("- Duration: " + scene.get("duration", "N/A"))
        lines.append("- Mood: " + scene.get("mood", "N/A"))
        lines.append("- Music: " + scene.get("music", "N/A"))
        lines.append("")
        for shot in scene.get("shots", []):
            lines.append("### Shot #" + str(shot.get("shotNumber", "?")))
            lines.append("- Type: " + shot.get("shotType", "N/A"))
            lines.append("- Camera: " + shot.get("cameraMove", "N/A"))
            chars = ", ".join(shot.get("characters", []))
            if chars:
                lines.append("- Characters: " + chars)
            desc = shot.get("description", "")
            if desc:
                lines.append("- Action: " + desc)
            dial = shot.get("dialogue", "")
            if dial and dial != "-":
                lines.append("- Dialogue: " + dial)
            lines.append("")
    return chr(10).join(lines)


def storyboard_to_script(project) -> str:
    sb = project.storyboard or {}
    lines = ["Project: " + sb.get("projectName", "Untitled")]
    lines.append("BGM: " + sb.get("globalBGM", "N/A"))
    lines.append("=" * 40)
    for scene in sb.get("scenes", []):
        lines.append("")
        lines.append(scene.get("title", "Scene"))
        lines.append("-" * 30)
        for shot in scene.get("shots", []):
            sn = shot.get("shotNumber", "?")
            st = shot.get("shotType", "")
            cm = shot.get("cameraMove", "")
            ca = shot.get("cameraAngle", "")
            dur = shot.get("duration", "")
            desc = shot.get("description", "")[:60]
            chars = ", ".join(shot.get("characters", []))[:30]
            lines.append(f"  {sn}. [{st}] [{cm}/{ca}] ({dur}) {desc}")
            if chars:
                lines.append(f"      Cast: {chars}")
    return chr(10).join(lines)
