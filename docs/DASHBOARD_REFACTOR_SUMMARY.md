# Dashboard Refactor Summary

Updated: 2026-02-07

## Refactor Goals

- Reposition the project toward a read-only market intelligence dashboard.
- Use Schwab as the primary data source for market and option-chain data.
- Keep legacy trading execution paths guarded/disabled by default.

## Added Capabilities

1. Schwab provider client
- `app/providers/schwab_client.py`

2. Snapshot service (cache + history)
- `app/services/market_snapshot_service.py`

3. Analytics layer (GEX and option structure metrics)
- `app/analytics/gex_dashboard.py`

4. Local API server
- `app/api/dashboard_server.py`

5. Dashboard UI
- `dashboard/index.html`

6. Dashboard runtime entrypoint
- `run_dashboard.py`

## Trading Path Handling

- `run_scalper.py`: disabled in this read-only build.
- `run_monitor.py`: disabled in this read-only build.
- `scalper.py` / `monitor.py`: guarded by legacy feature flag.

## Documentation Updated

- `README.md`
- `docs/WINDOWS_QUICKSTART.md`
- `docs/API_SETUP_GUIDE.md`
- `docs/SIGNAL_MODE_GUIDE.md`
- `.env.example`

## Runtime Command

```powershell
conda activate 111222
python run_dashboard.py
```

## Notes

- If Schwab credentials/token are invalid, `/api/health` and snapshot responses will show errors.
- To re-enable legacy trading paths explicitly, use:
  - `GAMMA_ENABLE_LEGACY_TRADING=1`
