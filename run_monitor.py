#!/usr/bin/env python3
"""Legacy entrypoint placeholder.

Trade monitoring has been retired in this repository build.
Use `run_dashboard.py` for the read-only information board.
"""

def main() -> int:
    print("run_monitor.py is disabled: trading monitor was removed.")
    print("Use: python run_dashboard.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
