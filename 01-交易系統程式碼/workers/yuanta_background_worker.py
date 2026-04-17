"""
元大庫存查詢 背景進程
- 獨立 32-bit Python 進程運行
- 每日台灣時間 09:15 自動同步
- 支持按需手動同步
"""

import logging
import os
import sys
import time
import subprocess
from datetime import datetime, time as dt_time
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [Yuanta Worker] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/yuanta_worker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ============================
# 工具函數
# ============================

def is_market_open() -> bool:
    """判斷台灣股市是否開盤時段（09:00-13:30）"""
    now = datetime.now()
    current_time = now.time()

    # 只在交易日（周一到周五）且開盤時段執行
    if now.weekday() >= 5:  # 週六週日
        return False

    # 開盤時間：09:00 - 13:30
    return dt_time(9, 0) <= current_time <= dt_time(13, 30)


def should_sync_now() -> bool:
    """判斷是否應該執行同步（每日 09:15）"""
    now = datetime.now()
    current_time = now.time()

    # 只在台灣開盤時段執行
    if now.weekday() >= 5:  # 週六週日，不執行
        return False

    # 目標時間：09:15-09:20（5 分鐘窗口）
    return dt_time(9, 15) <= current_time <= dt_time(9, 20)


def run_sync_script() -> bool:
    """調用元大同步腳本（使用 32-bit Python）"""
    try:
        logger.info("🔄 開始同步元大庫存...")

        # 獲取 32-bit Python 路徑
        venv_32bit = PROJECT_ROOT / ".venv_yuanta32_new" / "Scripts" / "python.exe"
        sync_script = PROJECT_ROOT / "brokers" / "sync_yuanta_positions.py"

        if not venv_32bit.exists():
            logger.error(f"❌ 找不到 32-bit Python：{venv_32bit}")
            return False

        if not sync_script.exists():
            logger.error(f"❌ 找不到同步腳本：{sync_script}")
            return False

        # 運行同步腳本
        logger.info(f"📍 使用 Python: {venv_32bit}")
        logger.info(f"📍 腳本位置: {sync_script}")

        result = subprocess.run(
            [str(venv_32bit), str(sync_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,  # 5 分鐘超時
        )

        # 記錄輸出
        if result.stdout:
            logger.info("=== 標準輸出 ===")
            for line in result.stdout.split("\n"):
                if line.strip():
                    logger.info(line)

        if result.stderr:
            logger.warning("=== 錯誤輸出 ===")
            for line in result.stderr.split("\n"):
                if line.strip():
                    logger.warning(line)

        if result.returncode == 0:
            logger.info("✅ 元大同步完成 (Return Code: 0)")
            return True
        else:
            logger.error(f"❌ 元大同步失敗 (Return Code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        logger.error("❌ 同步超時（超過 5 分鐘）")
        return False
    except Exception as e:
        logger.error(f"❌ 同步異常：{e}", exc_info=True)
        return False


# ============================
# 主要邏輯
# ============================

class YuantaBackgroundWorker:
    """元大背景工作進程"""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval  # 檢查間隔（秒）
        self.last_sync_time = None
        self.today_synced = False  # 今天是否已同步過

    def run(self) -> None:
        """主循環"""
        logger.info("=" * 60)
        logger.info("🚀 元大背景查詢進程已啟動")
        logger.info(f"📍 同步時間：每日台灣時間 09:15")
        logger.info(f"📍 檢查間隔：{self.check_interval} 秒")
        logger.info("=" * 60)

        check_count = 0

        while True:
            try:
                check_count += 1
                now = datetime.now()
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

                logger.debug(f"📊 檢查 #{check_count} ({current_time_str})")

                # 檢查是否超過午夜（重置今日同步標誌）
                if now.hour == 0 and now.minute < self.check_interval // 60:
                    self.today_synced = False
                    logger.info("📅 新的一天開始，重置同步標誌")

                # 判斷是否應該執行同步
                if should_sync_now():
                    if not self.today_synced:
                        logger.info(f"⏰ 同步時間已到（09:15±5 分鐘）")
                        success = run_sync_script()

                        if success:
                            self.today_synced = True
                            self.last_sync_time = now
                            logger.info(f"✅ 同步成功，標記今日已同步")
                        else:
                            logger.error(f"❌ 同步失敗，稍後會重試")
                    else:
                        logger.debug("ℹ️ 今天已同步過，跳過")
                else:
                    logger.debug(f"⏸️  非同步時間 ({current_time_str})")

                # 等待下一次檢查
                logger.debug(f"💤 等待 {self.check_interval}s 後進行下一次檢查...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("\n⏹️  元大背景進程已停止 (Ctrl+C)")
                break
            except Exception as e:
                logger.error(f"❌ 背景進程異常：{e}", exc_info=True)
                logger.warning(f"⚠️ 等待 {self.check_interval}s 後重試...")
                time.sleep(self.check_interval)


def main():
    """入口函數"""
    # 創建日誌目錄
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    # 驗證環境
    logger.info("📋 驗證環境...")
    venv_32bit = PROJECT_ROOT / ".venv_yuanta32_new" / "Scripts" / "python.exe"
    if not venv_32bit.exists():
        logger.error(f"❌ 找不到 32-bit Python：{venv_32bit}")
        logger.error("請確認 .venv_yuanta32_new 已正確設置")
        sys.exit(1)
    logger.info(f"✅ 32-bit Python 找到：{venv_32bit}")

    sync_script = PROJECT_ROOT / "brokers" / "sync_yuanta_positions.py"
    if not sync_script.exists():
        logger.error(f"❌ 找不到同步腳本：{sync_script}")
        sys.exit(1)
    logger.info(f"✅ 同步腳本找到：{sync_script}")

    # 啟動進程
    worker = YuantaBackgroundWorker(check_interval=60)
    worker.run()


if __name__ == "__main__":
    main()
