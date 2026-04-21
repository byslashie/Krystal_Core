"""
intel_scraper.py - 影子艦隊 & 油輪異常偵測引擎

功能：
1. monitor_shadow_fleet() - 偵測 AIS 訊號中斷 & MMSI 黑名單衝突
2. detect_oil_shock_anomaly() - 偵測荷姆茲海峽異常急停 & 群聚異常 → 觸發 macro_risk
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import io

# 設置標準輸出編碼
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============================================================================
# 導入依賴
# ============================================================================
try:
    from ship_monitoring.ais_scraper import fetch_gulf_tankers
    from ship_monitoring.movement_detector import VesselTracker
    SHIP_MONITOR_OK = True
except Exception as e:
    logger.warning(f"ship_monitoring 導入失敗: {e}")
    SHIP_MONITOR_OK = False

try:
    from sheets_utils import write_intel_event, get_latest_intel_risk
    SHEETS_OK = True
except Exception as e:
    logger.warning(f"sheets_utils 導入失敗: {e}")
    SHEETS_OK = False

# ============================================================================
# 常量定義
# ============================================================================

# 荷姆茲海峽 + 阿曼灣監測區（用戶指定：23°N-27°N, 56°E-60°E）
HORMUZ_REGION = {
    "lat_min": 23.0,
    "lat_max": 27.0,
    "lon_min": 56.0,
    "lon_max": 60.0,
}

# 已知安全錨地（速度=0 在此視為正常拋錨，排除誤報）
SAFE_ZONES = [
    {"name": "富吉拉港錨地", "lat": 25.12, "lon": 56.35, "radius_km": 15},
    {"name": "霍爾法坎港", "lat": 25.36, "lon": 56.36, "radius_km": 10},
    {"name": "科爾·法坎", "lat": 25.37, "lon": 56.36, "radius_km": 8},
]

# 影子艦隊 MMSI/船名黑名單（可從 UN/OFAC 制裁列表擴充）
SHADOW_FLEET_BLACKLIST = [
    {"mmsi": "211378570", "vessel_name": "ASIAN GLORY", "reason": "伊朗關聯艦隊"},
    {"mmsi": "538008776", "vessel_name": "ISLAMIC REPUBLIC", "reason": "OFAC 制裁"},
]

# 異常偵測閾值
AIS_OUTAGE_THRESHOLD_HOURS = 12  # AIS 訊號中斷超過此時間視為異常
SPEED_SHOCK_HIGH = 10.0          # 異常急停：高速閾值（節）
SPEED_SHOCK_LOW = 1.0            # 異常急停：急停閾值（節）
SPEED_HISTORY_MINUTES = 30       # 速度變化窗口（分鐘）
CLUSTER_ANOMALY_COUNT = 3        # 群聚異常：同時多少艘觸發


# ============================================================================
# 主類
# ============================================================================

class ShadowFleetMonitor:
    """影子艦隊監測引擎"""

    def __init__(self):
        self.vessel_history = {}  # mmsi -> List[{timestamp, lat, lon, speed, heading, data}]
        self.tracker = VesselTracker()
        logger.info("[✓] ShadowFleetMonitor initialized")

    def update_vessel_history(self, vessels: List[Dict]):
        """更新船舶歷史記錄（維持 24 小時窗口）"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        for vessel in vessels:
            mmsi = vessel.get("mmsi")
            if not mmsi:
                continue

            if mmsi not in self.vessel_history:
                self.vessel_history[mmsi] = []

            # 新增記錄
            record = {
                "timestamp": datetime.fromisoformat(vessel.get("last_update", datetime.now().isoformat())),
                "lat": vessel.get("latitude"),
                "lon": vessel.get("longitude"),
                "speed": vessel.get("speed", 0),
                "heading": vessel.get("heading", 0),
                "vessel_name": vessel.get("vessel_name"),
                "data": vessel,
            }
            self.vessel_history[mmsi].append(record)

            # 清理超過 24h 的記錄
            self.vessel_history[mmsi] = [
                r for r in self.vessel_history[mmsi] if r["timestamp"] > cutoff_time
            ]

    def monitor_shadow_fleet(self) -> List[Dict]:
        """
        偵測影子艦隊異常：
        1. AIS 訊號中斷 > 12 小時
        2. MMSI/船名在黑名單中

        返回異常列表
        """
        if not SHIP_MONITOR_OK:
            logger.warning("[✗] ship_monitoring 不可用")
            return []

        vessels = fetch_gulf_tankers()
        self.update_vessel_history(vessels)

        anomalies = []

        for vessel in vessels:
            mmsi = vessel.get("mmsi")
            name = vessel.get("vessel_name")

            # 檢查 AIS 訊號中斷
            ais_outage = self._check_ais_outage(vessel)
            if ais_outage:
                anomalies.append(ais_outage)
                logger.info(f"[⚠️ ] AIS 訊號中斷: {name} ({mmsi})")

            # 檢查黑名單
            blacklist_match = self._check_mmsi_blacklist(vessel)
            if blacklist_match:
                anomalies.append(blacklist_match)
                logger.info(f"[🚨] 黑名單匹配: {name} ({mmsi})")

        # 若有異常，寫入 intel_events
        for anomaly in anomalies:
            self._write_event(anomaly)

        logger.info(f"[📊] Shadow Fleet Monitor: {len(anomalies)} 異常")
        return anomalies

    def detect_oil_shock_anomaly(self) -> Dict:
        """
        偵測油輪異常急停與群聚異常：
        1. 在安全區外的快速油輪發生異常急停 (speed >10 → <1 在 30 分鐘內)
        2. 當 ≥ 3 艘油輪同時異常 → 觸發群聚異常 → 寫入 CRITICAL，建議 XLE/S5

        返回分析結果 Dict
        """
        if not SHIP_MONITOR_OK:
            logger.warning("[✗] ship_monitoring 不可用")
            return {"status": "error", "message": "ship_monitoring unavailable"}

        vessels = fetch_gulf_tankers()
        self.update_vessel_history(vessels)

        # 篩選在荷姆茲海峽的油輪
        hormuz_vessels = [
            v for v in vessels
            if self._is_in_hormuz_strait(v.get("latitude"), v.get("longitude"))
        ]

        shocked_vessels = []

        for vessel in hormuz_vessels:
            mmsi = vessel.get("mmsi")
            name = vessel.get("vessel_name")
            lat = vessel.get("latitude")
            lon = vessel.get("longitude")

            # 排除安全區
            if self._is_in_safe_zone(lat, lon):
                logger.debug(f"[ℹ️ ] {name}: 在安全錨地內，正常拋錨")
                continue

            # 檢測異常急停
            if self._detect_speed_shock(vessel):
                shocked_vessels.append(vessel)
                logger.info(f"[⚠️ ] 異常急停: {name} ({mmsi}) - 速度從 >10 → <1")

        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "hormuz_vessel_count": len(hormuz_vessels),
            "shock_count": len(shocked_vessels),
            "vessels": [
                {
                    "mmsi": v.get("mmsi"),
                    "vessel_name": v.get("vessel_name"),
                    "latitude": v.get("latitude"),
                    "longitude": v.get("longitude"),
                    "speed": v.get("speed"),
                }
                for v in shocked_vessels
            ],
        }

        # 檢測群聚異常
        if len(shocked_vessels) >= CLUSTER_ANOMALY_COUNT:
            logger.critical(
                f"[🔥] 群聚異常觸發：{len(shocked_vessels)} 艘油輪同時異常急停！"
            )
            result["cluster_anomaly"] = True
            result["cluster_count"] = len(shocked_vessels)
            result["macro_risk"] = "HIGH"
            result["recommendation"] = "buy XLE (能源ETF) / activate S5 (做空科技股)"

            # 觸發 macro 操作建議
            self._trigger_macro_response("cluster_stop")
        else:
            result["cluster_anomaly"] = False
            result["cluster_count"] = 0

        logger.info(f"[📊] Oil Shock Monitor: {len(shocked_vessels)} 異常急停，群聚={result['cluster_anomaly']}")
        return result

    # ──────────────────────────────────────────────────────────────────────
    # 輔助方法
    # ──────────────────────────────────────────────────────────────────────

    def _check_ais_outage(self, vessel: Dict) -> Optional[Dict]:
        """
        檢查 AIS 訊號中斷
        若 last_update 距今 > 12 小時 → 異常
        """
        last_update_str = vessel.get("last_update")
        if not last_update_str:
            return None

        try:
            last_update = datetime.fromisoformat(last_update_str)
        except:
            return None

        outage_duration = datetime.now() - last_update
        if outage_duration > timedelta(hours=AIS_OUTAGE_THRESHOLD_HOURS):
            hours = outage_duration.total_seconds() / 3600

            return {
                "event_type": "Shadow_Fleet_Anomaly",
                "severity": "HIGH",
                "date": datetime.now().isoformat(),
                "location": f"{vessel.get('vessel_name')} ({vessel.get('latitude'):.1f}°N, {vessel.get('longitude'):.1f}°E)",
                "llm_risk_score": 0.85,
                "summary": f"AIS 訊號中斷: {vessel.get('vessel_name')} ({vessel.get('mmsi')}) - 已失聯 {hours:.1f} 小時",
                "impact_assets": "XLE,USO,WTI,USOIL",
            }

        return None

    def _check_mmsi_blacklist(self, vessel: Dict) -> Optional[Dict]:
        """
        檢查 MMSI/船名是否在黑名單中
        """
        mmsi = vessel.get("mmsi")
        name = vessel.get("vessel_name")

        for blacklist_entry in SHADOW_FLEET_BLACKLIST:
            if mmsi == blacklist_entry.get("mmsi") or name == blacklist_entry.get("vessel_name"):
                return {
                    "event_type": "Shadow_Fleet_Anomaly",
                    "severity": "HIGH",
                    "date": datetime.now().isoformat(),
                    "location": f"{name} ({vessel.get('latitude'):.1f}°N, {vessel.get('longitude'):.1f}°E)",
                    "llm_risk_score": 0.85,
                    "summary": f"MMSI 衝突: {mmsi} ({name}) 在黑名單中 - {blacklist_entry.get('reason')}",
                    "impact_assets": "XLE,USO,WTI,USOIL",
                }

        return None

    def _is_in_safe_zone(self, lat: float, lon: float) -> bool:
        """
        檢查座標是否在已知安全錨地內
        使用簡化的距離計算（≈ Haversine）
        """
        if not lat or not lon:
            return False

        for zone in SAFE_ZONES:
            # 簡化計算：假設 1° 緯度 ≈ 111 km，1° 經度 ≈ 111 km * cos(lat)
            lat_diff = abs(lat - zone["lat"]) * 111
            lon_diff = abs(lon - zone["lon"]) * 111 * (0.9)  # cos(25°) ≈ 0.9

            distance_km = (lat_diff**2 + lon_diff**2) ** 0.5

            if distance_km < zone["radius_km"]:
                return True

        return False

    def _is_in_hormuz_strait(self, lat: float, lon: float) -> bool:
        """檢查座標是否在荷姆茲海峽監測區內"""
        if not lat or not lon:
            return False

        return (
            HORMUZ_REGION["lat_min"] <= lat <= HORMUZ_REGION["lat_max"]
            and HORMUZ_REGION["lon_min"] <= lon <= HORMUZ_REGION["lon_max"]
        )

    def _detect_speed_shock(self, vessel: Dict) -> bool:
        """
        檢測異常急停：
        在 30 分鐘內，速度從 > SPEED_SHOCK_HIGH 降到 < SPEED_SHOCK_LOW
        """
        mmsi = vessel.get("mmsi")
        current_speed = vessel.get("speed", 0)

        # 當前速度 < 1 節
        if current_speed >= SPEED_SHOCK_LOW:
            return False

        # 查詢歷史（最近 30 分鐘）
        if mmsi not in self.vessel_history or len(self.vessel_history[mmsi]) < 2:
            return False

        history = self.vessel_history[mmsi]
        cutoff_time = datetime.now() - timedelta(minutes=SPEED_HISTORY_MINUTES)

        # 找最近 30 分鐘內速度 > 10 的記錄
        for record in reversed(history):
            if record["timestamp"] < cutoff_time:
                break
            if record["speed"] > SPEED_SHOCK_HIGH:
                logger.debug(
                    f"[DEBUG] {vessel.get('vessel_name')}: 速度從 {record['speed']:.1f} → {current_speed:.1f}"
                )
                return True

        return False

    def _write_event(self, event_data: Dict) -> bool:
        """寫入事件到 intel_events"""
        if not SHEETS_OK:
            logger.warning("[ℹ️ ] sheets_utils 不可用，事件不寫入 Google Sheets")
            logger.info(f"[事件] {event_data.get('event_type')}: {event_data.get('summary')}")
            return True

        try:
            success = write_intel_event(event_data)
            if success:
                logger.info(f"[✅] intel_events 新增: {event_data.get('event_type')}")
            return success
        except Exception as e:
            logger.error(f"[❌] 寫入 intel_events 失敗: {e}")
            return False

    def _trigger_macro_response(self, anomaly_type: str):
        """
        觸發 macro 操作建議
        當群聚異常被偵測時，寫入 CRITICAL 級別事件
        """
        event = {
            "date": datetime.now().isoformat(),
            "event_type": "Oil_Supply_Shock_Risk",
            "location": "波斯灣-荷姆茲海峽",
            "severity": "CRITICAL",
            "llm_risk_score": 0.95,
            "summary": f"群聚異常觸發 ({anomaly_type})：建議 buy XLE (能源ETF) / activate S5 (做空科技股)",
            "impact_assets": "XLE,XOP,USO,WTI,S5",
        }

        self._write_event(event)

        # get_latest_intel_risk() 將讀取此 0.95 分數，自動觸發 M1 決策引擎
        try:
            risk_score = get_latest_intel_risk(hours=24)
            logger.info(f"[M1] 最新風險分數: {risk_score}")
        except Exception as e:
            logger.debug(f"無法讀取風險分數: {e}")
