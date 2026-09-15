#!/usr/bin/env python3
"""
Local dev static file server for the Amahirwe frontend.

Plain `python3 -m http.server` sends no cache-control headers at all, so
browsers (and especially editor-embedded preview browsers like VS Code's
Simple Browser) are free to guess a caching policy — which in practice
means edited CSS/JS/HTML can keep showing the old version until a forceful
hard refresh, or sometimes not even then. This server explicitly tells
every response "never cache this", so a normal reload always shows
whatever is currently on disk.

Usage (from the project root):
    python3 dev-server.py [port]   # defaults to 5500
"""

import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
    server = HTTPServer(("127.0.0.1", port), NoCacheHandler)
    print(f"Serving with no-cache headers on http://127.0.0.1:{port}/ (Ctrl+C to stop)")
    server.serve_forever()
