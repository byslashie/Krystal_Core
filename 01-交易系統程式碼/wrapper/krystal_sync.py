# -*- coding: utf-8 -*-
"""
krystal_sync.py - ASCII path wrapper for Yuanta sync
Placed at C:/Users/jrenw/ to avoid Chinese path issues in Windows Task Scheduler
"""
import subprocess
import sys
from pathlib import Path

PROJECT = Path("C:/Projects/Krystal_完整系統/01-交易系統程式碼")
PYTHON64 = r"C:\Users\krystalchen\AppData\Local\Programs\Python\Python311\python.exe"
PYTHON32 = str(PROJECT / ".venv_yuanta32/Scripts/python.exe")
SYNC_SCRIPT  = str(PROJECT / "brokers/sync_yuanta_positions.py")
UPLOAD_SCRIPT = str(PROJECT / "brokers/upload_yuanta_to_sheets.py")

import logging
from datetime import datetime

log_path = PROJECT / "logs" / f"yuanta_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_path.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger()

# ── 台股交易日判斷 ──────────────────────────────────────────
def is_tw_trading_day() -> bool:
    try:
        import exchange_calendars as xcals
        cal = xcals.get_calendar("XTAI")
        today = datetime.now().strftime("%Y-%m-%d")
        return cal.is_session(today)
    except Exception:
        return True  # 無法判斷時預設繼續執行

today_str = datetime.now().strftime("%Y-%m-%d")
if not is_tw_trading_day():
    log.info(f"=== {today_str} 台股休市，跳過同步 ===")
    sys.path.insert(0, str(PROJECT))
    try:
        from modules.notifier import notify_sync_event
        notify_sync_event("元大同步", f"{today_str} 台股休市，今日跳過", ok=True)
    except Exception:
        pass
    sys.exit(0)

log.info("=== 元大庫存同步開始 ===")

# Step 1: 32-bit Python 抓庫存
step1_ok = False
import os
if os.path.exists(PYTHON32) and os.path.exists(SYNC_SCRIPT):
    log.info("[Step1] 32-bit 抓庫存...")
    try:
        r = subprocess.run(
            [PYTHON32, SYNC_SCRIPT],
            cwd=str(PROJECT),
            capture_output=True, text=True, timeout=180
        )
        log.info(r.stdout[-2000:] if r.stdout else "")
        if r.stderr:
            log.info("[stderr] " + r.stderr[-500:])
        log.info(f"[Step1] RC={r.returncode}")
        step1_ok = (r.returncode == 0)
    except subprocess.TimeoutExpired:
        log.info("[Step1] 超時（180s），跳過，使用現有 snapshot")
    except Exception as e:
        log.info(f"[Step1] 例外：{e}")
else:
    log.info("[Step1] 跳過（32-bit Python 或腳本不存在），使用現有 snapshot")

# Step 2: 64-bit Python 上傳 Sheets
log.info("[Step2] 上傳至 Google Sheets...")
r2 = subprocess.run(
    [PYTHON64, UPLOAD_SCRIPT],
    cwd=str(PROJECT),
    capture_output=True, text=True, timeout=60
)
log.info(r2.stdout[-2000:] if r2.stdout else "")
if r2.stderr:
    log.info("[stderr] " + r2.stderr[-500:])
log.info(f"[Step2] RC={r2.returncode}")

if r2.returncode == 0:
    log.info("=== 同步完成 ===")
else:
    log.info("=== Step2 失敗，請查看 log ===")
    try:
        sys.path.insert(0, str(PROJECT))
        from modules.notifier import notify_sync_event
        notify_sync_event("元大 Step2 上傳失敗", f"RC={r2.returncode}", ok=False)
    except Exception:
        pass

sys.exit(r2.returncode)
