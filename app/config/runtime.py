from __future__ import annotations

import os
from pathlib import Path

from app.common.paths import PROJECT_ROOT


def load_dotenv(env_file: Path | None = None, *, override: bool = False) -> Path:
    env_path = env_file or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return env_path

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if override or key not in os.environ:
            os.environ[key] = value
    return env_path

