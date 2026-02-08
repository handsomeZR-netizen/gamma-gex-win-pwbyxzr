from __future__ import annotations

import os
import subprocess
from pathlib import Path


def ensure_legacy_root_gamma(project_root: Path) -> bool:
    """
    Ensure '/root/gamma' style paths used by legacy scripts resolve on Windows.

    Returns True if alias is available or not needed.
    """
    if os.name != "nt":
        return True

    alias = Path(r"C:\root\gamma")
    if alias.exists():
        return True

    try:
        alias.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(alias),
            str(project_root),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 or alias.exists()
    except Exception:
        return False

