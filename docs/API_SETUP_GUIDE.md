# API Setup Guide (Schwab Dashboard)

更新时间：2026-02-07  
适用：本仓库当前版本（只读信息看板）

## 1. 必需 API 变量

在 `.env` 中配置：

1. `SCHWAB_CLIENT_ID`
2. `SCHWAB_CLIENT_SECRET`
3. `SCHWAB_REFRESH_TOKEN`

可选：
- `SCHWAB_ACCESS_TOKEN`（临时调试用）

## 2. 获取流程（简版）

1. 登录 Schwab Developer Portal。
2. 创建应用并获取 client id / client secret。
3. 按官方 OAuth 流程拿到 refresh token。
4. 写入 `.env`，启动：
   ```powershell
   python run_dashboard.py
   ```

## 3. 常见错误

1. `401 invalid_token`
- 原因：access token 过期或无效。
- 处理：确认 `SCHWAB_REFRESH_TOKEN` 可用，且 client id/secret 正确。

2. `token refresh failed`
- 原因：refresh token 失效或应用权限不匹配。
- 处理：重新走授权流程刷新 token。

3. 看板打开但无数据
- 原因：API 调用失败或被限流。
- 处理：查看 `/api/health` 返回中的 `last_error`。

## 4. 运行时变量（可选）

- `DASHBOARD_REFRESH_SECONDS`（默认 12）
- `DASHBOARD_HOST`（默认 `127.0.0.1`）
- `DASHBOARD_PORT`（默认 `8787`）

## 5. 说明

- 本仓库当前版本仅提供 **read-only 信息看板**。
- 不执行下单、平仓或任何交易动作。
