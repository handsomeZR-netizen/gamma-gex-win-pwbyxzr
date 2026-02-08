#!/usr/bin/env python3
"""Read-only signal runner backed by Schwab market data."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.common.compat import ensure_legacy_root_gamma
from app.config.runtime import load_dotenv
from app.providers import SchwabClient
from app.services import MarketSnapshotService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gamma signal-only mode (Schwab). Read-only; never places orders."
    )
    parser.add_argument("index", nargs="?", default="SPX", choices=["SPX", "NDX"], help="Index code.")
    parser.add_argument("--watch", action="store_true", help="Continuously evaluate signals.")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between evaluations in watch mode.")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def _format_human(snapshot: dict) -> str:
    market = snapshot.get("market", {})
    gex = snapshot.get("gex", {})
    signals = snapshot.get("signals", {})
    options_summary = snapshot.get("options", {}).get("summary", {})

    lines = [
        f"[{snapshot.get('timestamp_local', '-')}] {snapshot.get('index', {}).get('code', 'N/A')} SIGNAL",
        f"Spot={market.get('spot')} | VIX={market.get('vix')} | Pin={gex.get('pin')} | Distance={gex.get('distance_to_pin')}",
        f"Bias={gex.get('direction_bias')} | Observation={signals.get('observation')}",
        (
            f"PCR(OI)={options_summary.get('put_call_oi_ratio')} | "
            f"PCR(Vol)={options_summary.get('put_call_volume_ratio')} | "
            f"Contracts={options_summary.get('contracts')}"
        ),
    ]
    reasons = signals.get("reasons") or []
    if reasons:
        lines.append("Reasons:")
        lines.extend([f"- {r}" for r in reasons])
    return "\n".join(lines)


def main() -> int:
    load_dotenv()
    root = Path(__file__).resolve().parent
    ensure_legacy_root_gamma(root)
    args = parse_args()

    if args.interval < 5:
        raise SystemExit("ERROR: --interval must be >= 5 seconds")

    client = SchwabClient()
    service = MarketSnapshotService(client=client, refresh_seconds=args.interval)

    print("SIGNAL MODE (Schwab): read-only evaluation. No orders will be sent.", flush=True)
    try:
        while True:
            snapshot = service.refresh_snapshot(args.index)
            if args.json_output:
                print(json.dumps(snapshot, ensure_ascii=False), flush=True)
            else:
                print(_format_human(snapshot), flush=True)
                print("-" * 90, flush=True)
            if not args.watch:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
