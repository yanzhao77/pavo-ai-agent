"""PDF export using reportlab."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def storyboard_to_pdf(project) -> bytes:
    """Generate PDF bytes from project storyboard data."""
    sb = project.storyboard or {}
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin

    def draw_text(text, size=10, indent=0):
        nonlocal y
        c.setFont("Helvetica", size)
        if y < margin + 20:
            c.showPage()
            y = height - margin
        c.drawString(margin + indent, y, text)
        y -= size * 0.5 + 4

    draw_text(sb.get("projectName", "Untitled"), 16)
    y -= 4
    if sb.get("globalBGM"):
        draw_text("BGM: " + sb["globalBGM"], 8)
        y -= 4

    for scene in sb.get("scenes", []):
        if y < margin + 40:
            c.showPage()
            y = height - margin
        y -= 4
        draw_text(scene.get("title", "Scene"), 13)
        draw_text("Duration: " + scene.get("duration", "N/A"), 9)
        draw_text("Mood: " + scene.get("mood", "N/A"), 9)
        y -= 2

        for shot in scene.get("shots", []):
            sn = shot.get("shotNumber", "?")
            st = shot.get("shotType", "N/A")
            cm = shot.get("cameraMove", "N/A")
            dur = shot.get("duration", "N/A")
            desc = shot.get("description", "")[:80]
            chars = ", ".join(shot.get("characters", []))
            draw_text(f"Shot #{sn}: [{st}] {cm} ({dur})", 9, 10)
            if desc:
                draw_text(desc, 8, 20)
            if chars:
                draw_text("Cast: " + chars, 8, 20)
            y -= 1

    c.save()
    buf.seek(0)
    return buf.getvalue()
