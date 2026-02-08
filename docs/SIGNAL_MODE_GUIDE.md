# Signal Mode Guide (Schwab Read-Only)

更新时间：2026-02-07

## 1. 目标

`run_signal.py` 提供一个只读信号输出：
- 读取 Schwab 市场数据与期权链
- 输出 GEX 结构与观察结论
- 不做任何交易操作

## 2. 命令

```powershell
# 单次输出
python run_signal.py SPX

# 持续模式（每 15 秒）
python run_signal.py SPX --watch --interval 15

# JSON 模式
python run_signal.py NDX --json
```

## 3. 输出内容

- 指数现价、VIX
- GEX Pin 与距离
- 方向偏向（bias）
- 观察结论（observation）
- PCR（OI/Volume）等统计

## 4. 依赖变量

必需：
- `SCHWAB_CLIENT_ID`
- `SCHWAB_CLIENT_SECRET`
- `SCHWAB_REFRESH_TOKEN`

## 5. 说明

- 此模式仅用于信息观察与研究。
- 不包含下单/平仓能力。
