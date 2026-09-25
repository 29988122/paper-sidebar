#!/usr/bin/env python3
"""Screenshot helpers. Coordinates are in pixels of the raw 2x capture.

  shots.py sample <png> <x0,y0,x1,y1> [...]     most common sRGB colours per box
  shots.py store <png>... --out DIR             -> 1280x800 RGB PNGs for the Web Store
  shots.py compare <before.png> <after.png>     -> 1280x800 before/after tile
  shots.py check                                verify store asset sizes
"""
import argparse
import io
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent


def load_srgb(path):
    """Open a capture and convert it from the embedded display profile to sRGB (keeps alpha)."""
    im = Image.open(path)
    icc = im.info.get("icc_profile")
    rgba = im.convert("RGBA")
    if not icc:
        return rgba
    src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
    rgb = ImageCms.profileToProfile(rgba.convert("RGB"), src, ImageCms.createProfile("sRGB"),
                                    renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode="RGB")
    rgb.putalpha(rgba.getchannel("A"))
    return rgb


def hexs(c):
    return "#%02X%02X%02X" % tuple(c[:3])


def census(im, box, n=4):
    cnt = Counter(p[:3] for p in im.crop(box).get_flattened_data() if p[3] == 255)
    total = sum(cnt.values()) or 1
    return [(hexs(c), v * 100 / total) for c, v in cnt.most_common(n)]


def fill_corners(im):
    """Replace the transparent rounded window corners with the colour next to them."""
    w, h = im.size
    r = max(24, w // 60)
    out = im.copy()
    for x0, y0 in ((0, 0), (w - r, 0), (0, h - r), (w - r, h - r)):
        box = (x0, y0, x0 + r, y0 + r)
        solid = Counter(p[:3] for p in im.crop(box).get_flattened_data() if p[3] == 255)
        colour = solid.most_common(1)[0][0] if solid else (255, 255, 255)
        patch = Image.new("RGBA", (r, r), colour + (255,))
        patch.alpha_composite(im.crop(box))
        out.paste(patch, box[:2])
    return out.convert("RGB")


def to_store(path, out_dir):
    im = fill_corners(load_srgb(path))
    w, h = im.size
    if w / h > 1.6:
        im = im.crop((0, 0, round(h * 1.6), h))
    else:
        im = im.crop((0, 0, w, round(w / 1.6)))
    out = Path(out_dir) / (Path(path).stem + ".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.resize((1280, 800), Image.LANCZOS).save(out, optimize=True)
    return out


def compare(before, after, out, name, sidebar_px=480, height_px=1062):
    """1280x800 before/after tile: the two sidebars side by side, plus three short lines of copy."""
    from PIL import ImageDraw, ImageFilter, ImageFont

    font = lambda size, i=1: ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", size, index=i)  # noqa: E731
    W, H, s = 1280, 800, 2
    canvas = Image.new("RGB", (W * s, H * s))
    d = ImageDraw.Draw(canvas)
    for y in range(H * s):
        t = y / (H * s - 1)
        d.line([(0, y), (W * s, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip((236,) * 3, (248,) * 3)))
    pw = 300
    ph = round(pw * height_px / sidebar_px)
    for i, (path, label) in enumerate(((before, "Chrome default"), (after, name))):
        x, y = 90 + i * 380, 70 + (694 - ph) // 2
        crop = fill_corners(load_srgb(path)).crop((0, 0, sidebar_px, height_px)).resize((pw * s, ph * s), Image.LANCZOS)
        shadow = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(shadow).rounded_rectangle([x * s, (y + 6) * s, (x + pw) * s, (y + ph + 6) * s], 16 * s, fill=60)
        canvas.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(12 * s)))
        mask = Image.new("L", crop.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, crop.width - 1, crop.height - 1], 16 * s, fill=255)
        canvas.paste(crop, (x * s, y * s), mask)
        d.text(((x + pw / 2) * s, 50 * s), label, font=font(24 * s), fill="#000000", anchor="mm")
    ay = 70 + 694 // 2  # arrow between the panels (drawn: the font has no arrow glyph)
    d.line([(396 * s, ay * s), (452 * s, ay * s)], fill="#6B6B6B", width=4 * s)
    d.polygon([(460 * s, ay * s), (446 * s, (ay - 9) * s), (446 * s, (ay + 9) * s)], fill="#6B6B6B")
    for i, line in enumerate(("Soft grey tabs.", "White pages.", "Orange current tab.")):
        d.text((840 * s, (330 + i * 54) * s), line, font=font(38 * s), fill="#000000", anchor="lm")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((W, H), Image.LANCZOS).save(out, optimize=True)
    return out


def check():
    ok = True
    expect = [(ROOT / "store/icon-128.png", (128, 128), "RGBA"), (ROOT / "store/promo-440x280.png", (440, 280), "RGB")]
    expect += [(p, (1280, 800), "RGB") for p in sorted((ROOT / "store/screenshots").glob("*.png"))]
    for p, size, mode in expect:
        with Image.open(p) as im:
            good = im.size == size and im.mode == mode
        ok &= good
        print(f"{'ok ' if good else 'BAD'} {p.relative_to(ROOT)} {im.size} {im.mode}")
    shots = len(expect) - 2
    if not 1 <= shots <= 5:
        ok = False
        print(f"BAD need 1-5 screenshots, have {shots}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("png")
    s.add_argument("boxes", nargs="+")
    st = sub.add_parser("store")
    st.add_argument("pngs", nargs="+")
    st.add_argument("--out", default=str(ROOT / "store/screenshots"))
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--out", default=str(ROOT / "store/screenshots/30-before-after.png"))
    c.add_argument("--name", default="Paper Sidebar")
    sub.add_parser("check")
    a = ap.parse_args()
    if a.cmd == "sample":
        im = load_srgb(a.png)
        for b in a.boxes:
            box = tuple(int(v) for v in b.split(","))
            print(f"{b:>22}: " + ", ".join(f"{c} {pct:.0f}%" for c, pct in census(im, box)))
    elif a.cmd == "store":
        for p in a.pngs:
            print(to_store(p, a.out))
    elif a.cmd == "compare":
        print(compare(a.before, a.after, a.out, a.name))
    elif a.cmd == "check":
        sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
