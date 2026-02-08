# Current Architecture

Last updated: 2026-02-08

## 1. Runtime Purpose

The project is currently centered on a read-only options intelligence workflow:
- Fetch market and option-chain data from Schwab.
- Compute GEX structure and strategy context.
- Serve local dashboard APIs.
- Render interactive dashboard with strategy decision flow and debug diagnostics.

Trading execution paths exist historically but are not the primary runtime in this build.

## 2. High-Level Data Flow

1. `run_dashboard.py`
- Loads environment.
- Creates `SchwabClient`.
- Creates `MarketSnapshotService`.
- Starts local HTTP server.

2. `app/providers/schwab_client.py`
- Handles OAuth token refresh and authenticated API requests.
- Fetches quotes and option chain.

3. `app/services/market_snapshot_service.py`
- Refreshes snapshot from provider.
- Enriches snapshot with analytics and strategy payload.
- Stores in-memory cache and jsonl history.
- Emits structured service logs and debug events.

4. `app/analytics/gex_dashboard.py`
- Flattens option chain.
- Computes option summaries.
- Computes GEX pin/walls/top levels.
- Builds dashboard snapshot section.

5. `app/signals/engine.py`
- Produces strategy payload:
  - `core` setup
  - `tradeable` decision
  - `checks` filter chain

6. `app/api/dashboard_server.py`
- Exposes local endpoints:
  - `/api/health`
  - `/api/dashboard/snapshot`
  - `/api/dashboard/history`
  - `/api/dashboard/debug`

7. `dashboard/index.html`
- Fetches APIs on interval.
- Renders metrics, decision flow, history charts, and debug panel.

## 3. Core Interfaces

### Snapshot Contract (`/api/dashboard/snapshot`)

Top-level blocks:
- `index`
- `market`
- `options`
- `gex`
- `signals` (lightweight summary)
- `strategy` (full decision context)
- `system`

### Strategy Contract

- `strategy.core`
- `strategy.tradeable`
- `strategy.checks`
- `strategy.market_inputs`
- `strategy.meta`

## 4. Observability

### Runtime Logs

- Success/slow/failure events:
  - `data/logs/dashboard_server.log`
- Error-level events:
  - `data/logs/dashboard_error.log`

### Debug API

- `/api/dashboard/debug`
- Exposes service state, recent events/errors, snapshot summary, and log file pointers.

## 5. Operational Modes

### Fast mode (default)

- Controlled by `DASHBOARD_STRATEGY_FAST_MODE` (default true).
- Keeps dashboard refresh latency stable by skipping expensive external volatility checks in UI-oriented flow.

### Strict mode

- Set `DASHBOARD_STRATEGY_FAST_MODE=0`.
- Enables full external checks in tradeability pipeline for deeper diagnostics.

## 6. Known Improvement Areas

- Script sprawl at repository root still high; continue migration into categorized `scripts/*`.
- Documentation is rich but fragmented; maintain history index discipline.
- Add automated API contract tests for snapshot/debug payload shape.
