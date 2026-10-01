"""Genera assets/icon.ico a partir de formas vectoriales simples (sin dependencias externas)."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "icon.ico"
SIZES = [16, 24, 32, 48, 64, 128, 256]

BG_TOP = (10, 11, 14, 255)
BG_BOTTOM = (22, 26, 36, 255)
ACCENT = (0, 206, 206, 255)


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    for y in range(size):
        t = y / max(1, size - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        d.line([(0, y), (size, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    radius = max(2, size // 5)
    md.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(img, mask=mask)
    img = rounded
    d = ImageDraw.Draw(img)

    cx, cy = size / 2, size / 2
    note_w = size * 0.3
    note_h = size * 0.08
    stem_h = size * 0.42

    head_x = cx - note_w * 0.35
    head_y = cy + stem_h * 0.3
    d.ellipse(
        [head_x - note_w / 2, head_y - note_h, head_x + note_w / 2, head_y + note_h],
        fill=ACCENT,
    )

    stem_w = max(1, size * 0.045)
    stem_x = head_x + note_w / 2 - stem_w / 2
    d.rectangle(
        [stem_x, head_y - stem_h, stem_x + stem_w, head_y],
        fill=ACCENT,
    )

    flag_w = size * 0.22
    d.polygon(
        [
            (stem_x + stem_w, head_y - stem_h),
            (stem_x + stem_w + flag_w, head_y - stem_h + size * 0.1),
            (stem_x + stem_w, head_y - stem_h + size * 0.22),
        ],
        fill=ACCENT,
    )

    return img


images = [render(s) for s in SIZES]
images[-1].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
print(f"Generado {OUT}")
