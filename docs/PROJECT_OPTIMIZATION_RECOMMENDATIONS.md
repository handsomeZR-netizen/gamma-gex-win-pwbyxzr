# Project Optimization Recommendations

Date: 2026-02-08
Scope: Engineering structure, runtime reliability, and maintainability.

## Priority P0 (Immediate)

1. Repository script consolidation
- Problem: root directory contains many one-off scripts, reducing discoverability.
- Action:
  - keep only canonical entrypoints at root (`run_dashboard.py`, `run_signal.py`, `README.md`, `requirements.txt`)
  - migrate historical/analysis/backtest helpers into categorized `scripts/*`
- Success criteria:
  - root file count materially reduced
  - no regression for dashboard startup

2. API contract stabilization tests
- Problem: dashboard depends on nested JSON fields; shape drift can silently break UI.
- Action:
  - add schema checks for `/api/dashboard/snapshot` and `/api/dashboard/debug`
  - assert required keys and type expectations
- Success criteria:
  - contract tests pass in CI/local pre-push

3. Documentation entrypoint normalization
- Problem: docs are rich but fragmented.
- Action:
  - maintain `docs/history/INDEX.md` and architecture doc as primary source
  - ensure README links only to maintained docs first
- Success criteria:
  - newcomers can run and troubleshoot within one guided path

## Priority P1 (Near-Term)

1. Snapshot latency governance
- Add percentile tracking (`p50/p95`) for refresh time.
- Emit warning thresholds per index profile.

2. Strategy explainability enrichment
- Add normalized score fields (signal strength / risk grade).
- Keep existing `checks` semantics backward compatible.

3. Dashboard performance tuning
- Avoid refetch overlap when previous refresh still in-flight.
- Add stale-data badge when refresh exceeds interval.

## Priority P2 (Mid-Term)

1. Packaging and CLI modernization
- Convert ad-hoc scripts to `python -m` subcommands.
- Introduce a small command registry for analysis/backtest tools.

2. Data lifecycle policy
- Add retention policy for `data/*.jsonl` snapshots and logs.
- Add archival utility with date window controls.

3. CI baseline
- Add lint + compile + contract-test stage.
- Add smoke test for `run_dashboard.py` boot path.

## Deferred / Optional

- Split dashboard frontend into dedicated React/Vite app (if customization speed becomes bottleneck).
- Introduce typed schema layer for API payload generation.

## Notes
- Recommendations are ordered for minimal disruption to the current read-only dashboard path.
- Focus remains on maintainability and operator confidence rather than feature explosion.
