# Gamma GEX Scalper - 中文文档

> 基于 Gamma 暴露（GEX）的 0DTE 期权自动交易系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)](https://github.com)

---

## 🎯 项目简介

Gamma GEX Scalper 是一个自动化的 0DTE（当日到期）期权交易系统，利用期权市场的 Gamma 暴露效应进行交易。

### 核心策略

**GEX Pin 效应**: 期权市场的 Gamma 暴露会在特定价格点形成"引力"，价格倾向于向该点靠拢。

- 价格 > Pin → 卖出 Call Spread（看跌回归）
- 价格 < Pin → 卖出 Put Spread（看涨回归）
- 价格 ≈ Pin → 卖出 Iron Condor（中性）

### 性能表现

**1年回测结果**（$25,000 起始资金）:

| 指数 | 最终余额 | ROI | 胜率 | 盈亏比 |
|------|---------|-----|------|--------|
| **NDX** | $290,076 | **+1,060%** | 87.6% | 10.36 |
| **SPX** | $110,551 | +342% | 90.8% | 5.55 |

**NDX 收益是 SPX 的 3.1 倍** ⭐

---

## 📋 目录

- [快速开始](#快速开始)
- [系统要求](#系统要求)
- [安装配置](#安装配置)
- [使用方法](#使用方法)
- [文档导航](#文档导航)
- [常见问题](#常见问题)
- [风险提示](#风险提示)

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd gamma-gex-scalper-main
```

### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 3. 配置环境

```bash
# 创建配置文件
sudo nano /etc/gamma.env

# 添加 API 密钥（替换为你的实际密钥）
export TRADIER_SANDBOX_KEY="你的_Sandbox_密钥"
export TRADIER_LIVE_KEY="你的_Live_密钥"
export TRADIER_PAPER_ACCOUNT_ID="你的_Sandbox_账户ID"
export TRADIER_LIVE_ACCOUNT_ID="你的_Live_账户ID"

# 加载配置
source /etc/gamma.env
```

### 4. 运行模拟交易

```bash
# SPX 模拟交易
python3 scalper.py SPX PAPER

# NDX 模拟交易（推荐，收益更高）
python3 scalper.py NDX PAPER
```

### 5. 监控持仓

```bash
# 启动监控程序
python3 monitor.py PAPER
```

**详细步骤**: 参见 [docs/快速开始指南.md](docs/快速开始指南.md)

---

## 💻 系统要求

### 硬件要求

- **CPU**: 1 核心+
- **内存**: 2GB+
- **磁盘**: 10GB+（含数据库）
- **网络**: 稳定的互联网连接

### 软件要求

- **操作系统**: Linux (Ubuntu/Debian 推荐)
- **Python**: 3.8 或更高版本
- **数据库**: SQLite3（Python 自带）

### API 要求

1. **Tradier API** (必需)
   - 注册地址: https://tradier.com
   - 需要 Sandbox 和 Live 两个账户
   - 费用: 免费（需开户）

2. **Discord Webhook** (可选，推荐)
   - 用于接收交易提醒
   - 费用: 免费

3. **Healthcheck.io** (可选)
   - 用于系统监控
   - 费用: 免费套餐

---

## 🔧 安装配置

### Python 依赖

```bash
# 安装核心依赖
pip3 install yfinance pandas requests pytz

# 或使用 requirements.txt
pip3 install -r requirements.txt
```

### 环境变量配置

创建 `/etc/gamma.env` 文件：

```bash
# Tradier API 密钥
export TRADIER_SANDBOX_KEY="你的_Sandbox_密钥"
export TRADIER_LIVE_KEY="你的_Live_密钥"
export TRADIER_PAPER_ACCOUNT_ID="你的_Sandbox_账户ID"
export TRADIER_LIVE_ACCOUNT_ID="你的_Live_账户ID"

# Discord Webhook（可选）
export GAMMA_DISCORD_WEBHOOK_PAPER_URL="https://discord.com/api/webhooks/..."
export GAMMA_DISCORD_WEBHOOK_LIVE_URL="https://discord.com/api/webhooks/..."

# Healthcheck（可选）
export GAMMA_HEALTHCHECK_PAPER_URL="https://hc-ping.com/..."
export GAMMA_HEALTHCHECK_LIVE_URL="https://hc-ping.com/..."
```

加载配置：

```bash
source /etc/gamma.env
```

### 验证配置

```bash
# 检查环境变量
echo $TRADIER_SANDBOX_KEY

# 测试运行（不会实际下单）
python3 scalper.py SPX PAPER 6000 6050
```

---

## 📖 使用方法

### 基本命令

```bash
# 格式
python scalper.py <INDEX> [PAPER|LIVE] [pin_override] [price_override]

# 参数说明
# <INDEX>: 必需，SPX 或 NDX
# [PAPER|LIVE]: 可选，默认 PAPER（模拟）
# [pin_override]: 可选，覆盖 GEX Pin 价格（测试用）
# [price_override]: 可选，覆盖指数价格（测试用）
```

### 使用示例

```bash
# 1. SPX 模拟交易
python3 scalper.py SPX PAPER

# 2. NDX 模拟交易
python3 scalper.py NDX PAPER

# 3. SPX 实盘交易
python3 scalper.py SPX LIVE

# 4. NDX 实盘交易
python3 scalper.py NDX LIVE

# 5. 测试模式（带价格覆盖）
python3 scalper.py SPX PAPER 6000 6050
```

### 监控持仓

```bash
# 监控模拟持仓
python3 monitor.py PAPER

# 监控实盘持仓
python3 monitor.py LIVE
```

### 查看日志

```bash
# 交易记录
tail -20 data/trades.csv

# 监控日志
tail -50 data/monitor_paper.log

# 实时监控
tail -f data/monitor_paper.log
```

---

## 📚 文档导航

### 新手必读

1. **[快速开始指南](docs/快速开始指南.md)** ⭐
   - 完整的安装和运行步骤
   - 环境配置详解
   - 常见问题解答

2. **[项目总结](docs/项目总结.md)**
   - 项目概述和架构
   - 性能数据和回测结果
   - 学习路径建议

3. **[文件清理指南](docs/文件清理指南.md)**
   - 哪些文件可以删除
   - 如何整理项目目录
   - 文档分类规则

### 技术文档

4. **[README.md](README.md)** - 英文原版文档
5. **[START_HERE_2026_01_14.md](START_HERE_2026_01_14.md)** - 2026-01-14 部署总结
6. **[DEPLOYMENT_VALIDATION_2026_01_14.txt](DEPLOYMENT_VALIDATION_2026_01_14.txt)** - 部署验证

### 回测报告

7. **[COMPREHENSIVE_BACKTEST_FINAL_REPORT.txt](COMPREHENSIVE_BACKTEST_FINAL_REPORT.txt)** - 完整回测报告
8. **[5YEAR_BACKTEST_REPORT_2026-01-10.md](5YEAR_BACKTEST_REPORT_2026-01-10.md)** - 5年回测报告
9. **[MULTI_INDEX_COMPARISON_2026-01-10.md](MULTI_INDEX_COMPARISON_2026-01-10.md)** - 多指数对比

---

## 🗂️ 项目结构

```
gamma-gex-scalper-main/
├── README.md                    # 英文文档
├── README_CN.md                 # 中文文档（本文件）
├── requirements.txt             # Python 依赖
│
├── scalper.py                   # 主交易程序
├── monitor.py                   # 持仓监控
├── config.py                    # 环境配置
├── index_config.py              # 指数配置
│
├── autoscaling.py               # 仓位管理
├── decision_logger.py           # 决策日志
├── discord_autodelete.py        # Discord 通知
├── claude_anomaly_integration.py # AI 异常检测
├── market_veto_cache.py         # 市场过滤
│
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── gex_strategy.py          # GEX 策略逻辑
│   └── broken_wing_ic_calculator.py # BWIC 计算
│
├── data/                        # 数据目录
│   ├── orders_paper.json        # 模拟持仓
│   ├── orders_live.json         # 实盘持仓
│   ├── trades.csv               # 交易记录
│   └── *.log                    # 日志文件
│
└── docs/                        # 文档目录
    ├── 快速开始指南.md
    ├── 文件清理指南.md
    ├── 项目总结.md
    ├── guides/                  # 使用指南
    ├── reports/                 # 回测报告
    ├── analysis/                # 分析文档
    └── deployment/              # 部署文档
```

---

## ❓ 常见问题

### 1. 如何获取 Tradier API 密钥？

1. 访问 https://tradier.com 注册账户
2. 登录后进入 Settings → API Access
3. 创建 Sandbox 和 Live 两个 API Token
4. 复制密钥到 `/etc/gamma.env`

### 2. 为什么没有交易信号？

可能原因：
- VIX 太低（< 13）
- 不在交易时间（10:00-13:00 ET）
- RSI 超出范围（40-80）
- 市场波动太大

查看日志：
```bash
tail -50 data/monitor_paper.log | grep "SKIP"
```

### 3. 如何验证系统正常运行？

```bash
# 检查环境变量
echo $TRADIER_SANDBOX_KEY

# 检查优化参数
grep "CUTOFF_HOUR\|VIX_FLOOR" scalper.py

# 测试运行
python3 scalper.py SPX PAPER 6000 6050
```

### 4. 持仓没有自动平仓怎么办？

检查监控服务：
```bash
# 查看服务状态
sudo systemctl status gamma-monitor-paper

# 查看监控日志
journalctl -u gamma-monitor-paper -n 100

# 手动启动监控
python3 monitor.py PAPER
```

### 5. 如何整理项目文件？

运行整理脚本：
```bash
python3 organize_docs.py
```

或参考 [文件清理指南](docs/文件清理指南.md)

---

## ⚠️ 风险提示

### 市场风险

- **高波动性**: 0DTE 期权波动极大，可能快速亏损
- **历史表现**: 不代表未来收益
- **策略失效**: 市场异常时策略可能失效

### 技术风险

- **API 故障**: 可能导致无法交易或错过止损
- **网络中断**: 可能导致持仓失控
- **系统故障**: 需要定期监控和维护

### 资金管理建议

- **起始资金**: 建议 $25,000+
- **单笔风险**: 不超过账户的 2-5%
- **最大回撤**: 容忍度 < 20%
- **分散投资**: 不要全仓单一策略

### 使用建议

1. **先模拟后实盘**: 至少运行 2-4 周模拟交易
2. **小资金测试**: 实盘从小资金开始
3. **严格止损**: 不要手动干预止损
4. **定期复盘**: 每周回顾交易表现

---

## 📊 性能监控

### 关键指标

- **胜率目标**: 40-50%
- **盈亏比**: 2:1 以上
- **月收益**: 5-15%
- **最大回撤**: < 20%

### 监控命令

```bash
# 查看最近交易
tail -20 data/trades.csv

# 实时监控
watch -n 5 "tail -20 data/monitor_paper.log"

# 查看系统日志
journalctl -u gamma-monitor-paper -f
```

---

## 🔄 自动化运行

### 使用 Systemd

创建服务文件：

```bash
sudo nano /etc/systemd/system/gamma-monitor-paper.service
```

内容：

```ini
[Unit]
Description=Gamma GEX Monitor - Paper
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/gamma-gex-scalper-main
ExecStart=/usr/bin/python3 monitor.py PAPER
EnvironmentFile=/etc/gamma.env
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable gamma-monitor-paper
sudo systemctl start gamma-monitor-paper
sudo systemctl status gamma-monitor-paper
```

### 使用 Cron

```bash
crontab -e

# 添加定时任务（每30分钟）
0,30 9-15 * * 1-5 cd /path/to/gamma-gex-scalper-main && source /etc/gamma.env && python3 scalper.py NDX PAPER >> /var/log/gamma.log 2>&1
```

---

## 🛠️ 故障排除

### 401 错误（API 认证失败）

```bash
# 检查环境变量
echo $TRADIER_SANDBOX_KEY

# 重新加载
source /etc/gamma.env

# 验证 API
curl -H "Authorization: Bearer $TRADIER_SANDBOX_KEY" \
     "https://sandbox.tradier.com/v1/markets/quotes?symbols=SPY"
```

### 无法连接 API

```bash
# 检查网络
ping api.tradier.com

# 检查防火墙
sudo ufw status

# 测试 API
python3 -c "import requests; print(requests.get('https://api.tradier.com').status_code)"
```

### 数据库错误

```bash
# 检查数据库文件
ls -lh data/*.db

# 备份数据库
cp data/market_data.db data/market_data.db.backup

# 重建数据库（如果损坏）
rm data/market_data.db
python3 data_collector_enhanced.py --init
```

---

## 📞 获取帮助

### 查看日志

```bash
# 交易日志
tail -50 data/trades.csv

# 监控日志
tail -100 data/monitor_paper.log

# 系统日志
journalctl -u gamma-monitor-paper -n 100
```

### 调试模式

```bash
# 启用详细日志
export DEBUG=1
python3 scalper.py SPX PAPER

# 测试模式（不下单）
python3 scalper.py SPX PAPER 6000 6050
```

### 社区支持

- 查看项目文档
- 阅读常见问题
- 查看 GitHub Issues

---

## 📝 更新日志

### v1.0.0 (2026-01-14)

- ✅ 核心 GEX 策略实现
- ✅ SPX 和 NDX 支持
- ✅ 自动仓位管理
- ✅ 完整风险控制

### v1.1.0 (2026-01-14)

- ✅ 时间过滤优化
- ✅ VIX 下限提升
- ✅ RSI 强制执行
- ✅ BWIC 集成

---

## 📄 许可证

本项目仅供学习和研究使用。

### 免责声明

**期权交易风险极高，可能损失全部本金。使用本系统前请确保：**

1. 充分理解期权交易风险
2. 具备足够的风险承受能力
3. 不使用借贷资金交易
4. 做好可能损失全部本金的准备

**本项目不构成投资建议，作者不对任何损失负责。**

---

## 🌟 致谢

感谢所有为本项目做出贡献的开发者和测试者。

---

**创建日期**: 2026-02-06  
**最后更新**: 2026-02-06  
**版本**: 1.0  
**状态**: 生产就绪

**快速链接**:
- [快速开始指南](docs/快速开始指南.md)
- [项目总结](docs/项目总结.md)
- [文件清理指南](docs/文件清理指南.md)
