#!/usr/bin/env python3
"""Run the local Schwab-powered information dashboard."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.api import create_dashboard_server
from app.common.compat import ensure_legacy_root_gamma
from app.config.runtime import load_dotenv
from app.providers import SchwabClient, SchwabClientError
from app.services import MarketSnapshotService


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def parse_args() -> argparse.Namespace:
    default_host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    default_port = int(os.getenv("DASHBOARD_PORT", "8787"))
    default_refresh = int(os.getenv("DASHBOARD_REFRESH_SECONDS", "12"))
    parser = argparse.ArgumentParser(description="Gamma read-only dashboard server (Schwab)")
    parser.add_argument("--host", default=default_host, help=f"Bind host (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Bind port (default: {default_port})")
    parser.add_argument(
        "--refresh-seconds",
        type=int,
        default=default_refresh,
        help=f"Snapshot refresh cadence in seconds (default: {default_refresh})",
    )
    parser.add_argument(
        "--warmup-index",
        default="SPX",
        choices=["SPX", "NDX"],
        help="Index code to preload on startup.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    root = Path(__file__).resolve().parent
    ensure_legacy_root_gamma(root)
    args = parse_args()
    strategy_fast_mode = _parse_bool_env("DASHBOARD_STRATEGY_FAST_MODE", True)

    client = SchwabClient()
    service = MarketSnapshotService(
        client=client,
        refresh_seconds=args.refresh_seconds,
        strategy_fast_mode=strategy_fast_mode,
    )

    # Warm up once so startup reveals credential/API issues early.
    try:
        service.refresh_snapshot(args.warmup_index)
    except SchwabClientError as exc:
        print(f"[WARN] Startup warmup failed: {exc}")
        print("[WARN] Dashboard will still run and keep retrying on refresh.")

    dashboard_root = root / "dashboard"
    try:
        server = create_dashboard_server(
            host=args.host,
            port=args.port,
            service=service,
            dashboard_root=dashboard_root,
        )
    except OSError as exc:
        print(f"[ERROR] Failed to bind {args.host}:{args.port} - {exc}")
        print("[ERROR] Another dashboard instance may already be running on this port.")
        return 2

    base_url = f"http://{args.host}:{args.port}/"
    print(f"Dashboard running at {base_url}")
    print(f"Strategy fast mode: {strategy_fast_mode} (set DASHBOARD_STRATEGY_FAST_MODE=0 for strict checks)")
    print("Read-only mode: no order placement code is executed.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
