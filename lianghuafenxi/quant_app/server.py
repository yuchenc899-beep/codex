import argparse
import json
import sqlite3
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .ledger import import_archive, read_archive

ROOT = Path(__file__).resolve().parents[1]
UI = Path(__file__).resolve().parent / "ui"
ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css")}


class Dashboard(BaseHTTPRequestHandler):
    def __init__(self, *args, database, **kwargs):
        self.database = database
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == "/api/archive":
            with sqlite3.connect(self.database) as db:
                payload = json.dumps(read_archive(db), ensure_ascii=False).encode("utf-8")
            content_type = "application/json"
        elif path in ASSETS:
            filename, content_type = ASSETS[path]
            payload = (UI / filename).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--archive", type=Path, default=ROOT / "自选与持仓清单_2026-11-11.md")
    parser.add_argument("--database", type=Path, default=ROOT / "private" / "quant.sqlite3")
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as db:
        import_archive(db, args.archive)
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(Dashboard, database=args.database)) as server:
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
