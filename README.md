# Gamma Dashboard (Schwab, Read-Only)

This repository is now focused on a **read-only options information dashboard**:
- Schwab market data + option chain ingestion
- GEX/pin structure analytics
- Local web dashboard for monitoring
- Signal CLI for quick terminal checks

Trading execution is intentionally disabled in this build.

## Quick Start

```powershell
conda create -n 111222 python=3.11 -y
conda activate 111222
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env`:
- `SCHWAB_CLIENT_ID`
- `SCHWAB_CLIENT_SECRET`
- `SCHWAB_REFRESH_TOKEN`

Run dashboard:
```powershell
python run_dashboard.py
```

Open:
- `http://127.0.0.1:8787/`

## Signal CLI

```powershell
python run_signal.py SPX --watch --interval 15
```

## Key Files

- `run_dashboard.py`: dashboard entrypoint
- `app/providers/schwab_client.py`: Schwab API client
- `app/services/market_snapshot_service.py`: snapshot/cache/history service
- `app/analytics/gex_dashboard.py`: analytics and GEX computation
- `app/api/dashboard_server.py`: local HTTP API server
- `dashboard/index.html`: frontend dashboard

## Architecture and History

- Current architecture:
  - `docs/architecture/ARCHITECTURE_CURRENT.md`
- Upgrade history index:
  - `docs/history/INDEX.md`
- Architecture upgrade timeline:
  - `docs/history/ARCH_UPGRADE_HISTORY.md`
- Feature changelog:
  - `docs/history/FEATURE_CHANGELOG.md`
- Optimization roadmap:
  - `docs/PROJECT_OPTIMIZATION_RECOMMENDATIONS.md`

## Legacy Trading Status

- `run_scalper.py` and `run_monitor.py` are disabled.
- `scalper.py` and `monitor.py` are guarded by `GAMMA_ENABLE_LEGACY_TRADING=1`.

## Runtime and Debug APIs

- `GET /api/health`
- `GET /api/dashboard/snapshot?index=SPX|NDX`
- `GET /api/dashboard/history?index=SPX|NDX&limit=120`
- `GET /api/dashboard/debug?index=SPX|NDX`
