from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.common.compat import ensure_legacy_root_gamma
from app.config.runtime import load_dotenv


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    load_dotenv()
    root = Path(__file__).resolve().parents[2]
    ensure_legacy_root_gamma(root)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.call([sys.executable, str(root / "gex_blackbox_recorder.py"), *args], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
