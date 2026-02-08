#!/usr/bin/env python3
"""Unified backtest launcher."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.common.compat import ensure_legacy_root_gamma
from app.config.runtime import load_dotenv


def list_backtests(root: Path) -> list[str]:
    return sorted(path.name for path in root.glob("backtest_*.py"))


def resolve_target(root: Path, name: str) -> Path:
    target = root / name
    if target.suffix != ".py":
        target = target.with_suffix(".py")
    if target.exists():
        return target
    prefixed = root / f"backtest_{name}"
    if prefixed.suffix != ".py":
        prefixed = prefixed.with_suffix(".py")
    if prefixed.exists():
        return prefixed
    raise FileNotFoundError(name)


def main() -> int:
    load_dotenv()
    root = Path(__file__).resolve().parent
    ensure_legacy_root_gamma(root)

    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        print("Usage: python run_backtest.py <name> [args...]")
        print("Examples:")
        print("  python run_backtest.py backtest_spx.py")
        print("  python run_backtest.py spx")
        print("\nAvailable scripts:")
        for name in list_backtests(root):
            print(f"  - {name}")
        return 0

    try:
        target = resolve_target(root, sys.argv[1])
    except FileNotFoundError:
        print(f"Backtest not found: {sys.argv[1]}")
        return 1

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.call([sys.executable, str(target), *sys.argv[2:]], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
