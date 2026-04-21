"""
🌍 波斯灣油輪監測 - Flask 實時儀表板
展示實時位置、告警日誌、歷史軌跡
"""

from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import json
import logging

try:
    from .ais_scraper import fetch_gulf_tankers
    from .movement_detector import VesselTracker, detect_all_alerts
    from .config import GULF_REGION
except ImportError:
    from ais_scraper import fetch_gulf_tankers
    from movement_detector import VesselTracker, detect_all_alerts
    from config import GULF_REGION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")

# 全局狀態
tracker = VesselTracker()
last_vessels = []
last_alerts = []
last_update = None


@app.route("/")
def index():
    """儀表板首頁"""
    return render_template("ship_dashboard.html")


@app.route("/api/vessels")
def api_vessels():
    """獲取當前所有油輪"""
    global last_vessels, last_update

    try:
        last_vessels = fetch_gulf_tankers()
        last_update = datetime.now().isoformat()

        return jsonify(
            {
                "success": True,
                "timestamp": last_update,
                "count": len(last_vessels),
                "vessels": last_vessels,
            }
        )
    except Exception as e:
        logger.error(f"❌ 獲取船舶數據失敗：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/alerts")
def api_alerts():
    """獲取最新告警"""
    global last_vessels, last_alerts

    try:
        if not last_vessels:
            last_vessels = fetch_gulf_tankers()

        last_alerts = detect_all_alerts(last_vessels, tracker)

        # 只返回最近 24 小時的告警
        cutoff = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            a
            for a in last_alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "count": len(recent_alerts),
                "alerts": recent_alerts,
            }
        )
    except Exception as e:
        logger.error(f"❌ 獲取告警數據失敗：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/statistics")
def api_statistics():
    """獲取統計數據"""
    try:
        if not last_vessels:
            last_vessels = fetch_gulf_tankers()

        in_region = sum(
            1
            for v in last_vessels
            if tracker.is_in_region(v["latitude"], v["longitude"])
        )

        alerts_24h = [
            a
            for a in last_alerts
            if datetime.fromisoformat(a["timestamp"])
            > (datetime.now() - timedelta(hours=24))
        ]

        high_alerts = [a for a in alerts_24h if a.get("severity") == "high"]

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "total_vessels": len(last_vessels),
                "in_region": in_region,
                "outside_region": len(last_vessels) - in_region,
                "recent_alerts_24h": len(alerts_24h),
                "critical_alerts": len(high_alerts),
                "region": GULF_REGION,
            }
        )
    except Exception as e:
        logger.error(f"❌ 計算統計失敗：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vessel/<mmsi>")
def api_vessel_detail(mmsi):
    """獲取特定船舶的詳細信息"""
    try:
        summary = tracker.get_vessel_summary(mmsi)

        if not summary:
            return (
                jsonify({"success": False, "error": f"未找到船舶 {mmsi}"}),
                404,
            )

        return jsonify(
            {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "vessel": summary,
            }
        )
    except Exception as e:
        logger.error(f"❌ 獲取船舶詳情失敗：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "Server error"}), 500


def main():
    """啟動儀表板"""
    logger.info("🚀 啟動波斯灣油輪監測儀表板...")
    logger.info("訪問 http://localhost:5001 查看儀表板")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True,
        use_reloader=False,  # 避免重複啟動
    )


if __name__ == "__main__":
    main()
