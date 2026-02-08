# Feature Changelog

This is a consolidated changelog for major user-visible capabilities.
Format follows: Added / Changed / Fixed / Deprecated / Removed.

## 2026-02-08

### Added
- Dashboard debug endpoint:
  - `GET /api/dashboard/debug?index=SPX|NDX`
- Structured dashboard runtime logs:
  - `data/logs/dashboard_server.log`
  - `data/logs/dashboard_error.log`
- Slow-refresh warning events in snapshot service.

### Changed
- Dashboard UI is bilingual (Chinese-first + English technical terms).
- Dashboard now shows full strategy chain and debug panel by default.
- `.gitignore` hardened for logs, jsonl snapshots, temp artifacts, and runtime marker files.

### Fixed
- Improved operational traceability for refresh latency and strategy payload inspection.

---

## 2026-02-07

### Added
- Strategy payload integration in dashboard snapshots:
  - `strategy.core`
  - `strategy.tradeable`
  - `strategy.checks`
  - `strategy.market_inputs`
  - `strategy.meta`
- ECharts-based GEX and history visualization.
- Decision-flow rendering from strategy checks.
- Strategy fast mode toggle path in runtime.

### Changed
- Quote extraction updated to support nested Schwab quote structures.

### Fixed
- Cases where `market.spot` / `market.vix` were not surfaced to UI despite valid quote payload.

---

## 2026-01-14

### Added
- Windows quickstart and compatibility wrapper stack.
- Runtime path normalization for cross-platform execution.

### Changed
- Startup flow shifted toward wrapper entrypoints for safer cross-platform operation.

---

## 2026-01-10

### Added
- Index-agnostic configuration model for SPX/NDX behaviors.
- Improved strike and spread scaling by index profile.

### Changed
- Strategy parameterization moved toward centralized config patterns.

---

## 2025-12-27

### Fixed
- Bug fix rollup across runtime and deployment path.
- Additional deployment validation and backtest consistency checks.

---

## 2025-12-17

### Fixed
- Critical reliability and emergency stop paths in legacy trading stack.
- Medium-level safeguards and operational guardrails.

---

## Notes
- This changelog captures major milestones and is intentionally concise.
- Detailed raw evidence remains in `docs/deployment/`, `docs/reports/`, and `docs/analysis/`.
