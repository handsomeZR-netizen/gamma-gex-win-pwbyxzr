# Strategy Visualization Upgrade Summary

Updated: 2026-02-07

## What Was Added

1. `snapshot` API now includes a full `strategy` section:
   - `strategy.core`
   - `strategy.tradeable`
   - `strategy.checks`
   - `strategy.market_inputs`
   - `strategy.meta`

2. Dashboard UI was redesigned for strategy-first workflows:
   - Chinese-first bilingual copy (Chinese business labels + English technical terms)
   - Action card (`TRADE` / `NO_TRADE`)
   - Core strategy card (`IC/CALL/PUT/SKIP`, strikes, confidence)
   - Decision-flow checks strip (pass/fail/non-blocking)
   - GEX structure chart with Pin / Call Wall / Put Wall markers
   - History replay chart (spot vs pin) + strategy history table
   - Built-in debug panel with:
     - service/snapshot summary
     - recent errors
     - recent refresh events
     - truncated raw snapshot JSON

3. Quote extraction was fixed for Schwab nested quote payload:
   - `market.spot` and `market.vix` now parse from nested `quote` fields.

## Backend Changes

- `app/signals/engine.py`
  - Added `build_dashboard_strategy(...)` to compute strategy payload without writing signal logs.
  - Added `fast_mode` support for dashboard refresh loops.
  - Added `use_external_volatility_checks` option in `compute_tradeable_signal(...)`.

- `app/signals/__init__.py`
  - Exported `build_dashboard_strategy`.

- `app/services/market_snapshot_service.py`
  - Attached `strategy` to every snapshot and history item.
  - Added fallback unavailable strategy payload when strategy compute fails.
  - Added structured service logging for refresh success/failure:
    - `data/logs/dashboard_server.log`
    - `data/logs/dashboard_error.log`
  - Added in-memory debug buffers (recent events + recent errors).

- `app/analytics/gex_dashboard.py`
  - Improved `extract_quote_price(...)` to read nested quote buckets.

- `app/api/dashboard_server.py`
  - Added `GET /api/dashboard/debug?index=SPX|NDX` for debug diagnostics.

- `run_dashboard.py`
  - Added `DASHBOARD_STRATEGY_FAST_MODE` env toggle for strict vs fast dashboard checks.

## Frontend Changes

- `dashboard/index.html`
  - Rebuilt layout and styles.
  - Localized UI into Chinese-first bilingual copy.
  - Added ECharts-based GEX and history charts.
  - Added strategy decision-flow rendering from `strategy.checks`.
  - Added core strategy and reasons panels.
  - Added collapsible debug panel and debug-copy action.
  - Updated history table to include strategy/action context.

## Notes

- This remains a read-only dashboard; no order placement is added.
- `strategy.fast_mode=true` is used in dashboard snapshots to keep refresh latency stable.
