from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_home() -> Path:
    env_home = os.getenv("GAMMA_HOME", "").strip()
    if env_home:
        return Path(env_home).expanduser().resolve()
    return PROJECT_ROOT


GAMMA_HOME = _resolve_home()
DATA_DIR = Path(os.getenv("GAMMA_DATA_DIR", str(GAMMA_HOME / "data"))).expanduser().resolve()
LOGS_DIR = DATA_DIR / "logs"
TMP_DIR = DATA_DIR / "tmp"

for directory in (DATA_DIR, LOGS_DIR, TMP_DIR):
    directory.mkdir(parents=True, exist_ok=True)

ACCOUNT_BALANCE_FILE = DATA_DIR / "account_balance.json"
ORDERS_PAPER_FILE = DATA_DIR / "orders_paper.json"
ORDERS_LIVE_FILE = DATA_DIR / "orders_live.json"
TRADES_FILE = DATA_DIR / "trades.csv"
GEX_BLACKBOX_DB = DATA_DIR / "gex_blackbox.db"
YFINANCE_WARNINGS_LOG = LOGS_DIR / "yfinance_warnings.log"
MONITOR_PAPER_LOG = LOGS_DIR / "monitor_paper.log"
MONITOR_LIVE_LOG = LOGS_DIR / "monitor_live.log"
DISCORD_MESSAGES_FILE = DATA_DIR / "discord_messages.json"


def data_path(*parts: str) -> Path:
    return DATA_DIR.joinpath(*parts)


def tmp_path(*parts: str) -> Path:
    return TMP_DIR.joinpath(*parts)

