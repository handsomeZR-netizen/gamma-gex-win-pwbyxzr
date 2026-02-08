from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from typing import Any, Dict, List, Tuple


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def _parse_expiry_key(exp_key: str) -> Tuple[str, int]:
    # Schwab shape example: "2026-02-09:3"
    if ":" in exp_key:
        expiry, dte = exp_key.split(":", 1)
        try:
            return expiry, int(float(dte))
        except (TypeError, ValueError):
            return expiry, 0
    return exp_key, 0


def extract_quote_price(quote: Dict[str, Any]) -> float | None:
    buckets: List[Dict[str, Any]] = []
    if isinstance(quote, dict):
        buckets.append(quote)
        nested_quote = quote.get("quote")
        if isinstance(nested_quote, dict):
            buckets.append(nested_quote)

    for bucket in buckets:
        for key in ("lastPrice", "last", "mark", "closePrice", "bidPrice", "askPrice"):
            value = _safe_float(bucket.get(key), default=0.0)
            if value > 0:
                return value
    return None


def flatten_option_chain(chain: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for side_name, side_map in (("CALL", chain.get("callExpDateMap", {})), ("PUT", chain.get("putExpDateMap", {}))):
        if not isinstance(side_map, dict):
            continue
        for exp_key, strike_map in side_map.items():
            expiry, dte = _parse_expiry_key(exp_key)
            if not isinstance(strike_map, dict):
                continue
            for strike_key, contracts in strike_map.items():
                strike = _safe_float(strike_key)
                if not isinstance(contracts, list):
                    continue
                for contract in contracts:
                    if not isinstance(contract, dict):
                        continue
                    bid = _safe_float(contract.get("bid"))
                    ask = _safe_float(contract.get("ask"))
                    mark = _safe_float(contract.get("mark"), default=(bid + ask) / 2 if bid > 0 and ask > 0 else 0.0)
                    last = _safe_float(contract.get("last"))

                    rows.append(
                        {
                            "side": side_name,
                            "symbol": contract.get("symbol"),
                            "expiry": expiry,
                            "dte": dte,
                            "strike": strike,
                            "bid": bid,
                            "ask": ask,
                            "last": last,
                            "mark": mark,
                            "delta": _safe_float(contract.get("delta")),
                            "gamma": _safe_float(contract.get("gamma")),
                            "theta": _safe_float(contract.get("theta")),
                            "vega": _safe_float(contract.get("vega")),
                            "iv": _safe_float(contract.get("volatility"), default=_safe_float(contract.get("iv"))),
                            "open_interest": _safe_float(contract.get("openInterest")),
                            "volume": _safe_float(contract.get("totalVolume"), default=_safe_float(contract.get("volume"))),
                        }
                    )
    return rows


def _group_top_levels(gex_by_strike: Dict[float, float], *, top_n: int = 8) -> List[Dict[str, Any]]:
    ranked = sorted(gex_by_strike.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top_n]
    out: List[Dict[str, Any]] = []
    for strike, gex in ranked:
        out.append(
            {
                "strike": round(strike, 2),
                "gex": gex,
                "gex_billion": round(gex / 1_000_000_000, 3),
                "side": "POSITIVE" if gex >= 0 else "NEGATIVE",
            }
        )
    return out


def _call_put_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    call_oi = sum(r["open_interest"] for r in rows if r["side"] == "CALL")
    put_oi = sum(r["open_interest"] for r in rows if r["side"] == "PUT")
    call_volume = sum(r["volume"] for r in rows if r["side"] == "CALL")
    put_volume = sum(r["volume"] for r in rows if r["side"] == "PUT")

    iv_values = [r["iv"] for r in rows if r["iv"] > 0]
    delta_values = [r["delta"] for r in rows if r["delta"] != 0]
    gamma_values = [r["gamma"] for r in rows if r["gamma"] != 0]

    return {
        "contracts": len(rows),
        "call_open_interest": int(call_oi),
        "put_open_interest": int(put_oi),
        "call_volume": int(call_volume),
        "put_volume": int(put_volume),
        "put_call_oi_ratio": round(put_oi / call_oi, 4) if call_oi > 0 else None,
        "put_call_volume_ratio": round(put_volume / call_volume, 4) if call_volume > 0 else None,
        "avg_iv": round(sum(iv_values) / len(iv_values), 4) if iv_values else None,
        "avg_abs_delta": round(sum(abs(v) for v in delta_values) / len(delta_values), 4) if delta_values else None,
        "avg_abs_gamma": round(sum(abs(v) for v in gamma_values) / len(gamma_values), 6) if gamma_values else None,
    }


def _compute_gex(rows: List[Dict[str, Any]], spot_price: float) -> Dict[str, Any]:
    gex_by_strike: Dict[float, float] = defaultdict(float)
    call_gex_by_strike: Dict[float, float] = defaultdict(float)
    put_gex_by_strike: Dict[float, float] = defaultdict(float)

    for row in rows:
        oi = row["open_interest"]
        gamma = row["gamma"]
        strike = row["strike"]
        if oi <= 0 or gamma == 0 or strike <= 0:
            continue

        raw = gamma * oi * 100 * (spot_price ** 2)
        if row["side"] == "CALL":
            gex_by_strike[strike] += raw
            call_gex_by_strike[strike] += raw
        else:
            gex_by_strike[strike] -= raw
            put_gex_by_strike[strike] -= raw

    if not gex_by_strike:
        return {
            "pin": None,
            "distance_to_pin": None,
            "direction_bias": "UNKNOWN",
            "net_gex": 0.0,
            "net_gex_billion": 0.0,
            "call_wall": None,
            "put_wall": None,
            "top_levels": [],
        }

    # Proximity-weighted pin selection.
    def score(strike: float, gex: float) -> float:
        distance_pct = abs(strike - spot_price) / max(spot_price, 1.0)
        return gex / (distance_pct ** 5 + 1e-12)

    positive_levels = [(s, g) for s, g in gex_by_strike.items() if g > 0]
    if positive_levels:
        pin_strike = max(positive_levels, key=lambda x: score(x[0], x[1]))[0]
    else:
        pin_strike = max(gex_by_strike.items(), key=lambda x: abs(x[1]))[0]

    call_wall = max(call_gex_by_strike.items(), key=lambda x: x[1])[0] if call_gex_by_strike else None
    put_wall = min(put_gex_by_strike.items(), key=lambda x: x[1])[0] if put_gex_by_strike else None

    distance = spot_price - pin_strike
    if abs(distance) <= 6:
        bias = "NEUTRAL_PIN"
    elif distance > 0:
        bias = "BEARISH_PULLBACK"
    else:
        bias = "BULLISH_REVERSION"

    net_gex = sum(gex_by_strike.values())
    return {
        "pin": round(pin_strike, 2),
        "distance_to_pin": round(distance, 2),
        "direction_bias": bias,
        "net_gex": net_gex,
        "net_gex_billion": round(net_gex / 1_000_000_000, 3),
        "call_wall": round(call_wall, 2) if call_wall is not None else None,
        "put_wall": round(put_wall, 2) if put_wall is not None else None,
        "top_levels": _group_top_levels(gex_by_strike),
    }


def _build_signal_summary(gex_section: Dict[str, Any], options_summary: Dict[str, Any], spot: float) -> Dict[str, Any]:
    reasons: List[str] = []
    direction_bias = gex_section.get("direction_bias", "UNKNOWN")
    pin = gex_section.get("pin")
    if pin is not None:
        reasons.append(f"Spot {spot:.2f} vs Pin {pin:.2f} (distance {gex_section['distance_to_pin']:+.2f})")

    pcr_oi = options_summary.get("put_call_oi_ratio")
    pcr_vol = options_summary.get("put_call_volume_ratio")
    if pcr_oi is not None:
        reasons.append(f"PCR(OI)={pcr_oi:.3f}")
    if pcr_vol is not None:
        reasons.append(f"PCR(Volume)={pcr_vol:.3f}")

    if direction_bias == "NEUTRAL_PIN":
        observation = "PINNING_RISK"
    elif direction_bias == "BEARISH_PULLBACK":
        observation = "UPSIDE_STRETCHED"
    elif direction_bias == "BULLISH_REVERSION":
        observation = "DOWNSIDE_STRETCHED"
    else:
        observation = "INCONCLUSIVE"

    return {
        "observation": observation,
        "direction_bias": direction_bias,
        "reasons": reasons,
    }


def build_dashboard_snapshot(
    *,
    index_code: str,
    index_symbol: str,
    index_quote: Dict[str, Any],
    vix_quote: Dict[str, Any] | None,
    option_chain: Dict[str, Any],
    generated_at: dt.datetime,
) -> Dict[str, Any]:
    spot = extract_quote_price(index_quote) or 0.0
    vix = extract_quote_price(vix_quote or {}) if vix_quote else None

    rows = flatten_option_chain(option_chain)
    options_summary = _call_put_summary(rows)
    gex_section = _compute_gex(rows, spot_price=spot if spot > 0 else 1.0)
    signal_summary = _build_signal_summary(gex_section, options_summary, spot=spot)

    expiries = sorted(set(r["expiry"] for r in rows if r.get("expiry")))
    nearest_expiries = expiries[:5]

    top_volume = sorted(rows, key=lambda x: x["volume"], reverse=True)[:10]
    top_oi = sorted(rows, key=lambda x: x["open_interest"], reverse=True)[:10]

    def contract_to_card(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "symbol": row.get("symbol"),
            "side": row["side"],
            "expiry": row["expiry"],
            "strike": row["strike"],
            "volume": int(row["volume"]),
            "open_interest": int(row["open_interest"]),
            "iv": row["iv"],
            "delta": row["delta"],
            "gamma": row["gamma"],
            "mark": row["mark"],
        }

    return {
        "timestamp_utc": generated_at.astimezone(dt.timezone.utc).isoformat(),
        "timestamp_local": generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "index": {"code": index_code, "symbol": index_symbol},
        "market": {
            "spot": round(spot, 4) if spot else None,
            "vix": round(vix, 4) if vix else None,
            "quote": index_quote,
            "vix_quote": vix_quote,
        },
        "options": {
            "summary": options_summary,
            "nearest_expiries": nearest_expiries,
            "top_volume_contracts": [contract_to_card(x) for x in top_volume],
            "top_open_interest_contracts": [contract_to_card(x) for x in top_oi],
            "raw_contract_count": len(rows),
        },
        "gex": gex_section,
        "signals": signal_summary,
    }
