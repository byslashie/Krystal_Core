#!/usr/bin/env python
"""Notify Discord of daily_nav sync errors"""
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def notify_error(step_name: str, return_code: int):
    """Send Discord notification for sync failure"""
    try:
        from modules.notifier import notify_sync_event

        error_msg = f"[ERROR] {step_name} 失敗 (RC={return_code})"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        notify_sync_event(
            title=f"Daily NAV 同步失敗 - {timestamp}",
            message=f"{error_msg}\n\n請檢查日誌: _logs/daily_nav.log",
            ok=False
        )
        logger.info(f"✅ Discord 通知已發送: {error_msg}")
    except Exception as e:
        logger.error(f"❌ 無法發送 Discord 通知: {e}")
        # Don't exit with error, since we're already reporting a sync failure

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: notify_error.py <step_name> <return_code>")
        sys.exit(1)

    step_name = sys.argv[1]
    return_code = int(sys.argv[2])
    notify_error(step_name, return_code)
