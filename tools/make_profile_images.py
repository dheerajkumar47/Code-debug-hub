"""Generate the Freelancer cover banner + portfolio thumbnails into profile/images/.

    pip install pillow && python tools/make_profile_images.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "profile" / "images"
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts"]

BG_TOP, BG_BOTTOM = (9, 20, 44), (18, 52, 96)
ACCENT = (34, 211, 238)
WHITE, MUTED = (245, 248, 252), (160, 180, 205)
CHIP_BG = (30, 64, 110)

ITEMS = [
    ("01-ai-receptionist", "AI Receptionist", "WhatsApp · Instagram · Messenger AI agent with booking & voice replies",
     ["Azure OpenAI", "WhatsApp API", "Graph API", ".NET"]),
    ("02-cctv-tracking", "Real-Time CCTV Tracking", "Live RTSP feeds · YOLO person detection · ArUco employee ID · heatmaps",
     ["YOLO", "OpenCV", "CUDA", "Python"]),
    ("03-rag-langgraph", "RAG Chatbot + LangGraph Router", "Vector search + web search agent that answers from your data",
     ["LangGraph", "Pinecone", "FastAPI", "Gemini"]),
    ("04-psx-dashboard", "AI Stock Market Dashboard (PSX)", "Live market data + AI daily summaries and SWOT per company",
     ["FastAPI", "React", "MongoDB", "Gemini"]),
    ("05-interview-agents", "Multi-Agent Interview Platform", "4 AI agents · ATS resume scoring · readiness verdict",
     ["Next.js", "Gemini", "Groq", "Supabase"]),
    ("06-meeting-intelligence", "AI Meeting Intelligence", "Whisper transcripts → grounded Q&A over every meeting",
     ["Whisper", "RAG", "FastAPI", "Python"]),
    ("07-ai-qa-platform", "AI QA Platform", "Agents generate test cases from tickets and run UI/API tests",
     ["AI Agents", "LLM", "API Testing", "Python"]),
    ("08-anomaly-detection", "Time-Series Anomaly Detection", "Server, finance & IoT anomalies · Prophet + Isolation Forest",
     ["Prophet", "scikit-learn", "FastAPI", "Docker"]),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"] if bold else \
        ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    for d in FONT_DIRS:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def gradient(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = (y / h) * 0.7 + (x / w) * 0.3
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
    return img


def grid(draw: ImageDraw.ImageDraw, w: int, h: int, step: int = 48) -> None:
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 10))
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, 10))


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = f"{cur} {wd}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    return lines + [cur] if cur else lines


def chips(draw, x, y, labels, fnt, pad=16, gap=12, h=48):
    for label in labels:
        w = int(draw.textlength(label, font=fnt)) + pad * 2
        draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=CHIP_BG, outline=ACCENT, width=2)
        draw.text((x + pad, y + h / 2), label, font=fnt, fill=WHITE, anchor="lm")
        x += w + gap


def thumbnail(slug, title, subtitle, stack, w=1200, h=900):
    img = gradient(w, h).convert("RGBA")
    over = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(over)
    grid(d, w, h)
    d.ellipse([w - 420, -200, w + 200, 420], fill=(34, 211, 238, 28))
    img = Image.alpha_composite(img, over)
    d = ImageDraw.Draw(img)
    m = 80
    d.text((m, 80), "DHEERAJ KUMAR · AI ENGINEER", font=font(26, True), fill=ACCENT)
    d.rectangle([m, 130, m + 90, 136], fill=ACCENT)
    y = 250
    for line in wrap(d, title, font(78, True), w - 2 * m):
        d.text((m, y), line, font=font(78, True), fill=WHITE)
        y += 96
    y += 20
    for line in wrap(d, subtitle, font(36), w - 2 * m):
        d.text((m, y), line, font=font(36), fill=MUTED)
        y += 50
    chips(d, m, h - 150, stack, font(28, True))
    img.convert("RGB").save(OUT / f"{slug}.png", optimize=True)


def cover(w=1920, h=480):
    img = gradient(w, h).convert("RGBA")
    over = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(over)
    grid(d, w, h)
    d.ellipse([w - 520, -260, w + 160, 420], fill=(34, 211, 238, 30))
    img = Image.alpha_composite(img, over)
    d = ImageDraw.Draw(img)
    x = 560  # leave room for the profile photo on the left
    d.text((x, 110), "AI systems that work in production", font=font(64, True), fill=WHITE)
    d.text((x, 200), "RAG Chatbots  ·  AI Agents  ·  WhatsApp AI  ·  Computer Vision", font=font(36), fill=ACCENT)
    chips(d, x, 300, ["Python", "FastAPI", "LangGraph", "OpenAI / Gemini / Claude", "YOLO", "Docker"], font(26, True),
          h=46)
    img.convert("RGB").save(OUT / "00-cover-banner.png", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cover()
    for it in ITEMS:
        thumbnail(*it)
    print(f"Saved {len(ITEMS) + 1} images to {OUT}")
