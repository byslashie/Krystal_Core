"""
🌊 AIS 數據爬蟲
取得波斯灣實時油輪位置數據
支持多個免費數據源
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time

try:
    from .config import (
        GULF_REGION,
        VESSEL_TYPES,
        SCRAPER_CONFIG,
        AISHUB_CONFIG,
        VESSEL_FINDER_CONFIG,
        DATA_SOURCE,
        MOCK_DATA,
        DEBUG,
    )
except ImportError:
    from config import (
        GULF_REGION,
        VESSEL_TYPES,
        SCRAPER_CONFIG,
        AISHUB_CONFIG,
        VESSEL_FINDER_CONFIG,
        DATA_SOURCE,
        MOCK_DATA,
        DEBUG,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISDataSource:
    """抽象基類：AIS 數據源"""

    def fetch_vessels(self) -> List[Dict]:
        """獲取油輪數據"""
        raise NotImplementedError


class AISHubScraper(AISDataSource):
    """AIS Hub 免費 API 爬蟲"""

    def __init__(self):
        self.api_key = AISHUB_CONFIG["api_key"]
        self.base_url = AISHUB_CONFIG["base_url"]
        self.timeout = SCRAPER_CONFIG["request_timeout"]
        self.max_retries = SCRAPER_CONFIG["max_retries"]

    def fetch_vessels(self) -> List[Dict]:
        """
        從 AIS Hub 獲取波斯灣油輪
        API: http://www.aishub.net/api/ref/index.php
        """
        region = GULF_REGION

        params = {
            "type": "ship",
            "format": "json",
            "latmin": region["lat_min"],
            "latmax": region["lat_max"],
            "lonmin": region["lon_min"],
            "lonmax": region["lon_max"],
        }

        if self.api_key and self.api_key != "free":
            params["key"] = self.api_key

        vessels = []
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                logger.info(
                    f"🔄 正在從 AIS Hub 獲取數據... (嘗試 {retry_count + 1}/{self.max_retries})"
                )
                response = requests.get(
                    self.base_url, params=params, timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()

                if isinstance(data, dict):
                    # AIS Hub 通常返回 {"ships": [...]} 或直接列表
                    ship_list = data.get("ships", []) or list(data.values())
                elif isinstance(data, list):
                    ship_list = data
                else:
                    logger.warning(f"⚠️ 未預期的數據格式: {type(data)}")
                    ship_list = []

                # 篩選油輪
                for ship in ship_list:
                    if self._is_tanker(ship):
                        vessel = self._normalize_vessel_data(ship, "aishub")
                        vessels.append(vessel)

                logger.info(
                    f"✅ 成功獲取 {len(vessels)} 艘波斯灣油輪 (來源: AIS Hub)"
                )
                return vessels

            except requests.exceptions.RequestException as e:
                retry_count += 1
                logger.warning(
                    f"⚠️ AIS Hub 連線失敗 ({e})，{SCRAPER_CONFIG['retry_delay']} 秒後重試..."
                )
                time.sleep(SCRAPER_CONFIG["retry_delay"])
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 解析失敗: {e}")
                break

        logger.error("❌ 無法從 AIS Hub 獲取數據，使用本地模擬數據")
        return self._get_mock_data()

    def _is_tanker(self, ship: Dict) -> bool:
        """檢查是否為油輪"""
        ship_type = ship.get("shiptype", "").lower()
        ship_type_code = ship.get("type", "")

        # 檢查船舶類型名稱
        for tanker_type in VESSEL_TYPES:
            if tanker_type.lower() in ship_type:
                return True

        # 檢查 MMSI 類型代碼（通常 3 開頭 = 油輪）
        if ship_type_code.startswith("3"):
            return True

        return False

    def _normalize_vessel_data(self, ship: Dict, source: str) -> Dict:
        """正規化船舶數據格式"""
        return {
            "source": source,
            "mmsi": str(ship.get("mmsi", ship.get("MMSI", ""))),
            "imo": ship.get("imo", ship.get("IMO", "")),
            "vessel_name": ship.get("shipname", ship.get("SHIPNAME", "Unknown")),
            "vessel_type": ship.get("shiptype", ship.get("TYPE", "")),
            "flag": ship.get("flag", ship.get("FLAG", "")),
            "latitude": float(ship.get("latitude", ship.get("LAT", 0))),
            "longitude": float(ship.get("longitude", ship.get("LON", 0))),
            "speed": float(ship.get("speed", ship.get("SPEED", 0))),
            "heading": int(ship.get("heading", ship.get("HEADING", 0))),
            "destination": ship.get("destination", ship.get("DESTINATION", "")),
            "origin_port": ship.get("origin_port", ship.get("ORIGIN_PORT", "")),
            "last_update": ship.get(
                "timestamp", ship.get("TIMESTAMP", datetime.now().isoformat())
            ),
            "status": "active",
        }

    def _get_mock_data(self) -> List[Dict]:
        """本地模擬數據用於測試"""
        return [
            {
                "source": "mock",
                "mmsi": "636012814",
                "imo": "9634555",
                "vessel_name": "PACIFIC OCEAN",
                "vessel_type": "Oil Tanker",
                "flag": "SG",
                "latitude": 26.5,
                "longitude": 52.5,
                "speed": 12.5,
                "heading": 45,
                "destination": "鹿特丹 (ROTABQ)",
                "origin_port": "拉斯坦努拉 (SAIQA)",
                "last_update": datetime.now().isoformat(),
                "status": "active",
            },
            {
                "source": "mock",
                "mmsi": "211378570",
                "imo": "9388494",
                "vessel_name": "ASIAN GLORY",
                "vessel_type": "Oil Tanker",
                "flag": "IR",
                "latitude": 27.2,
                "longitude": 51.8,
                "speed": 0.0,
                "heading": 0,
                "destination": "高雄港 (TWHAO)",
                "origin_port": "霍爾木茲海峽 (IRHMU)",
                "last_update": datetime.now().isoformat(),
                "status": "stationary",
            },
            {
                "source": "mock",
                "mmsi": "538008776",
                "imo": "9369078",
                "vessel_name": "ISLAMIC REPUBLIC",
                "vessel_type": "Crude Oil Tanker",
                "flag": "IR",
                "latitude": 26.1,
                "longitude": 50.5,
                "speed": 8.3,
                "heading": 120,
                "destination": "新加坡 (SGSIN)",
                "origin_port": "基斯克島 (IRKHIS)",
                "last_update": datetime.now().isoformat(),
                "status": "active",
            },
        ]


class AISScraperFactory:
    """工廠模式：根據配置選擇數據源"""

    @staticmethod
    def get_scraper(source: str = None) -> AISDataSource:
        if source is None:
            source = DATA_SOURCE

        if source == "aishub":
            return AISHubScraper()
        elif source == "mock":
            # 強制使用模擬數據
            scraper = AISHubScraper()
            scraper.fetch_vessels = scraper._get_mock_data
            return scraper
        else:
            logger.warning(f"⚠️ 未知的數據源 '{source}'，使用 AIS Hub")
            return AISHubScraper()


def fetch_gulf_tankers(use_mock: bool = None) -> List[Dict]:
    """便利函數：直接取得波斯灣油輪數據"""
    use_mock = use_mock or MOCK_DATA

    if use_mock:
        logger.info("📊 使用模擬數據模式")
        scraper = AISScraperFactory.get_scraper("mock")
        return scraper._get_mock_data()
    else:
        scraper = AISScraperFactory.get_scraper()
        return scraper.fetch_vessels()


if __name__ == "__main__":
    # 測試爬蟲
    logger.info("🚀 測試 AIS 爬蟲...")

    tankers = fetch_gulf_tankers(use_mock=True)
    print(f"\n獲得 {len(tankers)} 艘油輪：")
    for t in tankers:
        print(
            f"  🚢 {t['vessel_name']} (MMSI: {t['mmsi']}) @ ({t['latitude']:.2f}, {t['longitude']:.2f})"
        )
