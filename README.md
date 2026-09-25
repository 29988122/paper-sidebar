# Paper Sidebar

**English** · [繁體中文](README.zh-TW.md)

A colors-only Chrome theme for Chrome's native **vertical tabs**: everything stays white, and the current tab gets a small orange marker next to its icon.

[![Install from the Chrome Web Store](https://img.shields.io/badge/Chrome%20Web%20Store-Install-FF9500?logo=googlechrome&logoColor=white)](https://chromewebstore.google.com/detail/paper-sidebar/fbomcfigjianejcinmaloifgaladakic)

![Paper Sidebar in Chrome's vertical tabs](store/screenshots/60-hero.png)

![Chrome default vs. Paper Sidebar](store/screenshots/30-before-after.png)

## Features

- White tab sidebar, toolbar and window frame: no grey or tinted bands.
- The current tab is marked with an orange (#FF9500) capsule, the same height as the tab icon.
- Black tab titles; other tabs stay flat.
- Tab groups keep Chrome's own group colors.
- Looks the same in macOS light and dark mode.
- No code, no permissions, no data collection.

## Install

- **Chrome Web Store:** [Paper Sidebar](https://chromewebstore.google.com/detail/paper-sidebar/fbomcfigjianejcinmaloifgaladakic). Installed this way, the theme syncs to your other computers when "Themes" sync is on.
- **From source:** run `python3 tools/build.py`, then open `chrome://extensions` → turn on Developer mode → **Load unpacked** → pick the `build/` folder. A theme loaded this way does not sync.

To show tabs on the side: right-click any tab → **Show Tabs Vertically**.
To remove the theme: Settings → Appearance → Theme → **Reset to default**.

## How it works

A Chrome theme cannot style the browser UI with CSS; it only provides colors and images. Two Chrome behaviours shape this theme:

1. **The active tab always uses the `toolbar` color.** The same color also paints the toolbar row, infobars and the frame around the page. A grey active tab therefore means a grey toolbar and a grey frame. So `toolbar` is white here, which leaves the active tab white too.
2. **The marker is an image.** Chrome paints the `theme_toolbar` image in two places. On a tab it starts at the tab's own top-left corner, at 1 image pixel per device pixel. On the toolbar it starts at the window's left edge. A small capsule in the image's top-left corner therefore appears on the active tab, and on the toolbar that part of the image sits behind the sidebar.

Colors and the marker's size and position live in [`palette.json`](palette.json). Marker coordinates are device pixels on a 2× (Retina) display, where a tab is 60 px tall and its icon spans y 14–45.

## Limitations

- A hovered tab also shows the marker while the mouse is over it (Chrome paints the same image for hover).
- The marker is sized for Retina displays; on a 1× monitor it looks about twice as large.
- The marker relies on how Chrome currently paints theme images and may move if Chrome changes that.
- Tab-group colors, fonts, row height and the sidebar edge line are drawn by Chrome and can't be themed.
- Themes don't apply to Incognito windows. Picking a color in "Customize Chrome" replaces the theme.

## Development

Requires Python 3 with Pillow, and Node.js 22+ for the visual test harness.

```bash
python3 tools/build.py            # validate palette.json, print derived colors, write build/
python3 tools/build.py --zip      # also package dist/paper-sidebar-<version>.zip (whitelisted files only)
python3 tools/art.py store        # store icon and 440×280 promo tile
python3 tools/shots.py check      # verify store asset sizes
```

The visual test harness opens a separate, throwaway Chrome profile and never touches your own. The window is not headless, because headless Chrome has no tab strip to look at. The harness drives that Chrome over the DevTools Protocol (`Extensions.loadUnpacked`, plus a small helper extension that builds tab groups) and captures the window with `screencapture`. Capturing needs macOS Screen Recording permission.

```bash
export VT_UDD=/tmp/vt-udd                       # throwaway profile directory
harness/run.sh                                  # launch the test Chrome
node harness/cdp.mjs load build                 # install the theme
node harness/cdp.mjs layout harness/layouts/store.json   # (store.json expects: python3 harness/site.py harness/layouts/store.json)
node harness/cdp.mjs shot shots/test.png --when-front
python3 tools/shots.py sample shots/test.png 24,1155,438,1459   # sRGB color census of a region
harness/stop.sh --wipe
```

| Path | What it is |
|---|---|
| `palette.json` | Single source of truth: name, version, colors, marker |
| `tools/build.py` | Builds and validates the theme, packages the zip |
| `tools/art.py` | Icons, promo tile and the marker image |
| `tools/shots.py` | Screenshot color sampling and store-size export |
| `harness/` | Throwaway-Chrome test harness (CDP, helper extension, layouts) |
| `store/` | Store listing text and images |

## License

[MIT](LICENSE)
