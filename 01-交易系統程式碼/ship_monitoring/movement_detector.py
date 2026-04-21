"""
🔍 船舶移動檢測器
比對歷史數據，檢測：
- 進入/離開監測區域
- 速度異常變化
- 長時間靜止
- 位置跳躍
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import math

try:
    from .config import GULF_REGION, ALERT_RULES, ALERT_TYPES, VESSEL_STATUS
except ImportError:
    from config import GULF_REGION, ALERT_RULES, ALERT_TYPES, VESSEL_STATUS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VesselTracker:
    """船舶軌跡追踪與異常檢測"""

    def __init__(self):
        self.history: Dict[str, List[Dict]] = {}  # mmsi -> [歷史位置記錄]
        self.last_alerts: Dict[str, datetime] = {}  # mmsi -> 最後告警時間（防止重複）

    def is_in_region(self, lat: float, lon: float) -> bool:
        """檢查座標是否在波斯灣內"""
        return (
            GULF_REGION["lat_min"] <= lat <= GULF_REGION["lat_max"]
            and GULF_REGION["lon_min"] <= lon <= GULF_REGION["lon_max"]
        )

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        計算兩點間距離（Haversine 公式）
        返回距離，單位：公里
        """
        R = 6371  # 地球半徑（km）

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def detect_alerts(self, vessels: List[Dict]) -> List[Dict]:
        """
        檢測所有船舶的異常情況
        返回告警列表
        """
        alerts = []

        for vessel in vessels:
            mmsi = vessel["mmsi"]
            vessel_alerts = self._detect_vessel_alerts(vessel)
            alerts.extend(vessel_alerts)

            # 更新歷史記錄
            if mmsi not in self.history:
                self.history[mmsi] = []

            self.history[mmsi].append(
                {
                    "timestamp": datetime.fromisoformat(vessel["last_update"]),
                    "latitude": vessel["latitude"],
                    "longitude": vessel["longitude"],
                    "speed": vessel["speed"],
                    "heading": vessel["heading"],
                    "status": vessel["status"],
                }
            )

            # 保留最近 24 小時的數據
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.history[mmsi] = [
                h for h in self.history[mmsi] if h["timestamp"] > cutoff_time
            ]

        return alerts

    def _detect_vessel_alerts(self, vessel: Dict) -> List[Dict]:
        """檢測單艘船舶的異常"""
        alerts = []
        mmsi = vessel["mmsi"]
        lat, lon = vessel["latitude"], vessel["longitude"]
        speed = vessel["speed"]
        now = datetime.now()

        # 1️⃣ 進入/離開區域
        in_region = self.is_in_region(lat, lon)
        was_in_region = False

        if mmsi in self.history and len(self.history[mmsi]) > 0:
            prev = self.history[mmsi][-1]
            was_in_region = self.is_in_region(prev["latitude"], prev["longitude"])

        if ALERT_RULES["enter_region"] and in_region and not was_in_region:
            alerts.append(
                {
                    "alert_type": ALERT_TYPES["ENTERED_REGION"],
                    "vessel_name": vessel["vessel_name"],
                    "mmsi": mmsi,
                    "message": f"⚠️ 油輪進入波斯灣：{vessel['vessel_name']} ({mmsi})",
                    "severity": "high",
                    "timestamp": now.isoformat(),
                }
            )

        if ALERT_RULES["exit_region"] and not in_region and was_in_region:
            alerts.append(
                {
                    "alert_type": ALERT_TYPES["EXITED_REGION"],
                    "vessel_name": vessel["vessel_name"],
                    "mmsi": mmsi,
                    "message": f"✅ 油輪離開波斯灣：{vessel['vessel_name']} ({mmsi})",
                    "severity": "low",
                    "timestamp": now.isoformat(),
                }
            )

        # 2️⃣ 靜止超過閾值
        if ALERT_RULES["stationary_duration"] and mmsi in self.history:
            stationary_minutes = self._calculate_stationary_duration(mmsi)
            if stationary_minutes >= ALERT_RULES["stationary_duration"]:
                # 檢查是否已經告警過（防止重複）
                if mmsi not in self.last_alerts or (
                    now - self.last_alerts[mmsi]
                ).total_seconds() > 3600:  # 1 小時告警一次
                    alerts.append(
                        {
                            "alert_type": ALERT_TYPES["STATIONARY"],
                            "vessel_name": vessel["vessel_name"],
                            "mmsi": mmsi,
                            "message": f"🛑 油輪停止不動 {stationary_minutes:.0f} 分鐘：{vessel['vessel_name']} ({mmsi})",
                            "severity": "medium",
                            "timestamp": now.isoformat(),
                            "duration_minutes": stationary_minutes,
                        }
                    )
                    self.last_alerts[mmsi] = now

        # 3️⃣ 速度異常變化
        if ALERT_RULES["speed_increase_threshold"] and mmsi in self.history:
            speed_change = self._calculate_speed_change(mmsi)
            if speed_change is not None:
                if (
                    speed_change > ALERT_RULES["speed_increase_threshold"]
                    and speed > 5
                ):  # 避免靜止時的誤報
                    alerts.append(
                        {
                            "alert_type": ALERT_TYPES["SPEED_CHANGE"],
                            "vessel_name": vessel["vessel_name"],
                            "mmsi": mmsi,
                            "message": f"⚡ 油輪加速 {speed_change:.0f}%：{vessel['vessel_name']} ({mmsi}) 當前速度 {speed:.1f} 節",
                            "severity": "high",
                            "timestamp": now.isoformat(),
                            "speed_change_percent": speed_change,
                        }
                    )

        # 4️⃣ 新船舶進入區域
        if in_region and mmsi not in self.history:
            alerts.append(
                {
                    "alert_type": ALERT_TYPES["NEW_VESSEL"],
                    "vessel_name": vessel["vessel_name"],
                    "mmsi": mmsi,
                    "message": f"🆕 新油輪進入波斯灣：{vessel['vessel_name']} ({mmsi})",
                    "severity": "medium",
                    "timestamp": now.isoformat(),
                }
            )

        return alerts

    def _calculate_stationary_duration(self, mmsi: str) -> float:
        """計算船舶停止不動的時間（分鐘）"""
        if mmsi not in self.history or len(self.history[mmsi]) < 2:
            return 0

        # 檢查最近 10 個記錄是否都在同一位置
        recent = self.history[mmsi][-10:]
        start = recent[0]

        for record in recent[1:]:
            distance = self.calculate_distance(
                start["latitude"],
                start["longitude"],
                record["latitude"],
                record["longitude"],
            )
            if distance > 0.1:  # > 100 米 = 移動了
                return 0

        # 計算時間差
        if len(self.history[mmsi]) >= 2:
            duration = (
                self.history[mmsi][-1]["timestamp"]
                - self.history[mmsi][0]["timestamp"]
            ).total_seconds() / 60

            return max(duration, 0)

        return 0

    def _calculate_speed_change(self, mmsi: str) -> Optional[float]:
        """計算速度變化百分比"""
        if mmsi not in self.history or len(self.history[mmsi]) < 2:
            return None

        history = self.history[mmsi]

        # 比較最新記錄與 5 分鐘前的速度
        time_window = timedelta(minutes=5)
        target_time = history[-1]["timestamp"] - time_window

        prev_record = None
        for record in reversed(history[:-1]):
            if record["timestamp"] <= target_time:
                prev_record = record
                break

        if prev_record is None or prev_record["speed"] == 0:
            return None

        speed_change = (
            (history[-1]["speed"] - prev_record["speed"]) / prev_record["speed"]
        ) * 100

        return speed_change

    def get_vessel_summary(self, mmsi: str) -> Optional[Dict]:
        """獲取特定船舶的摘要"""
        if mmsi not in self.history:
            return None

        history = self.history[mmsi]
        latest = history[-1]

        return {
            "mmsi": mmsi,
            "total_records": len(history),
            "first_seen": history[0]["timestamp"].isoformat(),
            "last_seen": latest["timestamp"].isoformat(),
            "current_location": {
                "latitude": latest["latitude"],
                "longitude": latest["longitude"],
                "in_region": self.is_in_region(latest["latitude"], latest["longitude"]),
            },
            "current_speed": latest["speed"],
            "current_heading": latest["heading"],
            "stationary_duration": self._calculate_stationary_duration(mmsi),
        }


def detect_all_alerts(vessels: List[Dict], tracker: VesselTracker) -> List[Dict]:
    """便利函數：檢測所有告警"""
    return tracker.detect_alerts(vessels)


if __name__ == "__main__":
    # 測試檢測器
    logger.info("🔍 測試移動檢測器...")

    test_vessels = [
        {
            "vessel_name": "TEST TANKER",
            "mmsi": "123456789",
            "latitude": 26.5,
            "longitude": 52.5,
            "speed": 10.5,
            "heading": 45,
            "last_update": datetime.now().isoformat(),
            "status": "active",
        },
    ]

    tracker = VesselTracker()

    # 第一次掃描（進入區域）
    alerts = tracker.detect_alerts(test_vessels)
    print(f"\n第一次掃描：{len(alerts)} 個告警")
    for alert in alerts:
        print(f"  {alert['message']}")

    # 第二次掃描（無變化）
    alerts = tracker.detect_alerts(test_vessels)
    print(f"\n第二次掃描：{len(alerts)} 個告警")

    # 查詢摘要
    summary = tracker.get_vessel_summary("123456789")
    print(f"\n船舶摘要：{json.dumps(summary, indent=2)}")
