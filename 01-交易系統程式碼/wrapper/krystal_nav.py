# -*- coding: utf-8 -*-
"""
krystal_nav.py - ASCII path wrapper for daily NAV recording
Placed at C:/Users/jrenw/ to avoid Chinese path issues in Windows Task Scheduler
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

PROJECT = Path("h:/\u6211\u7684\u96f2\u7aef\u786c\u789f/Krystal_\u5b8c\u6574\u7cfb\u7d71/01-\u4ea4\u6613\u7cfb\u7d71\u7a0b\u5f0f\u78bc")
PYTHON64 = r"C:\Users\jrenw\AppData\Local\Programs\Python\Python311\python.exe"
NAV_SCRIPT = str(PROJECT / "brokers/record_daily_nav.py")

import logging
log_path = PROJECT / "logs" / f"daily_nav_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

log.info("=== 每日市值記錄開始 ===")
r = subprocess.run(
    [PYTHON64, NAV_SCRIPT],
    cwd=str(PROJECT),
    capture_output=True, text=True, timeout=60
)
log.info(r.stdout[-2000:] if r.stdout else "")
if r.stderr:
    log.info("[stderr] " + r.stderr[-500:])
log.info(f"RC={r.returncode}")
log.info("=== 完成 ===" if r.returncode == 0 else "=== 失敗 ===")
sys.exit(r.returncode)
