#!/usr/bin/env python3
"""Build the theme from palette.json.

  build.py           validate, print derived colours, write build/
  build.py --zip     ...and package dist/<id>-<version>.zip (whitelisted files only)
  build.py --check   validate and print only

Chrome writes "Cached Theme.pak" into any unpacked theme folder it loads, so
build/ is recreated from scratch every time and the zip never globs the folder.
"""
import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import art  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"
LOCALES = ("en", "zh_TW")

# Colour keys Chrome's BrowserThemePack recognises (chrome/browser/themes/browser_theme_pack.cc).
ALLOWED = {
    "frame", "frame_inactive", "frame_incognito", "frame_incognito_inactive",
    "background_tab", "background_tab_inactive", "background_tab_incognito",
    "background_tab_incognito_inactive", "toolbar", "toolbar_text", "toolbar_button_icon",
    "tab_text", "tab_background_text", "tab_background_text_inactive",
    "tab_background_text_incognito", "tab_background_text_incognito_inactive",
    "bookmark_text", "omnibox_background", "omnibox_text", "ntp_background", "ntp_text",
    "ntp_link", "ntp_header", "button_background",
}
# Everything the vertical strip (or light/dark fallbacks) can pick up is set explicitly.
REQUIRED = [
    "frame", "frame_inactive", "background_tab", "background_tab_inactive", "toolbar",
    "tab_text", "tab_background_text", "tab_background_text_inactive", "toolbar_text",
    "bookmark_text", "omnibox_text", "ntp_text", "toolbar_button_icon",
    "omnibox_background", "ntp_background", "ntp_link",
]
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
VERSION = re.compile(r"^\d+(\.\d+){0,3}$")

# tab_strip_color_mixer.cc: hover / selected / selected+hover blend toolbar over the inactive fill.
BLENDS = {"hover": 0.4, "multi-select": 0.75, "multi-select + hover": 0.85}
# chrome_color_mixer.cc picks the dark tab-group palette below this luminance.
GROUP_DARK_THRESHOLD = 0.211692


def rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def hexs(c):
    return "#%02X%02X%02X" % tuple(c)


def blend(fg, bg, alpha):
    """color_utils::AlphaBlend with a float alpha, rounded half away from zero."""
    return [int(f * alpha + b * (1 - alpha) + 0.5) for f, b in zip(fg, bg)]


def luminance(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validate(p):
    errors, warnings = [], []
    if not VERSION.match(p["version"]) or any(int(x) > 65535 for x in p["version"].split(".")):
        errors.append(f"bad version {p['version']!r}")
    for loc in LOCALES:
        name, summary = p["name"].get(loc, ""), p["summary"].get(loc, "")
        if not name or len(name) > 75:
            errors.append(f"name[{loc}] must be 1-75 chars (got {len(name)})")
        if not summary or len(summary) > 132:
            errors.append(f"summary[{loc}] must be 1-132 chars (got {len(summary)})")
    colors = p["colors"]
    for k, v in colors.items():
        if k not in ALLOWED:
            errors.append(f"unknown colour key {k!r}")
        if not isinstance(v, str) or not HEX.match(v):
            errors.append(f"{k}: {v!r} is not #RRGGBB")
    missing = [k for k in REQUIRED if k not in colors]
    if missing:
        errors.append(f"missing colour keys: {', '.join(missing)}")
    if errors:
        return errors, warnings
    c = {k: v.upper() for k, v in colors.items()}
    if c["background_tab"] != c["frame"]:
        errors.append("background_tab must equal frame (inactive tabs are always filled)")
    if c["background_tab_inactive"] != c["frame_inactive"]:
        errors.append("background_tab_inactive must equal frame_inactive")
    marker = p.get("marker")
    if marker:
        if not HEX.match(marker.get("color", "")):
            errors.append("marker.color must be #RRGGBB")
        if contrast(rgb(marker["color"]), rgb(c["toolbar"])) < 1.8:
            warnings.append("marker colour is hard to see against the tab background")
    elif contrast(rgb(c["toolbar"]), rgb(c["background_tab"])) < 1.2:
        warnings.append("toolbar is very close to the sidebar colour: the active tab and separators will be hard to see")
    for fg, bg in (("tab_text", "toolbar"), ("tab_background_text", "background_tab"),
                   ("omnibox_text", "omnibox_background")):
        if contrast(rgb(c[fg]), rgb(c[bg])) < 4.5:
            warnings.append(f"{fg} on {bg} is below 4.5:1")
    return errors, warnings


def report(p):
    c = {k: rgb(v) for k, v in p["colors"].items()}
    toolbar, inactive = c["toolbar"], c["background_tab"]
    print("derived tab states (vertical strip):")
    print(f"  {'sidebar / inactive tab':24s} {hexs(inactive)}")
    print(f"  {'active tab (= toolbar)':24s} {hexs(toolbar)}   vs sidebar {contrast(toolbar, inactive):.2f}:1")
    for label, a in BLENDS.items():
        col = blend(toolbar, inactive, a)
        print(f"  {label:24s} {hexs(col)}   title {contrast(c['tab_background_text'], col):.1f}:1")
    print("contrast:")
    for fg, bg in (("tab_text", "toolbar"), ("tab_background_text", "background_tab"),
                   ("toolbar_button_icon", "toolbar"), ("bookmark_text", "toolbar"),
                   ("omnibox_text", "omnibox_background"), ("omnibox_background", "toolbar")):
        print(f"  {fg + ' on ' + bg:40s} {contrast(c[fg], c[bg]):5.2f}:1")
    if p.get("marker"):
        m = p["marker"]
        print(f"active-tab marker: {m['color']} capsule, image x {m['x']} y {m['y']} (device px), "
              f"{contrast(rgb(m['color']), toolbar):.2f}:1 against the tab")
    dark = luminance(inactive) < GROUP_DARK_THRESHOLD
    print(f"tab-group chips: Chrome's {'dark (pastel)' if dark else 'light (saturated)'} palette")


def write_build(p):
    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "icons").mkdir(parents=True)
    theme = {"colors": {k: rgb(v) for k, v in p["colors"].items()}}
    if p.get("marker"):
        (BUILD / "images").mkdir()
        art.marker_image(p).save(BUILD / "images" / "toolbar.png", optimize=True)
        # Plain path: the {"100_percent": ...} form did not load in Chrome 153.
        theme["images"] = {"theme_toolbar": "images/toolbar.png"}
    manifest = {
        "manifest_version": 3,
        "name": "__MSG_extName__",
        "version": p["version"],
        "description": "__MSG_extDesc__",
        "default_locale": "en",
        "icons": {str(n): f"icons/icon-{n}.png" for n in (16, 48, 128)},
        "theme": theme,
    }
    text = re.sub(r"\[\s+(\d+),\s+(\d+),\s+(\d+)\s+\]", r"[\1, \2, \3]", json.dumps(manifest, indent=2))
    (BUILD / "manifest.json").write_text(text + "\n", encoding="utf-8")
    for loc in LOCALES:
        d = BUILD / "_locales" / loc
        d.mkdir(parents=True)
        messages = {
            "extName": {"message": p["name"][loc], "description": "Theme name"},
            "extDesc": {"message": p["summary"][loc], "description": "Theme summary"},
        }
        (d / "messages.json").write_text(json.dumps(messages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for n, path in art.render_icons(p, BUILD / "icons").items():
        with Image.open(path) as im:
            assert im.size == (n, n) and im.mode == "RGBA", (path, im.size, im.mode)
    print(f"wrote {BUILD}")


def package(p):
    files = [BUILD / "manifest.json"]
    files += sorted((BUILD / "_locales").glob("*/messages.json"))
    files += sorted((BUILD / "icons").glob("icon-*.png"))
    files += sorted((BUILD / "images").glob("*.png"))
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{p['id']}-{p['version']}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            info = zipfile.ZipInfo(f.relative_to(BUILD).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, f.read_bytes())
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        json.loads(z.read("manifest.json"))
    print(f"packaged {out} ({out.stat().st_size} bytes): {', '.join(names)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    p = json.loads((ROOT / "palette.json").read_text(encoding="utf-8"))
    errors, warnings = validate(p)
    for w in warnings:
        print(f"warning: {w}")
    if errors:
        for e in errors:
            print(f"error: {e}")
        sys.exit(1)
    report(p)
    if args.check:
        return
    write_build(p)
    if args.zip:
        package(p)


if __name__ == "__main__":
    main()
