# Security: Secrets Rotation and GitHub Alert Response

This project uses API credentials via environment variables only.
Do not commit real keys, secrets, or tokens to Git.

## 1) Required Environment Variables

- `SCHWAB_CLIENT_ID`
- `SCHWAB_CLIENT_SECRET`
- `SCHWAB_REFRESH_TOKEN`
- `DATABENTO_API_KEY` (if using Databento tools)
- `TRADIER_LIVE_KEY` / `TRADIER_SANDBOX_KEY` (if using Tradier tools)
- `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` (if using Alpaca tools)

## 2) Local Setup (Windows PowerShell)

```powershell
$env:SCHWAB_CLIENT_ID="your_client_id"
$env:SCHWAB_CLIENT_SECRET="your_client_secret"
$env:SCHWAB_REFRESH_TOKEN="your_refresh_token"
```

Use a local `.env` file if needed. `.env` is ignored by Git.

## 3) If GitHub Secret Scanning Alerts Trigger

1. Revoke and rotate exposed credentials in provider consoles immediately.
2. Update local environment variables with new credentials.
3. Remove plaintext secrets from files (code + docs + scripts).
4. Rewrite Git history if secrets were committed before.
5. Force-push sanitized history.
6. Re-run secret scan locally before pushing.

## 4) Local Secret Scan Commands

```powershell
rg -n --hidden -P "\bdb-[A-Za-z0-9]{20,}\b|\bPK[A-Z0-9]{18,}\b|Bearer\s+[A-Za-z0-9_-]{20,}" .
rg -n --hidden -S "SCHWAB_CLIENT_SECRET=|SCHWAB_REFRESH_TOKEN=|TRADIER_LIVE_KEY=|APCA_API_SECRET_KEY="
```

No output means no current matches for these patterns.

## 5) Ongoing Best Practices

- Keep `.env.example` as placeholders only.
- Never paste full credentials in issues, PRs, or chat.
- Prefer short-lived tokens where supported.
- Rotate credentials periodically and after every suspected leak.
