from __future__ import annotations

import contextlib
import datetime
import io
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytz
import requests
import yfinance as yf

from app.common.filelock import locked_open
from app.common.paths import data_path
from core.gex_strategy import get_gex_trade_setup
from index_config import IndexConfig, get_index_config


ET = pytz.timezone("US/Eastern")
LIVE_URL = "https://api.tradier.com/v1"

# Signal filter settings aligned with live scalper defaults.
CUTOFF_HOUR = 13
ABSOLUTE_CUTOFF_HOUR = 15
VIX_FLOOR = 13.0
RSI_MIN = 40.0
RSI_MAX = 80.0
SKIP_FRIDAY = False
MAX_CONSEC_DOWN_DAYS = 5
MAX_GAP_PCT = 0.5
MIN_EXPECTED_MOVE_BASE = 10.0


@dataclass(frozen=True)
class SignalOverrides:
    pin_override: float | None = None
    price_override: float | None = None
    vix_override: float | None = None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return None
        return out
    except (TypeError, ValueError):
        return None


def _fetch_tradier_quote(symbol: str, live_key: str) -> float | None:
    if not live_key:
        return None

    headers = {"Accept": "application/json", "Authorization": f"Bearer {live_key}"}
    try:
        r = requests.get(f"{LIVE_URL}/markets/quotes", headers=headers, params={"symbols": symbol}, timeout=10)
        if r.status_code != 200:
            return None
        quote = r.json().get("quotes", {}).get("quote")
        if not quote:
            return None
        if isinstance(quote, list):
            quote = quote[0]
        for key in ("last", "bid", "ask"):
            price = _safe_float(quote.get(key))
            if price is not None and price > 0:
                return price
        return None
    except Exception:
        return None


def _fetch_yf_last_price(symbol: str, period: str = "1d", interval: str = "1m") -> float | None:
    try:
        df = _yf_download(symbol, period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        close = df["Close"].iloc[-1]
        if isinstance(close, pd.Series):
            close = close.iloc[0]
        return _safe_float(close)
    except Exception:
        return None


def _yf_download(*args: Any, **kwargs: Any) -> pd.DataFrame:
    kwargs.setdefault("progress", False)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return yf.download(*args, **kwargs)


def get_index_price(index_config: IndexConfig, live_key: str) -> Tuple[float | None, str]:
    threshold = 100.0 if index_config.index_symbol == "DJX" else 1000.0

    index_price = _fetch_tradier_quote(index_config.index_symbol, live_key)
    if index_price is not None and index_price > threshold:
        return round(index_price), "tradier_index"

    etf_price = _fetch_tradier_quote(index_config.etf_symbol, live_key)
    if etf_price is not None and etf_price > 10:
        return round(etf_price * index_config.etf_multiplier), "tradier_etf_proxy"

    ticker_map = {"SPX": "^GSPC", "NDX": "^NDX", "DJX": "^DJI"}
    yf_index = _fetch_yf_last_price(ticker_map.get(index_config.code, "^GSPC"))
    if yf_index is not None and yf_index > threshold:
        return round(yf_index), "yfinance_index"

    yf_etf = _fetch_yf_last_price(index_config.etf_symbol)
    if yf_etf is not None and yf_etf > 10:
        return round(yf_etf * index_config.etf_multiplier), "yfinance_etf_proxy"

    return None, "unavailable"


def get_vix(live_key: str) -> Tuple[float | None, str]:
    tradier_vix = _fetch_tradier_quote("VIX", live_key)
    if tradier_vix is not None and tradier_vix > 5:
        return tradier_vix, "tradier"

    try:
        vix_data = _yf_download("^VIX", period="1d")
        if not vix_data.empty:
            close = vix_data["Close"].iloc[-1]
            if isinstance(close, pd.Series):
                close = close.iloc[0]
            vix_value = _safe_float(close)
            if vix_value is not None and vix_value > 5:
                return vix_value, "yfinance"
    except Exception:
        pass

    return None, "unavailable"


def get_rsi(symbol: str = "SPY", period: int = 14) -> float:
    try:
        data = _yf_download(symbol, period="30d", auto_adjust=True)
        if data.empty:
            return 50.0

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        avg_gain_val = avg_gain.iloc[-1]
        avg_loss_val = avg_loss.iloc[-1]

        if avg_loss_val == 0 or pd.isna(avg_loss_val):
            return 100.0
        if avg_gain_val == 0 or pd.isna(avg_gain_val):
            return 0.0

        rs = avg_gain_val / avg_loss_val
        rsi_val = 100 - (100 / (1 + rs))
        return round(float(rsi_val), 1)
    except Exception:
        return 50.0


def get_consecutive_down_days(symbol: str = "SPY") -> int:
    try:
        data = _yf_download(symbol, period="10d", auto_adjust=True)
        if data.empty:
            return 0

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        returns = close.pct_change().dropna()
        count = 0
        for value in reversed(returns.tolist()):
            if value < 0:
                count += 1
            else:
                break
        return count
    except Exception:
        return 0


def calculate_gap_size() -> float:
    try:
        data = _yf_download("SPY", period="2d", auto_adjust=True)
        if len(data) < 2:
            return 0.0

        prev_close = data["Close"].iloc[-2]
        today_open = data["Open"].iloc[-1]
        if isinstance(prev_close, pd.Series):
            prev_close = prev_close.iloc[0]
        if isinstance(today_open, pd.Series):
            today_open = today_open.iloc[0]

        prev_close_f = _safe_float(prev_close)
        today_open_f = _safe_float(today_open)
        if prev_close_f is None or today_open_f is None or prev_close_f == 0:
            return 0.0

        gap_pct = abs((today_open_f - prev_close_f) / prev_close_f) * 100
        return round(gap_pct, 4)
    except Exception:
        return 0.0


def calculate_gex_pin(index_config: IndexConfig, index_price: float, live_key: str) -> float | None:
    if not live_key:
        return None

    headers = {"Accept": "application/json", "Authorization": f"Bearer {live_key}"}
    today = datetime.date.today().strftime("%Y-%m-%d")
    try:
        r = requests.get(
            f"{LIVE_URL}/markets/options/chains",
            headers=headers,
            params={"symbol": index_config.index_symbol, "expiration": today, "greeks": "true"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        options = r.json().get("options", {}).get("option", [])
        if not options:
            return None
    except Exception:
        return None

    gex_by_strike: Dict[float, float] = {}
    for opt in options:
        strike = _safe_float(opt.get("strike"))
        oi = _safe_float(opt.get("open_interest"))
        gamma = _safe_float((opt.get("greeks") or {}).get("gamma"))
        if strike is None or oi is None or gamma is None:
            continue
        if oi == 0 or gamma == 0:
            continue

        gex = gamma * oi * 100 * (index_price ** 2)
        if opt.get("option_type") == "call":
            gex_by_strike[strike] = gex_by_strike.get(strike, 0.0) + gex
        else:
            gex_by_strike[strike] = gex_by_strike.get(strike, 0.0) - gex

    if not gex_by_strike:
        return None

    max_distance_pct = 0.015 if index_config.code == "SPX" else 0.020
    max_distance = index_price * max_distance_pct
    nearby_positive = [(s, g) for s, g in gex_by_strike.items() if abs(s - index_price) < max_distance and g > 0]

    if not nearby_positive:
        nearby_positive = [(s, g) for s, g in gex_by_strike.items() if abs(s - index_price) < index_config.far_max and g > 0]

    if nearby_positive:
        def score_peak(strike: float, gex: float) -> float:
            distance_pct = abs(strike - index_price) / max(index_price, 1.0)
            return gex / (distance_pct ** 5 + 1e-12)

        pin_strike, _, _ = max(((s, g, score_peak(s, g)) for s, g in nearby_positive), key=lambda x: x[2])
        return float(pin_strike)

    nearby_all = [(s, g) for s, g in gex_by_strike.items() if abs(s - index_price) < index_config.far_max]
    if nearby_all:
        pin_strike, _ = max(nearby_all, key=lambda x: abs(x[1]))
        return float(pin_strike)
    return None


def is_in_blackout_period(now_et: datetime.datetime) -> Tuple[bool, str | None]:
    if now_et.hour < 10:
        return True, "Before 10:00 AM ET - early volatility blocked"
    if now_et.hour >= 12:
        return True, "After noon ET - low performance period blocked"
    return False, None


def check_vix_spike(current_vix: float, lookback_minutes: int = 5) -> Tuple[bool, str | None]:
    try:
        vix_data = _yf_download("^VIX", period="1d", interval="5m")
        if len(vix_data) < 2:
            return True, None

        recent_vix = _safe_float(vix_data["Close"].iloc[-2])
        if recent_vix is None or recent_vix == 0:
            return True, None

        change_pct = (current_vix - recent_vix) / recent_vix
        if change_pct > 0.05:
            return False, f"VIX spiked {change_pct*100:.1f}% in {lookback_minutes}min ({recent_vix:.2f}->{current_vix:.2f})"
        return True, None
    except Exception:
        return True, None


def check_realized_volatility(index_symbol: str = "SPX", lookback_minutes: int = 30) -> Tuple[bool, str | None]:
    ticker_map = {"SPX": "^GSPC", "NDX": "^NDX", "DJX": "^DJI"}
    ticker = ticker_map.get(index_symbol, "^GSPC")

    try:
        data = _yf_download(ticker, period="2d", interval="5m", auto_adjust=True)
        if len(data) < 20:
            return True, None

        data["bar_range"] = data["High"] - data["Low"]
        bars_needed = max(1, lookback_minutes // 5)
        recent_bars = data.tail(bars_needed)
        baseline_bars = data.iloc[:-bars_needed]
        if baseline_bars.empty:
            return True, None

        recent_avg = _safe_float(recent_bars["bar_range"].mean())
        baseline_avg = _safe_float(baseline_bars["bar_range"].mean())
        if recent_avg is None or baseline_avg is None or baseline_avg <= 0:
            return True, None

        threshold = baseline_avg * 2.5
        if recent_avg > threshold:
            ratio = recent_avg / baseline_avg
            return False, f"Intraday volatility {recent_avg:.1f}pts is {ratio:.1f}x baseline ({baseline_avg:.1f}pts)"
        return True, None
    except Exception:
        return True, None


def compute_expected_move_2hr(index_price: float | None, vix: float | None) -> float | None:
    if index_price is None or vix is None:
        return None
    expected_move = index_price * (vix / 100) * math.sqrt(2.0 / (252 * 6.5))
    return round(expected_move, 2)


def compute_core_signal(
    pin_price: float | None,
    index_price: float | None,
    vix: float | None,
    *,
    index_symbol: str,
) -> Dict[str, Any]:
    if pin_price is None or index_price is None or vix is None:
        return {
            "available": False,
            "strategy": "UNAVAILABLE",
            "reason": "Missing pin/index/VIX data for core signal",
        }

    setup = get_gex_trade_setup(
        pin_price=pin_price,
        spx_price=index_price,
        vix=vix,
        vix_threshold=20.0,
        index_symbol=index_symbol,
    )
    return {
        "available": True,
        "strategy": setup.strategy,
        "direction": setup.direction,
        "confidence": setup.confidence,
        "distance": round(setup.distance, 2),
        "description": setup.description,
        "strikes": setup.strikes,
        "spread_width": setup.spread_width,
        "vix": round(setup.vix, 2),
    }


def _check_short_strike_proximity(
    core_signal: Dict[str, Any],
    index_price: float,
    index_config: IndexConfig,
) -> Tuple[bool, str | None]:
    strategy = core_signal.get("strategy")
    strikes = core_signal.get("strikes") or []
    min_distance = index_config.strike_increment

    if strategy == "IC":
        if len(strikes) < 4:
            return False, "IC strikes incomplete"
        call_short, _, put_short, _ = strikes
        call_distance = call_short - index_price
        put_distance = index_price - put_short
        if call_distance < min_distance:
            return False, f"Short call only {call_distance:.1f}pts from spot ({index_price:.1f})"
        if put_distance < min_distance:
            return False, f"Short put only {put_distance:.1f}pts from spot ({index_price:.1f})"
        return True, None

    if strategy in {"CALL", "PUT"}:
        if len(strikes) < 2:
            return False, f"{strategy} strikes incomplete"
        short_strike = strikes[0]
        distance = (short_strike - index_price) if strategy == "CALL" else (index_price - short_strike)
        if distance < min_distance:
            return False, f"Short strike only {distance:.1f}pts from spot ({index_price:.1f})"
    return True, None


def compute_tradeable_signal(
    *,
    index_config: IndexConfig,
    now_et: datetime.datetime,
    market_snapshot: Dict[str, Any],
    core_signal: Dict[str, Any],
    use_external_volatility_checks: bool = True,
) -> Dict[str, Any]:
    reasons: List[str] = []
    checks: Dict[str, Dict[str, Any]] = {}

    def add_check(
        name: str,
        ok: bool,
        pass_detail: str,
        fail_detail: str,
        *,
        blocking: bool = True,
    ) -> None:
        detail = pass_detail if ok else fail_detail
        checks[name] = {"ok": ok, "detail": detail, "blocking": blocking}
        if blocking and not ok:
            reasons.append(detail)

    is_weekday = now_et.weekday() < 5
    add_check(
        "market_open_day",
        is_weekday,
        "Weekday session",
        "Weekend - no 0DTE trading",
    )

    add_check(
        "entry_cutoff",
        now_et.hour < CUTOFF_HOUR,
        f"Before {CUTOFF_HOUR:02d}:00 ET entry cutoff",
        f"Past {CUTOFF_HOUR:02d}:00 ET entry cutoff",
    )
    add_check(
        "absolute_cutoff",
        now_et.hour < ABSOLUTE_CUTOFF_HOUR,
        f"Before {ABSOLUTE_CUTOFF_HOUR:02d}:00 ET absolute cutoff",
        f"In last hour before expiration ({ABSOLUTE_CUTOFF_HOUR:02d}:00 ET+)",
    )

    in_blackout, blackout_reason = is_in_blackout_period(now_et)
    add_check(
        "timing_blackout",
        not in_blackout,
        "Allowed entry window",
        blackout_reason or "Blocked by timing blackout",
    )

    vix = _safe_float(market_snapshot.get("vix"))
    if vix is None:
        add_check("vix_available", False, "VIX available", "VIX unavailable")
    else:
        add_check("vix_available", True, "VIX available", "VIX unavailable")
        add_check(
            "vix_floor",
            vix >= VIX_FLOOR,
            f"VIX {vix:.2f} >= floor {VIX_FLOOR:.1f}",
            f"VIX {vix:.2f} below floor {VIX_FLOOR:.1f}",
        )
        if use_external_volatility_checks:
            vix_safe, spike_reason = check_vix_spike(vix)
            add_check(
                "vix_spike",
                vix_safe,
                "No VIX spike detected",
                spike_reason or "VIX spike detected",
            )
        else:
            add_check(
                "vix_spike",
                True,
                "Skipped external VIX spike check (dashboard fast mode)",
                "Skipped external VIX spike check (dashboard fast mode)",
                blocking=False,
            )

    if use_external_volatility_checks:
        rvol_ok, rvol_reason = check_realized_volatility(index_config.code, lookback_minutes=30)
        add_check(
            "realized_volatility",
            rvol_ok,
            "Realized volatility acceptable",
            rvol_reason or "Realized volatility too high",
        )
    else:
        add_check(
            "realized_volatility",
            True,
            "Skipped external realized-volatility check (dashboard fast mode)",
            "Skipped external realized-volatility check (dashboard fast mode)",
            blocking=False,
        )

    expected_move = _safe_float(market_snapshot.get("expected_move_2hr"))
    min_expected_move = MIN_EXPECTED_MOVE_BASE * (index_config.base_spread_width / 5)
    if expected_move is None:
        add_check(
            "expected_move",
            False,
            f"Expected move >= {min_expected_move:.1f}pts",
            "Expected move unavailable (missing spot/VIX)",
        )
    else:
        add_check(
            "expected_move",
            expected_move >= min_expected_move,
            f"Expected move {expected_move:.1f}pts >= {min_expected_move:.1f}pts threshold",
            f"Expected move {expected_move:.1f}pts < {min_expected_move:.1f}pts threshold",
        )

    rsi = _safe_float(market_snapshot.get("rsi"))
    if rsi is None:
        add_check("rsi", False, "RSI available", "RSI unavailable")
    else:
        add_check(
            "rsi",
            RSI_MIN <= rsi <= RSI_MAX,
            f"RSI {rsi:.1f} in range {RSI_MIN:.0f}-{RSI_MAX:.0f}",
            f"RSI {rsi:.1f} outside {RSI_MIN:.0f}-{RSI_MAX:.0f}",
        )

    if SKIP_FRIDAY:
        add_check(
            "friday_policy",
            now_et.weekday() != 4,
            "Friday policy satisfied",
            "Friday trading disabled by policy",
        )
    else:
        add_check("friday_policy", True, "Friday trading allowed", "Friday trading blocked", blocking=False)

    consec_down = market_snapshot.get("consecutive_down_days")
    if isinstance(consec_down, int):
        add_check(
            "consecutive_down_days",
            consec_down <= MAX_CONSEC_DOWN_DAYS,
            f"{consec_down} consecutive down days <= {MAX_CONSEC_DOWN_DAYS}",
            f"{consec_down} consecutive down days > {MAX_CONSEC_DOWN_DAYS}",
        )
    else:
        add_check(
            "consecutive_down_days",
            False,
            "Consecutive down-days metric available",
            "Consecutive down-days metric unavailable",
        )

    gap_pct = _safe_float(market_snapshot.get("gap_pct"))
    if gap_pct is None:
        add_check("gap_size", False, "Gap metric available", "Gap metric unavailable")
    else:
        add_check(
            "gap_size",
            gap_pct <= MAX_GAP_PCT,
            f"Gap {gap_pct:.2f}% <= {MAX_GAP_PCT:.2f}%",
            f"Gap {gap_pct:.2f}% > {MAX_GAP_PCT:.2f}%",
        )

    pin_price = _safe_float(market_snapshot.get("pin_price"))
    add_check(
        "gex_pin",
        pin_price is not None,
        "GEX pin available",
        "GEX pin unavailable (provide TRADIER_LIVE_KEY or --pin-override)",
    )

    if not core_signal.get("available", False):
        add_check(
            "core_signal",
            False,
            "Core signal available",
            core_signal.get("reason", "Core signal unavailable"),
        )
    else:
        add_check("core_signal", True, "Core signal available", "Core signal unavailable", blocking=False)
        if core_signal.get("strategy") == "SKIP":
            add_check(
                "core_strategy",
                False,
                "Core strategy actionable",
                core_signal.get("description", "Core strategy is SKIP"),
            )
        else:
            add_check(
                "core_strategy",
                True,
                "Core strategy actionable",
                "Core strategy is SKIP",
                blocking=False,
            )

    index_price = _safe_float(market_snapshot.get("index_price"))
    if index_price is not None and core_signal.get("available", False) and core_signal.get("strategy") != "SKIP":
        proximity_ok, proximity_reason = _check_short_strike_proximity(core_signal, index_price, index_config)
        add_check(
            "short_strike_proximity",
            proximity_ok,
            "Short strike distance acceptable",
            proximity_reason or "Short strike too close to spot",
        )

    action = "TRADE" if not reasons else "NO_TRADE"
    return {
        "action": action,
        "primary_reason": "All entry filters passed" if action == "TRADE" else reasons[0],
        "reasons": reasons,
        "checks": checks,
        "evaluated_at_et": now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


def build_dashboard_strategy(
    index_code: str,
    *,
    index_price: float | None,
    pin_price: float | None,
    vix: float | None,
    now_utc: datetime.datetime | None = None,
    include_extended_metrics: bool = True,
    fast_mode: bool = True,
) -> Dict[str, Any]:
    """
    Build strategy payload for dashboard snapshots without writing signal logs.
    """
    index_config = get_index_config(index_code.upper())
    now_utc = now_utc or datetime.datetime.now(tz=datetime.timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=datetime.timezone.utc)
    now_et = now_utc.astimezone(ET)

    warnings: List[str] = []
    metrics_source = "defaults"

    if include_extended_metrics:
        try:
            rsi = get_rsi(index_config.etf_symbol)
            consecutive_down_days = get_consecutive_down_days(index_config.etf_symbol)
            gap_pct = calculate_gap_size()
            metrics_source = "yfinance"
        except Exception as exc:
            rsi = 50.0
            consecutive_down_days = 0
            gap_pct = 0.0
            warnings.append(f"Failed to collect extended metrics: {exc}")
    else:
        rsi = 50.0
        consecutive_down_days = 0
        gap_pct = 0.0

    expected_move_2hr = compute_expected_move_2hr(index_price, vix)
    market_snapshot = {
        "index_code": index_config.code,
        "index_symbol": index_config.index_symbol,
        "index_price": index_price,
        "index_price_source": "schwab_snapshot",
        "pin_price": pin_price,
        "pin_source": "schwab_chain",
        "vix": round(vix, 2) if vix is not None else None,
        "vix_source": "schwab_snapshot",
        "rsi": rsi,
        "consecutive_down_days": consecutive_down_days,
        "gap_pct": round(gap_pct, 4),
        "expected_move_2hr": expected_move_2hr,
    }

    core_signal = compute_core_signal(
        pin_price=pin_price,
        index_price=index_price,
        vix=vix,
        index_symbol=index_config.code,
    )

    tradeable_signal = compute_tradeable_signal(
        index_config=index_config,
        now_et=now_et,
        market_snapshot=market_snapshot,
        core_signal=core_signal,
        use_external_volatility_checks=not fast_mode,
    )

    return {
        "core": core_signal,
        "tradeable": tradeable_signal,
        "checks": tradeable_signal.get("checks", {}),
        "market_inputs": market_snapshot,
        "meta": {
            "source": "app.signals.engine",
            "index_code": index_config.code,
            "generated_at_utc": now_utc.isoformat(),
            "generated_at_et": now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "metrics_source": metrics_source,
            "fast_mode": fast_mode,
            "warnings": warnings,
        },
    }


def append_signal_log(record: Dict[str, Any], *, now_et: datetime.datetime | None = None) -> Path:
    now = now_et or datetime.datetime.now(ET)
    file_path = data_path(f"signals_{now.strftime('%Y%m%d')}.jsonl")
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    with locked_open(file_path, "a", exclusive=True) as handle:
        handle.write(line + "\n")
    return file_path


def evaluate_signal(index_code: str, *, overrides: SignalOverrides | None = None) -> Dict[str, Any]:
    index_config = get_index_config(index_code.upper())
    now_utc = datetime.datetime.now(tz=datetime.timezone.utc)
    now_et = now_utc.astimezone(ET)
    overrides = overrides or SignalOverrides()
    warnings: List[str] = []

    live_key = os.getenv("TRADIER_LIVE_KEY", "").strip()
    if not live_key:
        warnings.append("TRADIER_LIVE_KEY is not set; live quotes/GEX pin may be unavailable.")

    if overrides.price_override is not None:
        index_price = float(overrides.price_override)
        index_price_source = "override"
    else:
        index_price, index_price_source = get_index_price(index_config, live_key)
        if index_price is None:
            warnings.append(f"{index_config.code} spot price unavailable from Tradier/yfinance.")

    if overrides.vix_override is not None:
        vix = float(overrides.vix_override)
        vix_source = "override"
    else:
        vix, vix_source = get_vix(live_key)
        if vix is None:
            warnings.append("VIX unavailable from Tradier/yfinance.")

    rsi = get_rsi("SPY")
    consec_down_days = get_consecutive_down_days("SPY")
    gap_pct = calculate_gap_size()
    expected_move_2hr = compute_expected_move_2hr(index_price, vix)

    if overrides.pin_override is not None:
        pin_price = float(overrides.pin_override)
        pin_source = "override"
    elif index_price is not None:
        pin_price = calculate_gex_pin(index_config, index_price, live_key)
        pin_source = "tradier_gex" if pin_price is not None else "unavailable"
    else:
        pin_price = None
        pin_source = "unavailable"
    if pin_price is None:
        warnings.append("GEX pin unavailable; tradeable signal will likely be NO_TRADE.")

    core_signal = compute_core_signal(
        pin_price=pin_price,
        index_price=index_price,
        vix=vix,
        index_symbol=index_config.code,
    )

    market_snapshot = {
        "index_code": index_config.code,
        "index_symbol": index_config.index_symbol,
        "index_price": index_price,
        "index_price_source": index_price_source,
        "pin_price": pin_price,
        "pin_source": pin_source,
        "vix": round(vix, 2) if vix is not None else None,
        "vix_source": vix_source,
        "rsi": rsi,
        "consecutive_down_days": consec_down_days,
        "gap_pct": round(gap_pct, 4),
        "expected_move_2hr": expected_move_2hr,
    }

    tradeable_signal = compute_tradeable_signal(
        index_config=index_config,
        now_et=now_et,
        market_snapshot=market_snapshot,
        core_signal=core_signal,
    )

    payload: Dict[str, Any] = {
        "mode": "signal_only",
        "timestamp_utc": now_utc.isoformat(),
        "timestamp_et": now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "index": index_config.code,
        "market": market_snapshot,
        "core_signal": core_signal,
        "tradeable_signal": tradeable_signal,
        "warnings": warnings,
    }
    log_file = append_signal_log(payload, now_et=now_et)
    payload["log_file"] = str(log_file)
    return payload


def format_human_signal(payload: Dict[str, Any]) -> str:
    market = payload.get("market", {})
    core = payload.get("core_signal", {})
    tradeable = payload.get("tradeable_signal", {})

    lines = [
        f"[{payload.get('timestamp_et', '-')}] {payload.get('index', 'N/A')} SIGNAL (READ-ONLY)",
        (
            f"Spot={market.get('index_price')} ({market.get('index_price_source')}) | "
            f"PIN={market.get('pin_price')} ({market.get('pin_source')}) | "
            f"VIX={market.get('vix')} ({market.get('vix_source')})"
        ),
        (
            f"RSI={market.get('rsi')} | DownDays={market.get('consecutive_down_days')} | "
            f"Gap={market.get('gap_pct')}% | ExpMove2h={market.get('expected_move_2hr')}pts"
        ),
    ]

    if core.get("available"):
        lines.append(
            f"Core={core.get('strategy')} {core.get('direction')} {core.get('confidence')} | "
            f"{core.get('description')}"
        )
    else:
        lines.append(f"Core=UNAVAILABLE | {core.get('reason')}")

    lines.append(f"Tradeable={tradeable.get('action')} | {tradeable.get('primary_reason')}")
    reasons = tradeable.get("reasons") or []
    if len(reasons) > 1:
        lines.append("Additional reasons:")
        lines.extend([f"- {reason}" for reason in reasons[1:]])

    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend([f"- {warning}" for warning in warnings])

    lines.append(f"Log={payload.get('log_file')}")
    return "\n".join(lines)
