from __future__ import annotations

import datetime as dt
import json
import logging
import threading
import time
from copy import deepcopy
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, List

from app.analytics import build_dashboard_snapshot
from app.common.filelock import locked_open
from app.common.paths import data_path
from app.providers import SchwabClient, SchwabClientError
from app.signals import build_dashboard_strategy
from index_config import get_index_config


INDEX_SYMBOL_MAP: Dict[str, str] = {
    "SPX": "$SPX",
    "NDX": "$NDX",
}

VIX_SYMBOL = "$VIX"


@dataclass
class SnapshotState:
    snapshot: Dict[str, Any] | None = None
    updated_at_epoch: float = 0.0
    last_error: str | None = None


class MarketSnapshotService:
    def __init__(self, *, client: SchwabClient, refresh_seconds: int = 12, strategy_fast_mode: bool = True) -> None:
        self.client = client
        self.refresh_seconds = max(5, int(refresh_seconds))
        self.strategy_fast_mode = bool(strategy_fast_mode)
        self._lock = threading.Lock()
        self._states: Dict[str, SnapshotState] = {}
        self._history_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._refresh_locks: Dict[str, threading.Lock] = {}
        self._recent_events: Deque[Dict[str, Any]] = deque(maxlen=300)
        self._recent_errors: Deque[Dict[str, Any]] = deque(maxlen=120)
        self._logger = self._create_logger()

    @staticmethod
    def _create_logger() -> logging.Logger:
        logger = logging.getLogger("gamma.dashboard.service")
        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)
        logger.propagate = False
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        success_handler = logging.FileHandler(data_path("logs", "dashboard_server.log"), encoding="utf-8")
        success_handler.setLevel(logging.INFO)
        success_handler.setFormatter(formatter)

        error_handler = logging.FileHandler(data_path("logs", "dashboard_error.log"), encoding="utf-8")
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)

        logger.addHandler(success_handler)
        logger.addHandler(error_handler)
        return logger

    def _append_event(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self._recent_events.append(event)
            if event.get("level") in {"warning", "error"}:
                self._recent_errors.append(event)

    def _resolve_schwab_symbol(self, index_code: str) -> str:
        if index_code in INDEX_SYMBOL_MAP:
            return INDEX_SYMBOL_MAP[index_code]
        index_cfg = get_index_config(index_code)
        return f"${index_cfg.index_symbol}"

    def _history_path(self, index_code: str, now: dt.datetime | None = None) -> Path:
        ts = now or dt.datetime.now()
        return data_path(f"dashboard_snapshots_{index_code.lower()}_{ts.strftime('%Y%m%d')}.jsonl")

    def _write_history(self, index_code: str, snapshot: Dict[str, Any]) -> None:
        path = self._history_path(index_code)
        line = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
        with locked_open(path, "a", exclusive=True) as handle:
            handle.write(line + "\n")

    def _append_memory_history(self, index_code: str, snapshot: Dict[str, Any]) -> None:
        history = self._history_cache.setdefault(index_code, [])
        history.append(snapshot)
        if len(history) > 500:
            del history[:-500]

    def _extract_quote_bucket(self, quotes: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        if not isinstance(quotes, dict):
            return {}
        bucket = quotes.get(symbol) or quotes.get(symbol.replace("$", ""))
        if isinstance(bucket, dict):
            return bucket
        return {}

    def _fetch_option_chain_with_fallback(self, symbol: str) -> Dict[str, Any]:
        candidates = [symbol]
        if symbol.startswith("$"):
            candidates.append(symbol[1:])
        for item in candidates:
            chain = self.client.get_option_chain(symbol=item)
            if chain:
                return chain
        return {}

    @staticmethod
    def _build_unavailable_strategy(index_code: str, *, now_utc: dt.datetime, reason: str) -> Dict[str, Any]:
        return {
            "core": {
                "available": False,
                "strategy": "UNAVAILABLE",
                "reason": reason,
            },
            "tradeable": {
                "action": "NO_TRADE",
                "primary_reason": reason,
                "reasons": [reason],
                "checks": {},
                "evaluated_at_et": None,
            },
            "checks": {},
            "market_inputs": {
                "index_code": index_code,
                "index_price": None,
                "pin_price": None,
                "vix": None,
            },
            "meta": {
                "source": "app.signals.engine",
                "index_code": index_code,
                "generated_at_utc": now_utc.isoformat(),
                "generated_at_et": None,
                "metrics_source": "unavailable",
                "warnings": [reason],
                "error": reason,
            },
        }

    def refresh_snapshot(self, index_code: str) -> Dict[str, Any]:
        index_code = index_code.upper()
        schwab_symbol = self._resolve_schwab_symbol(index_code)
        now = dt.datetime.now()
        now_utc = dt.datetime.now(dt.timezone.utc)
        started_at = time.perf_counter()

        try:
            quotes = self.client.get_quotes([schwab_symbol, VIX_SYMBOL])
            index_quote = self._extract_quote_bucket(quotes, schwab_symbol)
            vix_quote = self._extract_quote_bucket(quotes, VIX_SYMBOL)
            chain = self._fetch_option_chain_with_fallback(schwab_symbol)

            snapshot = build_dashboard_snapshot(
                index_code=index_code,
                index_symbol=schwab_symbol,
                index_quote=index_quote,
                vix_quote=vix_quote,
                option_chain=chain,
                generated_at=now,
            )
            try:
                snapshot["strategy"] = build_dashboard_strategy(
                    index_code=index_code,
                    index_price=snapshot.get("market", {}).get("spot"),
                    pin_price=snapshot.get("gex", {}).get("pin"),
                    vix=snapshot.get("market", {}).get("vix"),
                    now_utc=now_utc,
                    include_extended_metrics=True,
                    fast_mode=self.strategy_fast_mode,
                )
            except Exception as strategy_exc:
                snapshot["strategy"] = self._build_unavailable_strategy(
                    index_code,
                    now_utc=now_utc,
                    reason=f"Strategy compute failed: {strategy_exc}",
                )
            snapshot["system"] = {
                "refresh_seconds": self.refresh_seconds,
                "last_refresh_epoch": time.time(),
                "source": "schwab",
                "error": None,
            }
            elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
            strategy = snapshot.get("strategy", {})
            checks = strategy.get("checks", {}) if isinstance(strategy, dict) else {}
            action = (strategy.get("tradeable") or {}).get("action") if isinstance(strategy, dict) else None
            event = {
                "timestamp_utc": now_utc.isoformat(),
                "level": "info",
                "event": "snapshot_refresh_ok",
                "index": index_code,
                "duration_ms": elapsed_ms,
                "spot": snapshot.get("market", {}).get("spot"),
                "vix": snapshot.get("market", {}).get("vix"),
                "has_strategy": bool(strategy),
                "checks_count": len(checks),
                "action": action,
            }
            self._logger.info(json.dumps(event, ensure_ascii=False))
            self._append_event(event)
            slow_threshold_ms = self.refresh_seconds * 1000.0
            if elapsed_ms > slow_threshold_ms:
                warn_event = {
                    "timestamp_utc": now_utc.isoformat(),
                    "level": "warning",
                    "event": "snapshot_refresh_slow",
                    "index": index_code,
                    "duration_ms": elapsed_ms,
                    "threshold_ms": slow_threshold_ms,
                    "message": "Snapshot refresh exceeded configured refresh interval.",
                }
                self._logger.warning(json.dumps(warn_event, ensure_ascii=False))
                self._append_event(warn_event)
            with self._lock:
                state = self._states.setdefault(index_code, SnapshotState())
                state.snapshot = snapshot
                state.updated_at_epoch = time.time()
                state.last_error = None
                self._append_memory_history(index_code, snapshot)
            self._write_history(index_code, snapshot)
            return snapshot
        except SchwabClientError as exc:
            error_snapshot = {
                "timestamp_utc": now.astimezone(dt.timezone.utc).isoformat(),
                "timestamp_local": now.strftime("%Y-%m-%d %H:%M:%S"),
                "index": {"code": index_code, "symbol": schwab_symbol},
                "market": {"spot": None, "vix": None, "quote": {}, "vix_quote": {}},
                "options": {"summary": {}, "nearest_expiries": [], "top_volume_contracts": [], "top_open_interest_contracts": [], "raw_contract_count": 0},
                "gex": {"pin": None, "distance_to_pin": None, "direction_bias": "UNKNOWN", "net_gex": 0.0, "net_gex_billion": 0.0, "call_wall": None, "put_wall": None, "top_levels": []},
                "signals": {"observation": "UNAVAILABLE", "direction_bias": "UNKNOWN", "reasons": [str(exc)]},
                "strategy": self._build_unavailable_strategy(
                    index_code,
                    now_utc=now_utc,
                    reason=f"Snapshot unavailable: {exc}",
                ),
                "system": {
                    "refresh_seconds": self.refresh_seconds,
                    "last_refresh_epoch": time.time(),
                    "source": "schwab",
                    "error": str(exc),
                },
            }
            elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
            event = {
                "timestamp_utc": now_utc.isoformat(),
                "level": "error",
                "event": "snapshot_refresh_failed",
                "index": index_code,
                "duration_ms": elapsed_ms,
                "error": str(exc),
            }
            self._logger.error(json.dumps(event, ensure_ascii=False))
            self._append_event(event)
            with self._lock:
                state = self._states.setdefault(index_code, SnapshotState())
                state.snapshot = error_snapshot
                state.updated_at_epoch = time.time()
                state.last_error = str(exc)
                self._append_memory_history(index_code, error_snapshot)
            return error_snapshot

    def get_snapshot(self, index_code: str) -> Dict[str, Any]:
        index_code = index_code.upper()
        with self._lock:
            state = self._states.get(index_code)
            snapshot = state.snapshot if state else None
            if snapshot and (time.time() - state.updated_at_epoch) < self.refresh_seconds:
                return snapshot
            refresh_lock = self._refresh_locks.setdefault(index_code, threading.Lock())

        if refresh_lock.acquire(blocking=False):
            try:
                return self.refresh_snapshot(index_code)
            finally:
                refresh_lock.release()

        # Another request is already refreshing this index.
        # Return stale snapshot immediately if available to avoid API read timeouts.
        if snapshot:
            stale_snapshot = deepcopy(snapshot)
            stale_system = dict(stale_snapshot.get("system") or {})
            stale_system["stale"] = True
            stale_system["stale_reason"] = "refresh_in_progress"
            stale_snapshot["system"] = stale_system
            return stale_snapshot

        # No cached snapshot yet; wait briefly for in-flight refresh to complete.
        if refresh_lock.acquire(timeout=max(1.0, self.refresh_seconds)):
            refresh_lock.release()
            with self._lock:
                state = self._states.get(index_code)
                if state and state.snapshot:
                    return state.snapshot

        return self.refresh_snapshot(index_code)

    def get_history(self, index_code: str, limit: int = 100) -> List[Dict[str, Any]]:
        index_code = index_code.upper()
        limit = max(1, min(1000, int(limit)))
        with self._lock:
            history = list(self._history_cache.get(index_code, []))
        if history:
            return list(reversed(history[-limit:]))
        return []

    def health(self) -> Dict[str, Any]:
        with self._lock:
            state_summary = {
                key: {
                    "updated_at_epoch": value.updated_at_epoch,
                    "has_snapshot": value.snapshot is not None,
                    "last_error": value.last_error,
                }
                for key, value in self._states.items()
            }
        return {
            "status": "ok",
            "source": "schwab",
            "refresh_seconds": self.refresh_seconds,
            "strategy_fast_mode": self.strategy_fast_mode,
            "indices": state_summary,
        }

    def debug(self, index_code: str) -> Dict[str, Any]:
        index_code = index_code.upper()
        with self._lock:
            state = self._states.get(index_code)
            snapshot = state.snapshot if state else None
            recent_events = list(self._recent_events)[-80:]
            recent_errors = list(self._recent_errors)[-50:]
            cache_size = len(self._history_cache.get(index_code, []))

        strategy = snapshot.get("strategy") if isinstance(snapshot, dict) else {}
        checks = strategy.get("checks", {}) if isinstance(strategy, dict) else {}
        tradeable = strategy.get("tradeable", {}) if isinstance(strategy, dict) else {}
        return {
            "index": index_code,
            "service": {
                "refresh_seconds": self.refresh_seconds,
                "strategy_fast_mode": self.strategy_fast_mode,
                "cache_size": cache_size,
                "has_snapshot": bool(snapshot),
                "last_error": state.last_error if state else None,
                "updated_at_epoch": state.updated_at_epoch if state else None,
            },
            "snapshot_summary": {
                "timestamp_local": snapshot.get("timestamp_local") if isinstance(snapshot, dict) else None,
                "spot": snapshot.get("market", {}).get("spot") if isinstance(snapshot, dict) else None,
                "vix": snapshot.get("market", {}).get("vix") if isinstance(snapshot, dict) else None,
                "pin": snapshot.get("gex", {}).get("pin") if isinstance(snapshot, dict) else None,
                "direction_bias": snapshot.get("gex", {}).get("direction_bias") if isinstance(snapshot, dict) else None,
                "strategy_action": tradeable.get("action"),
                "strategy_primary_reason": tradeable.get("primary_reason"),
                "strategy_checks_count": len(checks),
                "strategy_keys": sorted(strategy.keys()) if isinstance(strategy, dict) else [],
            },
            "recent_errors": recent_errors,
            "recent_events": recent_events,
            "log_files": {
                "server_log": str(data_path("logs", "dashboard_server.log")),
                "error_log": str(data_path("logs", "dashboard_error.log")),
            },
        }
