# Cleanup Manifest

## Kept
- Trading/runtime core:
  - `scalper.py`
  - `monitor.py`
  - `autoscaling.py`
  - `decision_logger.py`
  - `market_veto_cache.py`
  - `core/`
  - `index_config.py`
- Collector core:
  - `gex_blackbox_recorder.py`
  - `gex_blackbox_service.py`
  - `gex_blackbox_service_v2.py`
  - `gex_blackbox_continuous_collector.py`
- Backtests:
  - all `backtest_*.py`

## Added
- Cross-platform runtime helpers:
  - `app/common/paths.py`
  - `app/common/filelock.py`
  - `app/config/runtime.py`
- New entry scripts:
  - `run_scalper.py`
  - `run_monitor.py`
  - `run_blackbox_recorder.py`
  - `run_backtest.py`
- Windows scripts:
  - `scripts/windows/*.ps1`
- Env template:
  - `.env.example`

## Archived / Relocated
- Linux service/setup scripts moved to:
  - `scripts/linux_legacy/`
- Historical artifacts moved to:
  - `archive_legacy/artifacts/`

## Deferred
- Full migration of all non-backtest analysis helpers (`analyze_*`, `generate_*`, `show_*`) into modular CLI.
- Physical deletion of archived files after burn-in period.

