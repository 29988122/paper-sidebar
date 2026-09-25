#!/usr/bin/env python3
"""Tiny local site for store screenshots: http://localhost:<port>/<slug> renders a made-up page.

usage: site.py <layout.json> [port]    (slugs come from tab titles, e.g. "Team notes" -> /team-notes)
Serving over localhost keeps the omnibox clean (no "Not Secure" chip, no data: URL).
"""
import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

DEFAULT_BODY = [
    "This is a placeholder page used to preview the theme. It has a title, a favicon and a little text so the tab looks real.",
    "Nothing here comes from a real browsing session.",
]


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def favicon(letter, color):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="{color}"/>'
           f'<text x="16" y="22.5" font-family="Helvetica, Arial, sans-serif" font-size="18" font-weight="700" '
           f'text-anchor="middle" fill="#fff">{html.escape(letter)}</text></svg>')
    return "data:image/svg+xml," + quote(svg)


def render(tab):
    title = html.escape(tab["title"])
    paras = "".join(f"<p>{html.escape(p)}</p>" for p in tab.get("body", DEFAULT_BODY))
    return (f'<!doctype html><meta charset="utf-8"><title>{title}</title>'
            f'<link rel="icon" href="{favicon(tab.get("letter", tab["title"][0]), tab.get("icon", "#5F6368"))}">'
            '<style>body{font:16px/1.6 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;color:#1f1f1f;margin:0;background:#fff}'
            'main{max-width:640px;margin:56px auto;padding:0 32px}h1{font-size:30px;line-height:1.25;margin:0 0 18px}p{color:#3c3c3c}'
            '.bar{height:10px;border-radius:5px;background:#ececec;margin:14px 0}</style>'
            f'<main><h1>{title}</h1>{paras}<div class="bar" style="width:92%"></div>'
            '<div class="bar" style="width:84%"></div><div class="bar" style="width:66%"></div></main>')


def main():
    layout = json.load(open(sys.argv[1], encoding="utf-8"))
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    pages = {}
    for item in layout["items"]:
        for tab in item.get("tabs", [item]):
            if "title" in tab and "url" not in tab:
                pages["/" + slug(tab["title"])] = render(tab).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = pages.get(self.path.split("?")[0])
            self.send_response(200 if body else 404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body or b"not found")

        def log_message(self, *args):
            pass

    print(f"serving {len(pages)} pages on http://localhost:{port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
