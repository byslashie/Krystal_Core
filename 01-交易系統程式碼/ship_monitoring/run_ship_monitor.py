#!/usr/bin/env python3
"""
🚢 波斯灣油輪監測系統 - 一鍵啟動腳本

用法：
  python run_ship_monitor.py                    # 連續監測模式
  python run_ship_monitor.py --mode once        # 單次掃描
  python run_ship_monitor.py --dashboard        # 僅啟動儀表板
  python run_ship_monitor.py --test             # 測試模式（模擬數據）
"""

import os
import sys
import argparse
import subprocess
import threading
import time
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment():
    """檢查環境設定"""
    logger.info("🔍 檢查環境設定...")

    # 檢查 .env 檔案
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        logger.warning("⚠️ 未找到 .env 檔案，將使用預設配置或環境變數")
    else:
        logger.info(f"✅ 找到 .env 檔案：{env_file}")

    # 檢查 credentials.json
    creds_file = Path(__file__).parent.parent / "credentials.json"
    if not creds_file.exists():
        logger.warning(
            "⚠️ 未找到 credentials.json，Google Sheets 功能將被禁用"
        )
        os.environ["DISABLE_SHEETS"] = "1"
    else:
        logger.info(f"✅ 找到 credentials.json")

    # 檢查 Telegram 配置
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")

    if telegram_token and telegram_chat:
        logger.info("✅ Telegram 配置完成")
    else:
        logger.warning(
            "⚠️ Telegram 未配置！請設置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 環境變數"
        )

    # 檢查日誌目錄
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.info(f"📁 日誌目錄：{log_dir}")


def run_service(mode="continuous", iterations=None, test=False):
    """運行監測服務"""
    logger.info(f"🚀 啟動監測服務 (模式: {mode})")

    if test:
        logger.info("🔧 使用測試模式（模擬數據）")
        os.environ["MOCK_DATA"] = "1"

    service_module = Path(__file__).parent / "service.py"

    cmd = [sys.executable, str(service_module), "--mode", mode]

    if iterations:
        cmd.extend(["--iterations", str(iterations)])

    if test:
        cmd.append("--test")

    try:
        subprocess.run(cmd, cwd=str(Path(__file__).parent))
    except KeyboardInterrupt:
        logger.info("\n⏹️ 服務已停止")


def run_dashboard():
    """運行儀表板"""
    logger.info("🌍 啟動儀表板...")

    dashboard_module = Path(__file__).parent / "dashboard.py"

    try:
        subprocess.run([sys.executable, str(dashboard_module)], cwd=str(Path(__file__).parent))
    except KeyboardInterrupt:
        logger.info("\n⏹️ 儀表板已停止")


def run_parallel(service_mode="continuous", test=False):
    """並行運行服務和儀表板"""
    logger.info("🔄 同時運行服務和儀表板...")

    # 服務線程
    service_thread = threading.Thread(
        target=run_service,
        args=(service_mode, None, test),
        daemon=True
    )

    # 儀表板線程
    dashboard_thread = threading.Thread(
        target=run_dashboard,
        daemon=True
    )

    service_thread.start()
    time.sleep(2)  # 讓服務先啟動

    dashboard_thread.start()

    logger.info("✅ 兩個服務均已啟動")
    logger.info("📊 訪問儀表板：http://localhost:5001")
    logger.info("按 Ctrl+C 停止所有服務...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ 所有服務已停止")


def test_telegram():
    """測試 Telegram 連接"""
    logger.info("📱 測試 Telegram 連接...")

    from telegram_alerter import TelegramAlerter

    alerter = TelegramAlerter()
    if alerter.is_configured:
        if alerter.test_connection():
            logger.info("✅ Telegram 連接成功！")
            return True
        else:
            logger.error("❌ Telegram 連接失敗")
            return False
    else:
        logger.error("❌ Telegram 未配置")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="🚢 波斯灣油輪監測系統一鍵啟動"
    )

    parser.add_argument(
        "--mode",
        choices=["once", "continuous"],
        default="continuous",
        help="執行模式（預設：continuous）"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        help="連續模式下的最大迭代次數"
    )

    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="僅啟動儀表板"
    )

    parser.add_argument(
        "--service",
        action="store_true",
        help="僅啟動監測服務"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="同時啟動服務和儀表板"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="使用測試模式（模擬數據）"
    )

    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="測試 Telegram 連接"
    )

    args = parser.parse_args()

    # 檢查環境
    check_environment()

    print("\n" + "=" * 60)
    print("🚢 波斯灣油輪監測系統")
    print("=" * 60)

    # 根據參數選擇執行模式
    if args.test_telegram:
        test_telegram()
    elif args.dashboard:
        run_dashboard()
    elif args.service:
        run_service(mode=args.mode, iterations=args.iterations, test=args.test)
    elif args.parallel:
        run_parallel(service_mode=args.mode, test=args.test)
    else:
        # 預設：並行運行
        run_parallel(service_mode=args.mode, test=args.test)

    print("\n" + "=" * 60)
    print("✅ 系統關閉")
    print("=" * 60)


if __name__ == "__main__":
    main()
