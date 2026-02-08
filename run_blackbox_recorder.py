#!/usr/bin/env python3
"""Windows-friendly entrypoint for blackbox recorder."""

import os
import subprocess
import sys
from pathlib import Path

from app.common.compat import ensure_legacy_root_gamma
from app.config.runtime import load_dotenv


def main() -> int:
    load_dotenv()
    root = Path(__file__).resolve().parent
    ensure_legacy_root_gamma(root)
    target = root / "gex_blackbox_recorder.py"
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.call([sys.executable, str(target), *sys.argv[1:]], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
