"""
Builds rounded card-style SVGs for the GitHub profile README:
  Assets/card-*.svg  - project cards (screenshot on top, tag + title + text below)
  Assets/chip-*.svg  - rounded icon tiles made from your icon PNGs

Run from the repo root:   pip install pillow   then   python make_cards.py
Missing images or icons are skipped with a message, so you can run it any time.
"""
import base64, io, textwrap
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image

A = Path("Assets")

# ---- edit these -------------------------------------------------------------
CARDS = [
    dict(out="card-emptyknock.svg", image="EK-1.jpg", fit="cover",
         tag="UNREAL ENGINE", title="Empty Knock",
         text="A cult horror game about a band, a quiet house and something at the door."),
    dict(out="card-gam.svg", image="GAM.png", fit="contain",
         tag="TYPESCRIPT · REACT", title="Game Asset Manager",
         text="A desktop tool I built to organise my own game asset library."),
    dict(out="card-youtube.svg", image="EK-3.jpg", fit="cover",
         tag="YOUTUBE", title="Watch",
         text="Videos and updates on the AbiRockGames channel."),
    dict(out="card-itch.svg", image="EK-4.jpg", fit="cover",
         tag="ITCH.IO", title="Play",
         text="Builds and extras on the AbiRockGames itch.io page."),
]
# icon PNGs expected in Assets/ (name.png -> chip-name.svg)
CHIPS = ["youtube", "itchio", "instagram", "linkedin", "unreal", "typescript", "react"]

SURFACE, BORDER = "#0d1f1f", "#1f3b3a"          # card colours (match the header)
TITLE, BODY, TAG = "#c9d6d0", "#8fa8a0", "#5f8577"
FONT = "'Segoe UI', system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, Consolas, monospace"
# -----------------------------------------------------------------------------

CW, CH, IMG_H, R = 480, 430, 250, 22


def b64(img, fmt, **kw):
    buf = io.BytesIO()
    img.save(buf, fmt, **kw)
    mime = "jpeg" if fmt == "JPEG" else "png"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def cover(img, size):
    tw, th = size
    s = max(tw / img.width, th / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    l, t = (img.width - tw) // 2, (img.height - th) // 2
    return img.crop((l, t, l + tw, t + th))


def contain(img, size, bg=(10, 20, 20)):
    tw, th = size
    s = min(tw / img.width, th / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    canvas = Image.new("RGB", size, bg)
    canvas.paste(img, ((tw - img.width) // 2, (th - img.height) // 2))
    return canvas


def card(c):
    src = A / c["image"]
    if not src.exists():
        print("skip", c["out"], "- missing", src)
        return
    im = Image.open(src).convert("RGB")
    size = (CW * 2, IMG_H * 2)
    im = cover(im, size) if c["fit"] == "cover" else contain(im, size)
    uri = b64(im, "JPEG", quality=85, optimize=True)

    lines = textwrap.wrap(c["text"], 44)[:3]
    body = "".join(
        f'<text x="28" y="{356 + i * 26}" font-family="{FONT}" font-size="17" fill="{BODY}">{escape(t)}</text>'
        for i, t in enumerate(lines))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}">
<defs><clipPath id="c"><rect width="{CW}" height="{CH}" rx="{R}"/></clipPath></defs>
<g clip-path="url(#c)">
<rect width="{CW}" height="{CH}" fill="{SURFACE}"/>
<image xlink:href="{uri}" x="0" y="0" width="{CW}" height="{IMG_H}" preserveAspectRatio="xMidYMid slice"/>
<rect y="{IMG_H}" width="{CW}" height="2" fill="{BORDER}"/>
<text x="28" y="284" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{TAG}">{escape(c["tag"])}</text>
<text x="28" y="322" font-family="{FONT}" font-size="26" font-weight="700" fill="{TITLE}">{escape(c["title"])}</text>
{body}
</g>
<rect x="1" y="1" width="{CW - 2}" height="{CH - 2}" rx="{R - 1}" fill="none" stroke="{BORDER}" stroke-width="2"/>
</svg>'''
    (A / c["out"]).write_text(svg, encoding="utf-8")
    print("wrote", A / c["out"], f"{len(svg) // 1024} KB")


def chip(name):
    src = A / f"{name}.png"
    if not src.exists():
        print("skip chip", name, "- missing", src)
        return
    icon = Image.open(src).convert("RGBA").resize((96, 96), Image.LANCZOS)
    uri = b64(icon, "PNG", optimize=True)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 96 96" width="96" height="96">
<rect x="1" y="1" width="94" height="94" rx="24" fill="{SURFACE}" stroke="{BORDER}" stroke-width="2"/>
<image xlink:href="{uri}" x="24" y="24" width="48" height="48"/>
</svg>'''
    (A / f"chip-{name}.svg").write_text(svg, encoding="utf-8")
    print("wrote", A / f"chip-{name}.svg")


if __name__ == "__main__":
    for c in CARDS:
        card(c)
    for n in CHIPS:
        chip(n)