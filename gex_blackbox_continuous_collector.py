#!/usr/bin/env python3
"""
GEX BlackBox Continuous Collector - Collect every 30 seconds during market hours.

Cross-platform version:
- Uses repository paths (no /root or /var/log)
- Uses current Python interpreter for subprocess calls
"""

import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import time
from datetime import datetime, time as dt_time

import pytz

from app.common.paths import LOGS_DIR, PROJECT_ROOT
from app.config.runtime import load_dotenv

load_dotenv()

# Market hours in ET
MARKET_OPEN = dt_time(9, 30)   # 9:30 AM ET
MARKET_CLOSE = dt_time(16, 0)  # 4:00 PM ET
ET = pytz.timezone('America/New_York')

COLLECTION_INTERVAL = 30  # seconds
LOG_FILE = LOGS_DIR / 'gex_blackbox_collector.log'


def append_log(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{now}] {message}\n")


def is_market_open() -> bool:
    """Check if market is currently open."""
    now_et = datetime.now(ET)

    # Check if it's a trading day (Mon-Fri)
    if now_et.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Check if it's within market hours
    current_time = now_et.time()
    return MARKET_OPEN <= current_time < MARKET_CLOSE


def collect_snapshot(index_symbol: str) -> bool:
    """Collect a single snapshot."""
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'gex_blackbox_recorder.py'), index_symbol],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            if 'Snapshot saved' in result.stdout:
                append_log(f"{index_symbol} collection successful")
                return True
            append_log(f"{index_symbol} returned success but no snapshot marker")
            return True

        append_log(f"{index_symbol} collection failed (exit {result.returncode})")
        return False

    except subprocess.TimeoutExpired:
        append_log(f"{index_symbol} collection timeout")
        return False
    except Exception as e:
        append_log(f"{index_symbol} collection error: {e}")
        return False


def main(index_symbol: str) -> None:
    """Main loop - collect every 30 seconds during market hours."""

    if index_symbol.upper() not in ['SPX', 'NDX']:
        print(f"Invalid index symbol: {index_symbol}")
        print("Must be SPX or NDX")
        sys.exit(1)

    index_symbol = index_symbol.upper()

    print(f"GEX BlackBox Continuous Collector - {index_symbol}")
    print(f"Collection interval: {COLLECTION_INTERVAL} seconds")
    print(f"Market hours: {MARKET_OPEN.strftime('%H:%M')} - {MARKET_CLOSE.strftime('%H:%M')} ET (Mon-Fri)")
    print("Starting collection loop...")

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting {index_symbol} collector\n")
        f.write(f"{'='*70}\n")

    collection_count = 0
    error_count = 0
    last_market_status = None

    try:
        while True:
            market_open = is_market_open()

            if market_open != last_market_status:
                status_str = "OPEN" if market_open else "CLOSED"
                append_log(f"Market status: {status_str}")
                last_market_status = market_open

            if market_open:
                if collect_snapshot(index_symbol):
                    collection_count += 1
                else:
                    error_count += 1

            time.sleep(COLLECTION_INTERVAL)

    except KeyboardInterrupt:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Collector stopped (SIGINT)\n")
            f.write(f"Total collections: {collection_count}, Errors: {error_count}\n")
        print(f"\nCollector stopped. Total: {collection_count}, Errors: {error_count}")
        sys.exit(0)
    except Exception as e:
        append_log(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python gex_blackbox_continuous_collector.py <SPX|NDX>")
        sys.exit(1)

    main(sys.argv[1])

