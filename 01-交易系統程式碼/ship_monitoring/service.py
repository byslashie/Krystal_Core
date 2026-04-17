"""
🎯 波斯灣油輪監測服務
集成爬蟲、檢測器、告警和 Google Sheets
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import json

try:
    from .ais_scraper import fetch_gulf_tankers
    from .movement_detector import VesselTracker, detect_all_alerts
    from .telegram_alerter import create_alerter
    from .config import SCRAPER_CONFIG, DEBUG
except ImportError:
    from ais_scraper import fetch_gulf_tankers
    from movement_detector import VesselTracker, detect_all_alerts
    from telegram_alerter import create_alerter
    from config import SCRAPER_CONFIG, DEBUG

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ShipMonitoringService:
    """波斯灣油輪監測主服務"""

    def __init__(self):
        self.tracker = VesselTracker()
        self.alerter = create_alerter()
        self.last_status_report = datetime.now()
        self.status_report_interval = timedelta(hours=1)

        logger.info("🚀 波斯灣油輪監測服務已啟動")

    def run_once(self) -> Dict:
        """執行一次完整的掃描迴圈"""
        start_time = datetime.now()

        try:
            # 1️⃣ 獲取船舶數據
            logger.info("📡 正在獲取 AIS 數據...")
            vessels = fetch_gulf_tankers()

            if not vessels:
                logger.warning("⚠️ 未能獲取任何船舶數據")
                return {"success": False, "error": "No vessels found"}

            logger.info(f"✅ 獲得 {len(vessels)} 艘油輪")

            # 2️⃣ 檢測異常和告警
            logger.info("🔍 檢測異常移動...")
            alerts = detect_all_alerts(vessels, self.tracker)

            logger.info(f"📢 偵測到 {len(alerts)} 個告警")

            # 3️⃣ 發送告警到 Telegram
            if alerts:
                success_count = self.alerter.send_alerts_batch(alerts)
                logger.info(f"✅ {success_count}/{len(alerts)} 個告警已發送")

            # 4️⃣ 統計摘要
            stats = self._generate_statistics(vessels, alerts)

            # 5️⃣ 定期發送狀態報告
            if (datetime.now() - self.last_status_report) > self.status_report_interval:
                logger.info("📊 發送狀態報告...")
                self.alerter.send_status_report(stats)
                self.last_status_report = datetime.now()

            # 6️⃣ 嘗試寫入 Google Sheets（可選）
            try:
                self._write_to_sheets(vessels, alerts)
            except Exception as e:
                logger.warning(f"⚠️ Google Sheets 寫入失敗：{e}")

            duration = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "timestamp": start_time.isoformat(),
                "vessels_count": len(vessels),
                "alerts_count": len(alerts),
                "alerts_sent": success_count if alerts else 0,
                "duration_seconds": duration,
                "statistics": stats,
            }

            logger.info(f"✅ 掃描完成 ({duration:.1f}s)")
            return result

        except Exception as e:
            logger.error(f"❌ 掃描失敗：{e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def run_continuous(self, max_iterations: int = None):
        """連續執行監測（後台服務）"""
        iteration = 0
        logger.info(
            f"🔁 開始連續監測，更新間隔 {SCRAPER_CONFIG['update_interval']} 秒"
        )

        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                logger.info(f"\n{'=' * 60}")
                logger.info(f"掃描 #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'=' * 60}")

                result = self.run_once()

                if result["success"]:
                    logger.info(f"下次掃描將在 {SCRAPER_CONFIG['update_interval']} 秒後進行")
                else:
                    logger.error(f"掃描失敗，{SCRAPER_CONFIG['retry_delay']} 秒後重試")
                    time.sleep(SCRAPER_CONFIG["retry_delay"])
                    continue

                # 等待下一次掃描
                time.sleep(SCRAPER_CONFIG["update_interval"])

        except KeyboardInterrupt:
            logger.info("\n⏹️ 監測服務已停止 (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ 服務異常：{e}", exc_info=True)
        finally:
            logger.info("🛑 波斯灣油輪監測服務已關閉")

    def _generate_statistics(self, vessels: List[Dict], alerts: List[Dict]) -> Dict:
        """生成統計摘要"""
        in_region_count = sum(
            1
            for v in vessels
            if self.tracker.is_in_region(v["latitude"], v["longitude"])
        )

        high_severity_alerts = [a for a in alerts if a.get("severity") == "high"]

        return {
            "total_vessels": len(vessels),
            "vessels_in_region": in_region_count,
            "vessels_outside_region": len(vessels) - in_region_count,
            "recent_alerts": len(alerts),
            "high_severity_alerts": len(high_severity_alerts),
            "status": "Normal" if len(high_severity_alerts) == 0 else "⚠️ Caution",
            "major_events": [a["message"] for a in high_severity_alerts[:3]],
        }

    def _write_to_sheets(self, vessels: List[Dict], alerts: List[Dict]):
        """寫入數據到 Google Sheets"""
        try:
            # 動態導入 sheets_utils，如果存在的話
            import sys
            import os

            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

            from sheets_utils import write_ship_tracking, write_intel_event

            # 寫入船舶追踪數據
            for vessel in vessels:
                write_ship_tracking(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "vessel_name": vessel["vessel_name"],
                        "mmsi": vessel["mmsi"],
                        "imo": vessel.get("imo", ""),
                        "vessel_type": vessel["vessel_type"],
                        "flag": vessel["flag"],
                        "latitude": vessel["latitude"],
                        "longitude": vessel["longitude"],
                        "speed": vessel["speed"],
                        "heading": vessel["heading"],
                        "last_update": vessel["last_update"],
                        "status": vessel["status"],
                        "alert_type": "",
                    }
                )

            # 寫入告警作為 intel_events
            for alert in alerts:
                write_intel_event(
                    {
                        "date": datetime.now().isoformat(),
                        "event_type": "ship_movement",
                        "location": f"波斯灣 ({alert.get('mmsi', 'N/A')})",
                        "severity": {"high": 90, "medium": 50, "low": 20}.get(
                            alert.get("severity"), 30
                        ),
                        "llm_risk_score": {"high": 85, "medium": 60, "low": 30}.get(
                            alert.get("severity"), 40
                        ),
                        "summary": alert.get("message", ""),
                        "impact_assets": "Oil, Energy ETFs, XLE, USO",
                    }
                )

            logger.info("✅ 數據已寫入 Google Sheets")

        except ImportError:
            logger.debug("ℹ️ sheets_utils 未可用，跳過 Google Sheets 寫入")
        except Exception as e:
            logger.warning(f"⚠️ Google Sheets 寫入異常：{e}")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="波斯灣油輪監測服務")
    parser.add_argument(
        "--mode",
        choices=["once", "continuous"],
        default="continuous",
        help="執行模式",
    )
    parser.add_argument(
        "--iterations", type=int, default=None, help="連續模式下的最大迭代次數"
    )
    parser.add_argument(
        "--test", action="store_true", help="測試模式（使用模擬數據）"
    )

    args = parser.parse_args()

    service = ShipMonitoringService()

    if args.test:
        logger.info("🔧 運行在測試模式 (使用模擬數據)")

    if args.mode == "once":
        logger.info("📍 單次掃描模式")
        result = service.run_once()
        print("\n" + "=" * 60)
        print("掃描結果：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        logger.info("🔁 連續監測模式")
        service.run_continuous(max_iterations=args.iterations)


if __name__ == "__main__":
    main()
