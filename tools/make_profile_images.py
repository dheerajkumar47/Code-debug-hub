"""Build the Freelancer portfolio pack from tools/portfolio_items.py:

  • profile/images/00-cover-banner.png           profile cover
  • profile/images/NN-slug.png                   portfolio cover card   (1600 × 1200)
  • profile/images/NN-slug-how-it-works.png      architecture flow card (1600 × 1200)
  • docs/06-PORTFOLIO-ITEMS.md                   copy-paste text for each form field

Fails loudly if any title > 36 chars or description > 2000 chars (Freelancer form limits).

    pip install pillow && python tools/make_profile_images.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from portfolio_items import ITEMS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "profile" / "images"
DOC = ROOT / "docs" / "06-PORTFOLIO-ITEMS.md"
TITLE_MAX, DESC_MAX = 36, 2000
W, H = 1600, 1200
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts"]

BG_TOP, BG_BOTTOM = (9, 20, 44), (18, 52, 96)
ACCENT = (34, 211, 238)
WHITE, MUTED = (245, 248, 252), (165, 185, 210)
CHIP_BG, BOX_BG = (30, 64, 110), (20, 44, 80)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"] if bold else \
        ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    for d in FONT_DIRS:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def background(w: int, h: int, orb=True) -> Image.Image:
    # Vertical gradient (fast: draw lines), subtle grid, soft accent orb.
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM)))
    img = img.convert("RGBA")
    over = Image.new("RGBA", (w, h))
    o = ImageDraw.Draw(over)
    for x in range(0, w, 50):
        o.line([(x, 0), (x, h)], fill=(255, 255, 255, 10))
    for y in range(0, h, 50):
        o.line([(0, y), (w, y)], fill=(255, 255, 255, 10))
    if orb:
        o.ellipse([w - int(w * 0.36), -int(h * 0.22), w + int(w * 0.14), int(h * 0.42)], fill=(34, 211, 238, 28))
    return Image.alpha_composite(img, over)


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


def chips(draw, x, y, labels, fnt, pad=20, gap=14, h=60):
    for label in labels:
        w = int(draw.textlength(label, font=fnt)) + pad * 2
        draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=CHIP_BG, outline=ACCENT, width=2)
        draw.text((x + pad, y + h / 2), label, font=fnt, fill=WHITE, anchor="lm")
        x += w + gap


def header(d, m=100):
    d.text((m, 96), "DHEERAJ KUMAR · AI ENGINEER", font=font(32, True), fill=ACCENT)
    d.rectangle([m, 150, m + 110, 157], fill=ACCENT)


def cover_card(it):
    img = background(W, H)
    d = ImageDraw.Draw(img)
    m = 100
    header(d, m)
    y = 340
    for line in wrap(d, it["card_title"], font(100, True), W - 2 * m):
        d.text((m, y), line, font=font(100, True), fill=WHITE)
        y += 122
    y += 30
    for line in wrap(d, it["card_sub"], font(46), W - 2 * m):
        d.text((m, y), line, font=font(46), fill=MUTED)
        y += 64
    chips(d, m, H - 190, it["chips"], font(36, True), h=72)
    img.convert("RGB").save(OUT / f"{it['slug']}.png", optimize=True)


def flow_card(it):
    img = background(W, H, orb=False)
    d = ImageDraw.Draw(img)
    m = 100
    header(d, m)
    d.text((m, 190), f"How it works — {it['card_title']}", font=font(48, True), fill=WHITE)
    steps = it["flow"]
    top, bottom = 300, H - 70
    gap = 30
    box_h = min(135, (bottom - top - gap * (len(steps) - 1)) // len(steps))
    x0, x1 = m, W - m
    for i, (title, caption) in enumerate(steps):
        y0 = top + i * (box_h + gap)
        d.rounded_rectangle([x0, y0, x1, y0 + box_h], radius=18, fill=BOX_BG, outline=(60, 110, 160), width=2)
        # number badge
        cx, cy, r = x0 + 60, y0 + box_h // 2, 32
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
        d.text((cx, cy), str(i + 1), font=font(34, True), fill=BG_TOP, anchor="mm")
        d.text((x0 + 120, y0 + box_h * 0.32), title, font=font(38, True), fill=WHITE, anchor="lm")
        d.text((x0 + 120, y0 + box_h * 0.70), caption, font=font(30), fill=MUTED, anchor="lm")
        if i < len(steps) - 1:  # arrow to next box
            ax, ay = cx, y0 + box_h
            d.line([(ax, ay + 2), (ax, ay + gap - 4)], fill=ACCENT, width=4)
            d.polygon([(ax - 9, ay + gap - 12), (ax + 9, ay + gap - 12), (ax, ay + gap - 1)], fill=ACCENT)
    img.convert("RGB").save(OUT / f"{it['slug']}-how-it-works.png", optimize=True)


def cover_banner(w=1920, h=480):
    img = background(w, h)
    d = ImageDraw.Draw(img)
    x = 560  # room for the profile photo on the left
    d.text((x, 110), "AI systems that work in production", font=font(64, True), fill=WHITE)
    d.text((x, 200), "RAG Chatbots  ·  AI Agents  ·  WhatsApp AI  ·  Computer Vision", font=font(36), fill=ACCENT)
    chips(d, x, 300, ["Python", "FastAPI", "LangGraph", "OpenAI / Gemini / Claude", "YOLO", "Docker"],
          font(26, True), pad=16, gap=12, h=46)
    img.convert("RGB").save(OUT / "00-cover-banner.png", optimize=True)


def validate():
    errors = []
    for it in ITEMS:
        if len(it["title"]) > TITLE_MAX:
            errors.append(f"{it['slug']}: title {len(it['title'])} > {TITLE_MAX}")
        if len(it["description"]) > DESC_MAX:
            errors.append(f"{it['slug']}: description {len(it['description'])} > {DESC_MAX}")
    if errors:
        raise SystemExit("Form limits exceeded:\n" + "\n".join(errors))


def write_doc():
    out = ["# Portfolio Items: Ready for Freelancer's \"Create a portfolio item\" Form",
           "",
           "Generated by `tools/make_profile_images.py` from `tools/portfolio_items.py`. "
           f"Every title is **≤ {TITLE_MAX} characters** and every description is **≤ {DESC_MAX}**, "
           "so they fit the form exactly.",
           "",
           "**How to add each item:** Portfolio → *Create a portfolio item* →",
           "1. **Upload files:** upload **both** images (cover first, then the *how-it-works* diagram). "
           "Both are 1600 × 1200, the size Freelancer recommends. If you have a screen recording (MP4), add it too.",
           "2. **Title** → **Describe the work** → **Tags** → **Tools and software** → **Skills** → **Industry**. "
           "Copy each field from the boxes below.",
           "3. **Link a project on Freelancer?** Leave it empty for now (use it later for work you win on Freelancer).",
           "4. The form has no link field, so the GitHub or live link is already **inside the description**.",
           "",
           "Add them in the order below; the newest item shows first, so start with **8** and finish with **1** "
           "if you want **1** on top.",
           ""]
    for n, it in enumerate(ITEMS, 1):
        out += [
            "---",
            f"## {n}. {it['title']}",
            f"**Files to upload:** `profile/images/{it['slug']}.png` + `profile/images/{it['slug']}-how-it-works.png`",
            "",
            f"**Title** ({len(it['title'])}/{TITLE_MAX})",
            "```", it["title"], "```",
            f"**Describe the work you completed** ({len(it['description'])}/{DESC_MAX})",
            "```", it["description"], "```",
            "**Tags** (type each, press Enter)",
            "```", ", ".join(it["tags"]), "```",
            "**Tools and software**",
            "```", ", ".join(it["tools"]), "```",
            "**Skills**",
            "```", ", ".join(it["skills"]), "```",
            "**Industry**",
            "```", it["industry"], "```",
            "",
        ]
    DOC.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    validate()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("0[1-9]-*.png"):
        old.unlink()
    cover_banner()
    for it in ITEMS:
        cover_card(it)
        flow_card(it)
    write_doc()
    print(f"OK: {len(ITEMS)} items, {len(ITEMS) * 2 + 1} images → {OUT}, doc → {DOC}")
