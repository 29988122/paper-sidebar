#!/usr/bin/env python3
"""Icons and store artwork for the theme, drawn with Pillow from palette.json.

Everything is drawn large and downscaled with LANCZOS, so edges stay smooth.
The artwork is a small browser window with a white sidebar, coloured tab-group
chips and a grey active-tab row -- deliberately unlike any other product's logo.

usage: art.py icons <outdir> | art.py store | art.py all
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
REGULAR, BOLD, MEDIUM = 0, 1, 10

# Chrome's classic light tab-group colours: what the native strip draws on a white background.
GROUP = {
    "grey": "#5F6368", "blue": "#1A73E8", "red": "#D93025", "yellow": "#F9AB00",
    "green": "#188038", "pink": "#D01884", "purple": "#A142F4", "cyan": "#007B83",
    "orange": "#FA903E",
}
TRAFFIC = ("#FF5F57", "#FEBC2E", "#28C840")
OUTLINE = "#D3D3D3"      # the extension's border colour
TEXT_BAR = "#9A9A9A"


def load_palette():
    return json.loads((ROOT / "palette.json").read_text(encoding="utf-8"))


def font(size, index=REGULAR):
    return ImageFont.truetype(FONT, size, index=index)


class Canvas:
    """Draw in design units; `s` pixels per unit, `ox/oy` offset in units."""

    def __init__(self, img, s, ox=0.0, oy=0.0):
        self.img, self.s, self.ox, self.oy = img, s, ox, oy
        self.d = ImageDraw.Draw(img)

    def box(self, x0, y0, x1, y1):
        s = self.s
        return [(x0 + self.ox) * s, (y0 + self.oy) * s, (x1 + self.ox) * s - 1, (y1 + self.oy) * s - 1]

    def rect(self, b, fill, r=0):
        if r:
            self.d.rounded_rectangle(self.box(*b), radius=r * self.s, fill=fill)
        else:
            self.d.rectangle(self.box(*b), fill=fill)

    def circle(self, cx, cy, r, fill):
        self.rect((cx - r, cy - r, cx + r, cy + r), fill, r)

    def text(self, x, y, s, size, fill, index=REGULAR):
        f = font(round(size * self.s), index)
        self.d.text(((x + self.ox) * self.s, (y + self.oy) * self.s), s, font=f, fill=fill, anchor="lm")


def _window(c, colors, detail):
    """Window artwork in a 96x96 unit space."""
    toolbar, frame = colors["toolbar"], colors["frame"]
    marker = c.marker
    c.rect((0, 0, 96, 96), frame, r=16)
    # toolbar band (top-right; top corner stays rounded)
    c.rect((40, 0, 96, 20), toolbar, r=16)
    c.rect((40, 0, 80, 20), toolbar)
    c.rect((40, 10, 96, 20), toolbar)
    c.rect((46, 5, 90, 15), colors["omnibox_background"], r=5)
    c.rect((40, 19.5, 96, 20.5), OUTLINE)  # toolbar | page separator
    # sidebar | page divider
    c.rect((39.5, 0, 40.5, 96), OUTLINE)
    for i, col in enumerate(TRAFFIC):
        c.circle(9 + i * 7.5, 10, 2.8, col)

    def row(y, active=False, bar=16):
        if active:
            c.rect((4.2, y + 1.2, 6.2, y + 6.8), marker, r=1)
        if detail == "full":
            c.rect((7.5, y + 2.2, 11.3, y + 6), "#7A7A7A", r=0.8)
            c.rect((14, y + 3.3, 14 + bar, y + 4.9), "#3C3C3C" if active else TEXT_BAR, r=0.8)

    def chip(y, color, w):
        c.rect((5, y + 0.8, 5 + w, y + 7.2), GROUP[color], r=3.2)
        if detail == "full":
            c.rect((8, y + 3.3, 5 + w - 5, y + 4.8), "#FFFFFF", r=0.7)

    chip(18, "green", 22)
    row(28, active=True, bar=18)
    row(38, bar=14)
    chip(49, "cyan", 18)
    row(59, bar=17)
    row(69, bar=12)
    chip(80, "grey", 13)
    if detail == "full":
        c.rect((48, 30, 84, 32.5), "#E6E6E6", r=1)
        c.rect((48, 37, 78, 39.5), "#EDEDED", r=1)
        c.rect((48, 44, 81, 46.5), "#EDEDED", r=1)


def _outline(img, box_px, radius_px, width_px, color):
    ImageDraw.Draw(img).rounded_rectangle(box_px, radius=radius_px, outline=color, width=width_px)


def icon(size, colors, marker="#FF9500"):
    """Manifest/store icon. 128 keeps the store's 16px transparent padding."""
    scale = 16 if size <= 16 else 8
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    if size <= 16:
        c = Canvas(img, big / 16)
        c.marker = marker
        c.rect((1, 1, 15, 15), colors["frame"], r=3)
        c.rect((6, 1, 15, 5.5), colors["toolbar"], r=3)
        c.rect((6, 1, 12, 5.5), colors["toolbar"])
        c.rect((6, 3, 15, 5.5), colors["toolbar"])
        c.rect((6, 5.3, 15, 5.8), OUTLINE)
        c.rect((5.8, 1, 6.4, 15), OUTLINE)
        c.rect((2.2, 6.3, 5.2, 7.9), GROUP["green"], r=0.8)
        c.rect((1.6, 8.6, 2.6, 11.2), marker, r=0.5)
        c.rect((3.2, 9.4, 5.3, 10.4), "#8A8A8A", r=0.4)
        c.rect((2.2, 11.9, 4.8, 13.5), GROUP["cyan"], r=0.8)
        _outline(img, [c.s * 1, c.s * 1, c.s * 15 - 1, c.s * 15 - 1], 3 * c.s, round(c.s * 0.9), "#A8A8A8")
    else:
        pad = 16 if size >= 128 else size * 0.05
        unit = (size - 2 * pad) / 96 * scale
        c = Canvas(img, unit, pad * scale / unit, pad * scale / unit)
        c.marker = marker
        _window(c, colors, "full" if size >= 128 else "medium")
        o = pad * scale
        _outline(img, [o, o, big - o - 1, big - o - 1], 16 * unit, max(2, round(unit * 1.4)), OUTLINE)
    return img.resize((size, size), Image.LANCZOS)


def marker_image(palette, k=8):
    """theme_toolbar image: white, with the active-tab capsule near its top-left corner.

    Chrome tiles it from each tab's top-left at 1 image px = 1 device px, but from the
    window's left edge on the toolbar, where this corner sits behind the sidebar."""
    m = palette["marker"]
    (x0, x1), (y0, y1) = m["x"], m["y"]
    white = palette["colors"]["toolbar"]
    big = Image.new("RGB", (64 * k, 120 * k), white)
    ImageDraw.Draw(big).rounded_rectangle([x0 * k, y0 * k, x1 * k - 1, y1 * k - 1], radius=m["radius"] * k, fill=m["color"])
    img = Image.new("RGB", (3000, 120), white)
    img.paste(big.resize((64, 120), Image.LANCZOS), (0, 0))
    return img


def render_icons(palette, outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for n in (16, 48, 128):
        p = outdir / f"icon-{n}.png"
        icon(n, palette["colors"], palette["marker"]["color"]).save(p, optimize=True)
        paths[n] = p
    return paths


def _fit(text, size, index, max_w):
    while size > 8 and font(size, index).getlength(text) > max_w:
        size -= 1
    return size


def promo(palette, w=440, h=280, s=2):
    """Small promo tile (RGB, no alpha)."""
    colors = palette["colors"]
    W, H = w * s, h * s
    img = Image.new("RGB", (W, H), "#FFFFFF")
    top, bottom = (0xEC, 0xEC, 0xEC), (0xF8, 0xF8, 0xF8)
    grad = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        grad.line([(0, y), (W, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))

    wx0, wy0, wx1, wy1 = 24, 28, 244, 252
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle([wx0 * s, (wy0 + 5) * s, wx1 * s, (wy1 + 5) * s], radius=14 * s, fill=70)
    shadow = shadow.filter(ImageFilter.GaussianBlur(10 * s))
    img.paste(Image.new("RGB", (W, H), "#000000"), (0, 0), shadow)

    c = Canvas(img, s)
    sb = 88  # sidebar width
    c.rect((wx0, wy0, wx1, wy1), colors["frame"], r=14)
    c.rect((wx0 + sb, wy0, wx1, wy0 + 26), colors["toolbar"], r=14)
    c.rect((wx0 + sb, wy0, wx1 - 20, wy0 + 26), colors["toolbar"])
    c.rect((wx0 + sb, wy0 + 13, wx1, wy0 + 26), colors["toolbar"])
    c.rect((wx0 + sb + 8, wy0 + 6, wx1 - 8, wy0 + 20), colors["omnibox_background"], r=7)
    c.rect((wx0 + sb, wy0 + 25.5, wx1, wy0 + 26.5), OUTLINE)
    c.rect((wx0 + sb - 0.5, wy0, wx0 + sb + 0.5, wy1), OUTLINE)
    for i, col in enumerate(TRAFFIC):
        c.circle(wx0 + 12 + i * 10, wy0 + 13, 3.4, col)
    for i, (bw, col) in enumerate(((96, "#E3E3E3"), (80, "#EDEDED"), (104, "#EDEDED"), (70, "#EDEDED"))):
        c.rect((wx0 + sb + 16, wy0 + 44 + i * 13, wx0 + sb + 16 + bw, wy0 + 49 + i * 13), col, r=2.5)

    x0, x1 = wx0 + 5, wx0 + sb - 5
    y = wy0 + 32
    fav = ["#3C78D8", "#E06666", "#6AA84F", "#F1C232", "#8E7CC3", "#45818E", "#CC4125"]

    def row(label, active=False):
        nonlocal y
        if active:
            c.rect((x0 + 1.5, y + 4.5, x0 + 3.5, y + 12.5), palette["marker"]["color"], r=1)
        c.rect((x0 + 5, y + 5, x0 + 12, y + 12), fav[len(label) % len(fav)], r=1.6)
        c.text(x0 + 16, y + 8.7, label, 7.6, "#000000")
        y += 19

    def chip(label, color):
        nonlocal y
        tw = font(round(7.2 * s), BOLD).getlength(label) / s
        c.rect((x0 + 1, y + 2, x0 + 1 + tw + 12, y + 15), GROUP[color], r=6.5)
        c.text(x0 + 7, y + 8.7, label, 7.2, "#FFFFFF", BOLD)
        y += 19

    chip("Work", "blue")
    row("Weekly plan")
    row("Team notes", active=True)
    chip("Reading", "cyan")
    row("Long read")
    row("Recipes")
    chip("Travel", "green")
    row("Trail map")
    chip("Research", "purple")
    row("Weather")

    tx, max_w = 266, 440 - 266 - 18
    name = palette["name"]["en"].split(" ", 1)
    size = min(_fit(part, 38, BOLD, max_w) for part in name)
    for i, part in enumerate(name):
        c.text(tx, 78 + i * 40, part, size, "#000000", BOLD)
    sub = ["All-white vertical tabs,", "orange current tab"]
    ss = min(_fit(t, 15, MEDIUM, max_w) for t in sub)
    for i, t in enumerate(sub):
        c.text(tx, 160 + i * 20, t, ss, "#4D4D4D", MEDIUM)
    for i, col in enumerate(("#FFFFFF", palette["marker"]["color"], "#000000")):
        cx = tx + 11 + i * 30
        c.circle(cx, 222, 11, OUTLINE)
        c.circle(cx, 222, 10, col)
    return img.resize((w, h), Image.LANCZOS)


def render_store(palette):
    out = ROOT / "store"
    out.mkdir(parents=True, exist_ok=True)
    icon(128, palette["colors"], palette["marker"]["color"]).save(out / "icon-128.png", optimize=True)
    promo(palette).save(out / "promo-440x280.png", optimize=True)
    return out


def main(argv):
    p = load_palette()
    cmd = argv[1] if len(argv) > 1 else "all"
    if cmd in ("icons", "all"):
        target = argv[2] if cmd == "icons" and len(argv) > 2 else ROOT / "build" / "icons"
        for n, path in render_icons(p, target).items():
            print(f"icon {n:>3}: {path}")
    if cmd in ("store", "all"):
        out = render_store(p)
        print(f"store art: {out / 'icon-128.png'}, {out / 'promo-440x280.png'}")


if __name__ == "__main__":
    main(sys.argv)
