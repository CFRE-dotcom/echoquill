"""Generate icon.ico - white background, blue EQ, version badge top-right.
Runs automatically before each build, so the icon always shows the
current version from echoquill/__init__.py.
"""

import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUE = (10, 132, 255, 255)
LIGHT_BLUE = (10, 132, 255, 255)


def version() -> str:
    init = open(os.path.join(ROOT, "echoquill", "__init__.py"), encoding="utf-8").read()
    m = re.search(r'__version__ = "(\d+)\.(\d+)', init)
    return f"v{m.group(1)}.{m.group(2)}" if m else "v1"


def font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "arial.ttf",
                 "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_icon(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size // 5
    d.rounded_rectangle([4, 4, size - 4, size - 4], radius=r,
                        fill=(255, 255, 255, 255), outline=BLUE, width=max(2, size // 64))
    # EQ letters
    f = font(int(size * 0.46))
    d.text((size * 0.5, size * 0.56), "EQ", font=f, fill=BLUE, anchor="mm")
    # version badge, top-right
    v = version()
    bf = font(int(size * 0.14))
    bbox = d.textbbox((0, 0), v, font=bf)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = size * 0.03
    x2, y1 = size - size * 0.06, size * 0.06
    d.rounded_rectangle([x2 - tw - 2 * pad, y1, x2, y1 + th + 2 * pad],
                        radius=(th + 2 * pad) / 2, fill=LIGHT_BLUE)
    d.text((x2 - pad - tw / 2, y1 + pad + th / 2), v, font=bf,
           fill=(255, 255, 255, 255), anchor="mm")
    return img


def full_version() -> str:
    init = open(os.path.join(ROOT, "echoquill", "__init__.py"), encoding="utf-8").read()
    m = re.search(r'__version__ = "([\d.]+)"', init)
    return m.group(1) if m else "1.0"


def main():
    base = draw_icon(256)
    out = os.path.join(ROOT, "icon.ico")
    base.save(out, sizes=[(256, 256), (128, 128), (64, 64),
                          (48, 48), (32, 32), (16, 16)])
    with open(os.path.join(ROOT, "version.txt"), "w") as f:
        f.write(full_version())
    print(f"icon.ico written ({version()})")


if __name__ == "__main__":
    main()
