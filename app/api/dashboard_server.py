from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.services import MarketSnapshotService


class DashboardRequestHandler(BaseHTTPRequestHandler):
    service: MarketSnapshotService
    dashboard_root: Path

    server_version = "GammaDashboard/1.0"

    def _write_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _write_file(self, file_path: Path, content_type: str, status: int = HTTPStatus.OK) -> None:
        data = file_path.read_bytes()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route in {"/", "/index.html"}:
            index_file = self.dashboard_root / "index.html"
            if not index_file.exists():
                self._write_json({"error": "Dashboard page is missing."}, status=HTTPStatus.NOT_FOUND)
                return
            self._write_file(index_file, "text/html; charset=utf-8")
            return

        if route == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        if route == "/api/health":
            self._write_json(self.service.health())
            return

        if route == "/api/dashboard/snapshot":
            index_code = (query.get("index", ["SPX"])[0] or "SPX").upper()
            payload = self.service.get_snapshot(index_code)
            self._write_json(payload)
            return

        if route == "/api/dashboard/history":
            index_code = (query.get("index", ["SPX"])[0] or "SPX").upper()
            try:
                limit = int(query.get("limit", ["120"])[0])
            except (TypeError, ValueError):
                limit = 120
            payload = {
                "index": index_code,
                "items": self.service.get_history(index_code, limit=limit),
            }
            self._write_json(payload)
            return

        if route == "/api/dashboard/debug":
            index_code = (query.get("index", ["SPX"])[0] or "SPX").upper()
            payload = self.service.debug(index_code)
            self._write_json(payload)
            return

        self._write_json({"error": f"Route not found: {route}"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep server logs concise.
        return


def create_dashboard_server(
    *,
    host: str,
    port: int,
    service: MarketSnapshotService,
    dashboard_root: Path,
) -> ThreadingHTTPServer:
    class Handler(DashboardRequestHandler):
        pass

    Handler.service = service
    Handler.dashboard_root = dashboard_root
    return ThreadingHTTPServer((host, port), Handler)
