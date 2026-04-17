# 波斯灣油輪監測 - 配置檔

import os
from dotenv import load_dotenv

load_dotenv()

# ========== 監測區域配置 ==========
GULF_REGION = {
    "name": "波斯灣及周邊（Persian Gulf & Surroundings）",
    "lat_min": 22.0,  # 南邊界：阿曼/阿聯酋
    "lat_max": 33.0,  # 北邊界：伊朗南部
    "lon_min": 44.0,  # 西邊界：伊拉克
    "lon_max": 59.0,  # 東邊界：伊朗東部
}

# ========== 監測船舶類型 ==========
VESSEL_TYPES = [
    "Oil Tanker",
    "Chemical Tanker",
    "Products Tanker",
    "Crude Oil Tanker",
    "Tanker",
]

# ========== Telegram 設定 ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ========== 告警規則（嚴格模式）==========
ALERT_RULES = {
    "enter_region": True,  # 進入區域時告警
    "exit_region": True,  # 離開區域時告警
    "stationary_duration": 60,  # 停留 60 分鐘以上告警
    "speed_increase_threshold": 50,  # 速度增加 >50% 告警
    "speed_decrease_threshold": 50,  # 速度減少 >50% 告警
}

# ========== 爬蟲設定 ==========
SCRAPER_CONFIG = {
    "update_interval": 30,  # 每 30 秒更新一次
    "request_timeout": 10,
    "max_retries": 3,
    "retry_delay": 5,
}

# ========== 數據源選擇 ==========
# 選項: "aishub", "vesseltracker", "vessel_finder"
DATA_SOURCE = os.getenv("SHIP_DATA_SOURCE", "aishub")

# ========== AIS Hub API 設定 ==========
AISHUB_CONFIG = {
    "api_key": os.getenv("AISHUB_API_KEY", "free"),  # free 版本無需 key
    "base_url": "http://www.aishub.net/api/ref/index.php",
    "format": "json",
}

# ========== VesselFinder API 設定（備選）==========
VESSEL_FINDER_CONFIG = {
    "base_url": "https://api.vesselfinder.com/public/v2",
    "api_key": os.getenv("VESSEL_FINDER_API_KEY", ""),
}

# ========== 日誌設定 ==========
LOG_DIR = "./ship_monitoring/logs"
LOG_FILE = os.path.join(LOG_DIR, "ship_monitor.log")

# ========== Google Sheets 設定 ==========
SHEETS_CONFIG = {
    "tab_name": "ship_tracking",  # 新增的分頁名稱
    "columns": [
        "timestamp",
        "vessel_name",
        "mmsi",
        "imo",
        "vessel_type",
        "flag",
        "latitude",
        "longitude",
        "speed",
        "heading",
        "last_update",
        "status",
        "alert_type",
    ],
}

# ========== 狀態常數 ==========
VESSEL_STATUS = {
    "ACTIVE": "active",  # 移動中
    "STATIONARY": "stationary",  # 停止不動
    "ANCHORED": "anchored",  # 錨泊
    "TRANSITING": "transiting",  # 航行
    "MOORED": "moored",  # 靠泊
}

ALERT_TYPES = {
    "ENTERED_REGION": "entered_region",
    "EXITED_REGION": "exited_region",
    "STATIONARY": "stationary_alert",
    "SPEED_CHANGE": "speed_change",
    "NEW_VESSEL": "new_vessel_detected",
}

# ========== 開發模式 ==========
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
MOCK_DATA = os.getenv("MOCK_DATA", "False").lower() == "true"  # 使用模擬數據進行測試
