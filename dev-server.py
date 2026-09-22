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

Usage (from anywhere):
    python3 dev-server.py [port]   # defaults to 5500

Always serves frontend/ as the web root (see the os.chdir() below),
regardless of which directory you run it from — so a page like
frontend/student/dashboard.html is reachable at /student/dashboard.html,
matching exactly how vercel.json serves the same file in production
(its rewrite to /frontend/$1 happens server-side and is invisible to
the browser, so the URL never actually contains "/frontend/" either).
Frontend code (see pathToRoot() in js/auth.js) depends on this — if
dev-server.py is ever run with frontend/'s *parent* as the web root
instead, every page it serves would sit one directory level deeper
than production, and cross-page redirects (login, logout, dashboard
links) would 404 in dev without failing in prod, or vice versa.
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5500
    server = HTTPServer(("127.0.0.1", port), NoCacheHandler)
    print(f"Serving {FRONTEND_DIR} with no-cache headers on http://127.0.0.1:{port}/ (Ctrl+C to stop)")
    server.serve_forever()
