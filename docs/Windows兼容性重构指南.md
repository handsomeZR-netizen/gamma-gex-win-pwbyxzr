# Windows 兼容性重构指南

## 📊 可行性评估

### 总体评估：✅ **高度可行**

**难度等级**: ⭐⭐☆☆☆ (中等偏易)  
**预计工作量**: 2-4 小时  
**成功率**: 95%+

---

## 🔍 需要修改的部分

### 1. 文件锁定机制（核心问题）

**当前问题**:
```python
import fcntl  # ❌ Linux 专用，Windows 不支持

fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
```

**解决方案**: 使用 `filelock` 库（跨平台）

```python
from filelock import FileLock, Timeout  # ✅ 跨平台

lock = FileLock(LOCK_FILE, timeout=0)
try:
    with lock.acquire(blocking=False):
        # 执行交易逻辑
        pass
except Timeout:
    print("另一个实例正在运行")
    exit(0)
```

**优势**:
- ✅ Windows/Linux/macOS 全平台支持
- ✅ API 更简洁
- ✅ 自动清理锁文件
- ✅ 更好的异常处理

---

### 2. 文件路径（次要问题）

**当前问题**:
```python
GAMMA_HOME = '/root/gamma'  # ❌ Linux 硬编码路径
TRADE_LOG_FILE = f"{GAMMA_HOME}/data/trades.csv"
```

**解决方案**: 使用 `pathlib`（Python 标准库）

```python
from pathlib import Path

# 自动适配 Windows/Linux
GAMMA_HOME = Path(os.environ.get('GAMMA_HOME', Path.home() / 'gamma'))
TRADE_LOG_FILE = GAMMA_HOME / 'data' / 'trades.csv'

# Windows: C:\Users\用户名\gamma\data\trades.csv
# Linux: /home/用户名/gamma/data/trades.csv
```

**优势**:
- ✅ 自动处理路径分隔符（Windows `\` vs Linux `/`）
- ✅ 更安全的路径拼接
- ✅ 跨平台兼容

---

### 3. 环境变量配置（次要问题）

**当前问题**:
```bash
# Linux: /etc/gamma.env
export TRADIER_SANDBOX_KEY="..."
```

**解决方案**: 使用 `.env` 文件 + `python-dotenv`

```python
# 安装: pip install python-dotenv
from dotenv import load_dotenv

# 加载 .env 文件（Windows/Linux 通用）
load_dotenv()

# 读取环境变量
TRADIER_SANDBOX_KEY = os.getenv("TRADIER_SANDBOX_KEY")
```

**配置文件** (`.env`):
```bash
# Windows 和 Linux 都支持
TRADIER_SANDBOX_KEY=你的密钥
TRADIER_LIVE_KEY=你的密钥
TRADIER_PAPER_ACCOUNT_ID=账户ID
TRADIER_LIVE_ACCOUNT_ID=账户ID
```

---

### 4. 系统服务（可选）

**当前问题**:
```bash
# Linux: systemd
sudo systemctl start gamma-monitor-paper
```

**Windows 解决方案**:

#### 方案 A: Windows 任务计划程序（推荐）
```powershell
# 创建定时任务
schtasks /create /tn "GammaScalper" /tr "python C:\gamma\scalper.py NDX PAPER" /sc minute /mo 30 /st 09:00 /et 16:00
```

#### 方案 B: NSSM (Non-Sucking Service Manager)
```powershell
# 安装 NSSM
choco install nssm

# 创建 Windows 服务
nssm install GammaMonitor "C:\Python39\python.exe" "C:\gamma\monitor.py PAPER"
nssm start GammaMonitor
```

#### 方案 C: Python 脚本 + 启动文件夹
```python
# startup.py - 放到启动文件夹
import subprocess
subprocess.Popen(['python', 'C:\\gamma\\monitor.py', 'PAPER'])
```

---

## 🛠️ 具体重构步骤

### 步骤 1: 安装跨平台依赖

```bash
pip install filelock python-dotenv
```

更新 `requirements.txt`:
```txt
# 原有依赖
yfinance>=0.2.28
pandas>=1.5.0
requests>=2.28.0
pytz>=2022.7

# 新增跨平台依赖
filelock>=3.12.0        # 跨平台文件锁
python-dotenv>=1.0.0    # 环境变量管理
```

---

### 步骤 2: 修改 `scalper.py`

#### 2.1 替换导入

```python
# 原代码（第 24 行）
import datetime, requests, json, csv, pytz, time, math, fcntl, tempfile

# 修改为
import datetime, requests, json, csv, pytz, time, math, tempfile
from filelock import FileLock, Timeout  # 新增
from pathlib import Path  # 新增
from dotenv import load_dotenv  # 新增
```

#### 2.2 修改路径配置

```python
# 原代码（第 13 行）
GAMMA_HOME = os.environ.get('GAMMA_HOME', '/root/gamma')

# 修改为
load_dotenv()  # 加载 .env 文件
GAMMA_HOME = Path(os.environ.get('GAMMA_HOME', Path.home() / 'gamma'))

# 确保目录存在
(GAMMA_HOME / 'data').mkdir(parents=True, exist_ok=True)
```

#### 2.3 修改文件路径

```python
# 原代码
TRADE_LOG_FILE = f"{GAMMA_HOME}/data/trades.csv"
LOCK_FILE = f"/tmp/gexscalper_{INDEX_CONFIG.code.lower()}_{mode.lower()}.lock"

# 修改为
TRADE_LOG_FILE = GAMMA_HOME / 'data' / 'trades.csv'
LOCK_FILE = GAMMA_HOME / 'locks' / f"gexscalper_{INDEX_CONFIG.code.lower()}_{mode.lower()}.lock"

# 确保 locks 目录存在
(GAMMA_HOME / 'locks').mkdir(parents=True, exist_ok=True)
```

#### 2.4 替换文件锁定逻辑

```python
# 原代码（第 374-395 行）
lock_fd = None
try:
    lock_fd = open(LOCK_FILE, 'w')
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock_fd.write(f"{os.getpid()}\n")
    lock_fd.flush()
    log(f"Lock acquired (PID: {os.getpid()})")
except BlockingIOError:
    log("Lock held by another instance — exiting")
    if lock_fd:
        lock_fd.close()
    exit(0)

# 修改为
lock = FileLock(str(LOCK_FILE), timeout=0)
try:
    lock.acquire(blocking=False)
    log(f"Lock acquired (PID: {os.getpid()})")
except Timeout:
    log("Lock held by another instance — exiting")
    exit(0)
```

#### 2.5 修改锁释放逻辑

```python
# 原代码（第 2359-2363 行）
if 'lock_fd' in globals() and lock_fd is not None:
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
    except Exception as unlock_err:
        log(f"Warning: Error unlocking: {unlock_err}")

# 修改为
if 'lock' in globals() and lock is not None:
    try:
        lock.release()
    except Exception as unlock_err:
        log(f"Warning: Error unlocking: {unlock_err}")
```

---

### 步骤 3: 修改 `monitor.py`

同样的修改应用到 `monitor.py`:

1. 替换 `fcntl` 为 `filelock`
2. 使用 `pathlib.Path` 处理路径
3. 加载 `.env` 文件

---

### 步骤 4: 创建 `.env` 配置文件

在项目根目录创建 `.env`:

```bash
# Tradier API 配置
TRADIER_SANDBOX_KEY=你的_Sandbox_密钥
TRADIER_LIVE_KEY=你的_Live_密钥
TRADIER_PAPER_ACCOUNT_ID=你的_Sandbox_账户ID
TRADIER_LIVE_ACCOUNT_ID=你的_Live_账户ID

# Discord Webhook（可选）
GAMMA_DISCORD_WEBHOOK_PAPER_URL=https://discord.com/api/webhooks/...
GAMMA_DISCORD_WEBHOOK_LIVE_URL=https://discord.com/api/webhooks/...

# Healthcheck（可选）
GAMMA_HEALTHCHECK_PAPER_URL=https://hc-ping.com/...
GAMMA_HEALTHCHECK_LIVE_URL=https://hc-ping.com/...

# 项目路径（可选，默认为用户主目录下的 gamma）
# Windows: GAMMA_HOME=C:\Users\你的用户名\gamma
# Linux: GAMMA_HOME=/home/你的用户名/gamma
```

---

### 步骤 5: 创建 Windows 启动脚本

#### `start_scalper.bat`

```batch
@echo off
cd /d %~dp0
python scalper.py NDX PAPER
pause
```

#### `start_monitor.bat`

```batch
@echo off
cd /d %~dp0
python monitor.py PAPER
pause
```

#### `start_all.bat`（同时启动）

```batch
@echo off
cd /d %~dp0
start "Gamma Scalper" python scalper.py NDX PAPER
start "Gamma Monitor" python monitor.py PAPER
```

---

## 📝 完整的重构代码示例

### `scalper_windows_compatible.py` (核心修改)

```python
#!/usr/bin/env python3
"""
Gamma GEX Scalper - Windows 兼容版本
支持 Windows/Linux/macOS
"""

import sys
import os
import warnings
import logging
from pathlib import Path

# 加载环境变量（跨平台）
from dotenv import load_dotenv
load_dotenv()

# 配置基础目录（跨平台）
GAMMA_HOME = Path(os.environ.get('GAMMA_HOME', Path.home() / 'gamma'))

# 确保必要目录存在
(GAMMA_HOME / 'data').mkdir(parents=True, exist_ok=True)
(GAMMA_HOME / 'locks').mkdir(parents=True, exist_ok=True)

# 配置日志
logging.captureWarnings(True)
yfinance_logger = logging.getLogger('py.warnings')
yfinance_handler = logging.FileHandler(GAMMA_HOME / 'data' / 'yfinance_warnings.log')
yfinance_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
yfinance_logger.addHandler(yfinance_handler)
yfinance_logger.setLevel(logging.WARNING)

# 标准库导入
import datetime
import requests
import json
import csv
import pytz
import time
import math
import tempfile

# 第三方库导入
import yfinance as yf
import pandas as pd
from filelock import FileLock, Timeout  # 跨平台文件锁

# 项目模块导入
from decision_logger import DecisionLogger
from claude_anomaly_integration import should_block_trading
from autoscaling import calculate_position_size, get_max_risk_for_strategy
from config import (
    PAPER_ACCOUNT_ID, LIVE_ACCOUNT_ID, 
    TRADIER_LIVE_KEY, TRADIER_SANDBOX_KEY,
    DISCORD_ENABLED, DISCORD_WEBHOOK_LIVE_URL, DISCORD_WEBHOOK_PAPER_URL,
    DISCORD_DELAYED_ENABLED, DISCORD_DELAYED_WEBHOOK_URL, DISCORD_DELAY_SECONDS
)
from index_config import get_index_config, get_supported_indices
from core.gex_strategy import get_gex_trade_setup as core_get_gex_trade_setup
from core.broken_wing_ic_calculator import BrokenWingICCalculator

# ==================== 配置 ====================

# 文件路径（跨平台）
TRADE_LOG_FILE = GAMMA_HOME / 'data' / 'trades.csv'

# 时区配置
ET = pytz.timezone('US/Eastern')
CUTOFF_HOUR = 13

# ==================== 参数解析 ====================

if len(sys.argv) < 2:
    print("ERROR: Index parameter required")
    print(f"Usage: python scalper.py <INDEX> [PAPER|LIVE] [pin_override] [price_override]")
    print(f"Supported indices: {', '.join(get_supported_indices())}")
    sys.exit(1)

index_arg = sys.argv[1].upper()
try:
    INDEX_CONFIG = get_index_config(index_arg)
    print(f"Trading index: {INDEX_CONFIG.name} ({INDEX_CONFIG.code})")
except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

mode = "PAPER"
if len(sys.argv) > 2:
    arg2 = sys.argv[2].upper()
    if arg2 in ["REAL", "LIVE"]:
        mode = "REAL"
    elif arg2 == "PAPER":
        mode = "PAPER"

pin_override = None
price_override = None
dry_run = False

if len(sys.argv) > 3 and sys.argv[3]:
    try:
        pin_override = float(sys.argv[3])
        dry_run = True
    except (ValueError, TypeError):
        pass

if len(sys.argv) > 4 and sys.argv[4]:
    try:
        price_override = float(sys.argv[4])
        dry_run = True
    except (ValueError, TypeError):
        pass

# API 配置
TRADIER_ACCOUNT_ID = LIVE_ACCOUNT_ID if mode == "REAL" else PAPER_ACCOUNT_ID
TRADIER_KEY = TRADIER_LIVE_KEY if mode == "REAL" else TRADIER_SANDBOX_KEY
BASE_URL = "https://api.tradier.com/v1/" if mode == "REAL" else "https://sandbox.tradier.com/v1/"
HEADERS = {"Accept": "application/json", "Authorization": f"Bearer {TRADIER_KEY}"}

# Discord 配置
DISCORD_WEBHOOK_URL = DISCORD_WEBHOOK_LIVE_URL if mode == "REAL" else DISCORD_WEBHOOK_PAPER_URL

# 锁文件路径（跨平台）
LOCK_FILE = GAMMA_HOME / 'locks' / f"gexscalper_{INDEX_CONFIG.code.lower()}_{mode.lower()}.lock"

print("=" * 70)
print(f"Index: {INDEX_CONFIG.name} ({INDEX_CONFIG.code})")
print(f"{'LIVE TRADING MODE — REAL MONEY' if mode == 'REAL' else 'PAPER TRADING MODE — 100% SAFE'}")
print(f"Using account: {TRADIER_ACCOUNT_ID}")
print(f"Home directory: {GAMMA_HOME}")
if dry_run:
    print("DRY RUN — NO ORDERS WILL BE SENT")
if pin_override:
    print(f"PIN OVERRIDE: {pin_override}")
if price_override:
    print(f"PRICE OVERRIDE: {price_override}")
print("=" * 70)

def log(msg):
    print(f"[{datetime.datetime.now(ET).strftime('%H:%M:%S')}] {msg}")

# ==================== 文件锁定（跨平台）====================

log(f"Scalper starting... (lock file: {LOCK_FILE})")

# 使用 filelock 替代 fcntl（跨平台）
lock = FileLock(str(LOCK_FILE), timeout=0)
try:
    lock.acquire(blocking=False)
    log(f"Lock acquired (PID: {os.getpid()})")
except Timeout:
    log("Lock held by another instance — exiting")
    exit(0)

# ==================== 主逻辑 ====================

try:
    now_et = datetime.datetime.now(ET)
    
    # 时间检查
    if now_et.hour >= CUTOFF_HOUR:
        log(f"Time is {now_et.strftime('%H:%M')} ET — past {CUTOFF_HOUR}:00 PM cutoff. NO NEW TRADES.")
        raise SystemExit
    
    log("GEX Scalper started")
    
    # ... 其余交易逻辑保持不变 ...
    
except SystemExit:
    pass
except KeyboardInterrupt:
    log("Interrupted by user")
except Exception as e:
    log(f"FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # 释放锁（跨平台）
    if 'lock' in globals() and lock is not None:
        try:
            lock.release()
            log("Lock released")
        except Exception as unlock_err:
            log(f"Warning: Error unlocking: {unlock_err}")
```

---

## 🧪 测试步骤

### 1. Windows 测试

```powershell
# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件
notepad .env

# 测试运行
python scalper.py SPX PAPER 6000 6050

# 测试锁定机制（打开两个终端）
# 终端 1
python scalper.py SPX PAPER

# 终端 2（应该立即退出）
python scalper.py SPX PAPER
```

### 2. Linux 测试

```bash
# 安装依赖
pip3 install -r requirements.txt

# 创建 .env 文件
nano .env

# 测试运行
python3 scalper.py SPX PAPER 6000 6050

# 测试锁定机制
python3 scalper.py SPX PAPER &
python3 scalper.py SPX PAPER  # 应该立即退出
```

---

## 📊 兼容性对比

| 功能 | 原版 (Linux) | 重构版 (跨平台) |
|------|-------------|----------------|
| 文件锁定 | `fcntl` ❌ | `filelock` ✅ |
| 路径处理 | 硬编码 `/root/` ❌ | `pathlib` ✅ |
| 环境变量 | `/etc/gamma.env` ❌ | `.env` 文件 ✅ |
| 系统服务 | `systemd` ❌ | 任务计划程序 ✅ |
| Python 版本 | 3.8+ ✅ | 3.8+ ✅ |
| 依赖库 | 全部跨平台 ✅ | 全部跨平台 ✅ |

---

## ⚠️ 注意事项

### 1. 性能差异

- **Windows**: 文件 I/O 略慢于 Linux（~5-10%）
- **影响**: 可忽略（交易频率低）

### 2. 路径长度限制

- **Windows**: 路径最大 260 字符（可通过注册表解除）
- **建议**: 使用短路径（如 `C:\gamma`）

### 3. 权限问题

- **Windows**: 不需要 `sudo`
- **Linux**: 某些操作可能需要 `sudo`

### 4. 时区处理

- **Windows**: 确保系统时区正确
- **Linux**: 通常默认 UTC

---

## 🎯 总结

### 可行性：✅ **非常高**

**原因**:
1. ✅ 核心依赖（yfinance, pandas, requests）全部跨平台
2. ✅ 唯一的 Linux 特定代码（`fcntl`）有成熟的跨平台替代方案
3. ✅ 路径问题可通过 `pathlib` 轻松解决
4. ✅ 环境变量可通过 `.env` 文件统一管理

### 工作量：⭐⭐☆☆☆

**预计时间**: 2-4 小时

**任务分解**:
- 安装依赖: 10 分钟
- 修改 `scalper.py`: 60 分钟
- 修改 `monitor.py`: 30 分钟
- 创建 `.env` 和启动脚本: 20 分钟
- 测试验证: 60 分钟

### 风险：⭐☆☆☆☆ (极低)

**原因**:
- `filelock` 是成熟的跨平台库（GitHub 2.5k+ stars）
- `pathlib` 是 Python 标准库
- 修改不涉及核心交易逻辑

---

## 📚 参考资源

### 文档

- [filelock 官方文档](https://py-filelock.readthedocs.io/)
- [pathlib 官方文档](https://docs.python.org/3/library/pathlib.html)
- [python-dotenv 文档](https://pypi.org/project/python-dotenv/)

### 示例项目

- [跨平台 Python 项目最佳实践](https://github.com/navdeep-G/samplemod)

---

**创建日期**: 2026-02-06  
**评估结论**: ✅ 高度可行，建议重构  
**预计收益**: 支持 Windows 用户，扩大用户群
