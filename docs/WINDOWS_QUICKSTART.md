# Windows Quickstart (Schwab Read-Only Dashboard)

## 1) Prerequisites
- Windows 10/11
- Conda
- Python 3.11
- Schwab Developer API credentials

## 2) Setup
1. Create and activate conda environment:
   ```powershell
   conda create -n 111222 python=3.11 -y
   conda activate 111222
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Copy env template:
   ```powershell
   copy .env.example .env
   ```
4. Fill required variables in `.env`:
   - `SCHWAB_CLIENT_ID`
   - `SCHWAB_CLIENT_SECRET`
   - `SCHWAB_REFRESH_TOKEN`

## 3) Run Dashboard
```powershell
conda activate 111222
python run_dashboard.py
```

Default URL:
- `http://127.0.0.1:8787/`

## 4) Optional Read-Only Signal CLI
```powershell
python run_signal.py SPX --watch --interval 15
python run_signal.py NDX --json
```

## 5) Data & Logs
- Dashboard snapshots:
  - `data\dashboard_snapshots_spx_YYYYMMDD.jsonl`
  - `data\dashboard_snapshots_ndx_YYYYMMDD.jsonl`
- Generic runtime path: `data\`

## 6) Important Notes
- This build is **read-only** and does **not** place orders.
- `run_scalper.py` and `run_monitor.py` are intentionally disabled.
