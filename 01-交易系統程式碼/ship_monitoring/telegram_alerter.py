"""
📱 Telegram 告警模組
發送船舶監測告警到 Telegram
支持富格式消息和表情符號
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

try:
    from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEBUG
except ImportError:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEBUG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramAlerter:
    """Telegram 告警發送器"""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.api_base = "https://api.telegram.org/bot"
        self.is_configured = bool(self.bot_token and self.chat_id)

        if not self.is_configured:
            logger.warning(
                "⚠️ Telegram 未配置！請設置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 環境變數"
            )

    def send_alert(self, alert: Dict) -> bool:
        """發送單個告警"""
        if not self.is_configured:
            if DEBUG:
                logger.info(f"🔧 [模擬] 發送告警：{alert['message']}")
            return False

        message = self._format_alert_message(alert)
        return self._send_message(message)

    def send_alerts_batch(self, alerts: List[Dict]) -> int:
        """批量發送告警，返回成功數"""
        success_count = 0

        for alert in alerts:
            try:
                if self.send_alert(alert):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ 告警發送失敗：{alert['vessel_name']}")
            except Exception as e:
                logger.error(f"❌ 發送告警異常：{e}")

        return success_count

    def send_status_report(self, stats: Dict) -> bool:
        """發送狀態報告（每小時一次）"""
        if not self.is_configured:
            logger.info(f"🔧 [模擬] 發送狀態報告：{stats}")
            return False

        message = self._format_status_report(stats)
        return self._send_message(message)

    def _format_alert_message(self, alert: Dict) -> str:
        """格式化告警消息"""
        alert_type = alert.get("alert_type", "")
        severity = alert.get("severity", "info")

        # 根據嚴重程度選擇前綴
        emoji_map = {
            "high": "🚨",
            "medium": "⚠️",
            "low": "ℹ️",
            "info": "📢",
        }
        emoji = emoji_map.get(severity, "📌")

        # 基本信息
        lines = [
            f"{emoji} <b>船舶監測告警</b>",
            f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"<b>船名</b>：{alert.get('vessel_name', 'Unknown')}",
            f"<b>MMSI</b>：<code>{alert.get('mmsi', 'N/A')}</code>",
            "",
            f"<b>告警類型</b>：{alert_type}",
            f"<b>嚴重程度</b>：{severity}",
            "",
            f"💬 {alert.get('message', '')}",
        ]

        # 根據告警類型添加額外信息
        if alert.get("duration_minutes"):
            lines.append(f"⏱️ 停止時間：{alert['duration_minutes']:.0f} 分鐘")

        if alert.get("speed_change_percent"):
            lines.append(f"⚡ 速度變化：{alert['speed_change_percent']:.0f}%")

        lines.append("")
        lines.append(
            "🔗 <a href='https://www.marinetraffic.com/en/ais/home'>Marine Traffic</a> | "
            "<a href='https://www.shipxy.com/'>ShipXY</a>"
        )

        return "\n".join(lines)

    def _format_status_report(self, stats: Dict) -> str:
        """格式化狀態報告"""
        lines = [
            "📊 <b>波斯灣油輪監測 - 狀態報告</b>",
            f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"🚢 監測油輪總數：<b>{stats.get('total_vessels', 0)}</b>",
            f"📍 波斯灣內油輪：<b>{stats.get('vessels_in_region', 0)}</b>",
            f"🔴 最近 1 小時告警：<b>{stats.get('recent_alerts', 0)}</b>",
            f"✅ 系統狀態：<b>{stats.get('status', 'Normal')}</b>",
            "",
        ]

        # 如果有主要事件，列出
        if stats.get("major_events"):
            lines.append("<b>🚨 主要事件：</b>")
            for event in stats["major_events"]:
                lines.append(f"  • {event}")
            lines.append("")

        lines.append("持續監測中...")

        return "\n".join(lines)

    def _send_message(self, message: str) -> bool:
        """發送 Telegram 消息"""
        if not self.is_configured:
            return False

        url = f"{self.api_base}{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Telegram 消息已發送")
                return True
            else:
                logger.error(f"❌ Telegram 返回錯誤：{result.get('description')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Telegram 發送失敗：{e}")
            return False

    def test_connection(self) -> bool:
        """測試 Telegram 連接"""
        if not self.is_configured:
            logger.warning("⚠️ Telegram 未配置，跳過連接測試")
            return False

        logger.info("🔄 測試 Telegram 連接...")

        test_message = (
            "✅ <b>波斯灣油輪監測系統已連接</b>\n\n"
            "🚢 Ship Monitor 正在運行...\n"
            f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return self._send_message(test_message)


def create_alerter() -> TelegramAlerter:
    """工廠函數：建立 Telegram 告警器"""
    return TelegramAlerter()


if __name__ == "__main__":
    # 測試 Telegram 告警器
    logger.info("📱 測試 Telegram 告警器...")

    alerter = TelegramAlerter()

    # 測試連接
    if alerter.is_configured:
        if alerter.test_connection():
            logger.info("✅ Telegram 連接成功！")

            # 發送測試告警
            test_alert = {
                "alert_type": "entered_region",
                "vessel_name": "TEST TANKER",
                "mmsi": "123456789",
                "message": "⚠️ 測試油輪進入波斯灣",
                "severity": "high",
            }

            if alerter.send_alert(test_alert):
                logger.info("✅ 測試告警已發送！")
        else:
            logger.error("❌ Telegram 連接失敗")
    else:
        logger.warning("⚠️ Telegram 未配置，無法測試")
