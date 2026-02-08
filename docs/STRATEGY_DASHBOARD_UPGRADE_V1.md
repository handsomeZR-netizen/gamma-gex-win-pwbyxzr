# Strategy Dashboard Upgrade v1

## Overview

This upgrade focused on a more direct visual workflow for trading decisions:

- Chinese-first dashboard copy with technical English aliases.
- Strategy rule timeline to show pass/block/warn sequence.
- Decision score and strategy event overlays in history.
- Debug statistics for rule stability over recent snapshots.

## Backend Changes

### `app/services/market_snapshot_service.py`

- Added strategy UI aggregator:
  - `strategy_ui.decision_score`
  - `strategy_ui.blocking_fail_count`
  - `strategy_ui.soft_warn_count`
  - `strategy_ui.passed_count`
  - `strategy_ui.timeline[]`
- Added per-snapshot strategy event:
  - `strategy_event.action`
  - `strategy_event.primary_reason`
  - `strategy_event.decision_score`
- Added debug rule profiling:
  - `debug.rule_stats[]` with pass/fail rates.
- Kept existing single-flight stale-safe refresh behavior.

## Frontend Changes

### `dashboard/index.html`

- Rebuilt layout with clearer information hierarchy:
  - Top KPI cards (Spot, Pin, VIX, Action, Score).
  - GEX structure chart.
  - Rule timeline lane.
  - Trend chart (Spot/Pin/VIX + TRADE markers).
  - Option top-volume and top-OI tables.
  - Debug panel with grouped errors and rule stats.
- Added robust null-safe rendering for missing fields.
- Added stale/error chips and richer status feedback.

## API Compatibility

No existing route was removed.

- Existing routes continue to work:
  - `/api/health`
  - `/api/dashboard/snapshot`
  - `/api/dashboard/history`
  - `/api/dashboard/debug`
- New fields are additive and backward-compatible.

## Validation Checklist

- Python compile check passed for modified backend file.
- Dashboard smoke script executed successfully against:
  - health endpoint
  - snapshot endpoint
  - history endpoint
  - debug endpoint
- Snapshot payload now contains `strategy_ui` and `strategy_event`.
- Debug payload now contains `rule_stats`.
