# Architecture Upgrade History

This document tracks major architecture-level changes for the project in a single timeline.
It is focused on runtime architecture, data source migration, reliability upgrades, and platform compatibility.

## 2025-12-17 - Stability and Risk Control Hardening

### Motivation
- Reduce unexpected trading behavior and emergency-stop gaps.
- Improve guardrails around order lifecycle and position handling.

### Key upgrades
- Added critical runtime safety fixes across trading path.
- Added emergency stop and risk check improvements.
- Normalized medium-priority reliability fixes documented in deployment notes.

### Impacted areas
- Legacy trading runtime (`scalper.py`, `monitor.py`, risk-related helpers).
- Deployment and verification docs under `docs/deployment/`.

---

## 2025-12-27 - Bug Fix Rollup and Dashboard Seed

### Motivation
- Consolidate production bug fixes and begin dashboard-focused observability.

### Key upgrades
- Applied bug-fix bundles and deployment follow-ups.
- Produced early dashboard deployment documentation.

### Impacted areas
- Runtime and reporting scripts.
- Documentation baseline under `docs/deployment/` and `docs/reports/`.

---

## 2026-01-10 to 2026-01-14 - Index Generalization + Windows Compatibility Refactor

### Motivation
- Generalize SPX-only assumptions to SPX/NDX workflows.
- Make runtime and paths stable on Windows environments.

### Key upgrades
- Introduced centralized index configuration and scaling semantics.
- Added cross-platform path helpers and runtime wrappers.
- Added Windows quickstart and script support.
- Reduced dependence on Linux-only operational flow.

### Impacted areas
- `index_config.py`
- `app/common/paths.py`
- `app/config/runtime.py`
- `scripts/windows/*`
- `docs/WINDOWS_QUICKSTART.md`

---

## 2026-02-07 - Schwab Read-Only Dashboard Architecture

### Motivation
- Move project center from execution-first to read-only intelligence board.
- Replace unavailable/unstable provider path with Schwab-native data path.

### Key upgrades
- Added Schwab provider and token refresh flow:
  - `app/providers/schwab_client.py`
- Added market snapshot service and local cache/history:
  - `app/services/market_snapshot_service.py`
- Added analytics layer for option chain flattening and GEX structure:
  - `app/analytics/gex_dashboard.py`
- Added local API server and dashboard frontend:
  - `app/api/dashboard_server.py`
  - `dashboard/index.html`
- Added dashboard entrypoint:
  - `run_dashboard.py`

### Impacted areas
- End-to-end runtime path from data fetch to visualization.
- Project usage pattern shifted to `run_dashboard.py` and `run_signal.py`.

---

## 2026-02-07 to 2026-02-08 - Strategy Visualization + Debug Observability

### Motivation
- Make strategy decision process visible and explainable in UI.
- Add diagnostics for slow refresh, missing strategy payloads, and API health.

### Key upgrades
- Embedded full strategy payload into snapshot/history:
  - `strategy.core`
  - `strategy.tradeable`
  - `strategy.checks`
  - `strategy.market_inputs`
  - `strategy.meta`
- Added bilingual strategy dashboard and decision-flow rendering.
- Added debug API endpoint:
  - `GET /api/dashboard/debug?index=SPX|NDX`
- Added structured runtime logging:
  - `data/logs/dashboard_server.log`
  - `data/logs/dashboard_error.log`
- Added slow-refresh warning events and service debug buffers.
- Added environment toggle for strategy fast mode:
  - `DASHBOARD_STRATEGY_FAST_MODE`

### Impacted areas
- `app/signals/engine.py`
- `app/services/market_snapshot_service.py`
- `app/api/dashboard_server.py`
- `dashboard/index.html`
- `run_dashboard.py`

---

## Current Architecture Snapshot (as of 2026-02-08)

- Data source: Schwab market data and option chain APIs.
- Runtime mode: read-only dashboard and signal inspection.
- Core API surface:
  - `/api/health`
  - `/api/dashboard/snapshot`
  - `/api/dashboard/history`
  - `/api/dashboard/debug`
- Legacy trading entrypoints are intentionally guarded/disabled in this build.

See also:
- `docs/history/FEATURE_CHANGELOG.md`
- `docs/architecture/ARCHITECTURE_CURRENT.md`
- `docs/STRATEGY_VISUAL_UPGRADE_SUMMARY.md`
