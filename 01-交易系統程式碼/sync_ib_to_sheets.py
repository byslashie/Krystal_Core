import json
import subprocess
import sys
import os
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_ib():
    try:
        # 1. 執行 query_ib_positions.py 獲取數據
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, 'query_ib_positions.py')
        
        logger.info("📡 正在從 IB TWS 獲取最新數據...")
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8', timeout=40)
        
        if result.returncode != 0:
            logger.error(f"❌ 查詢失敗: {result.stderr}")
            return False

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error(f"❌ 無法解析回傳的 JSON 數據：{result.stdout}")
            return False

        if data.get('status') != 'success':
            logger.error(f"❌ IB 查詢回傳錯誤指標：{data.get('message')}")
            return False

        # 2. 準備寫入 Google Sheets
        from sheets_utils import append_broker_snapshot, overwrite_broker_positions, read_sheet_data_with_cache

        # A. 更新 Snapshot
        snapshot_data = {
            "broker": "IB",
            "net_liquidation": data.get('net_liquidation_value', 0),
            "total_cash_value": data.get('total_cash_value', 0),
            "currency": "USD",
            "timestamp": data.get('timestamp')
        }
        append_broker_snapshot(snapshot_data)

        # B. 更新 Positions 並記錄出清至 trades
        from sheets_utils import sync_broker_positions_and_log_trades

        new_ib_positions = []
        for p in data.get('positions', []):
            new_ib_positions.append({
                "symbol": p.get('symbol'),
                "broker": "IB",
                "position": p.get('position'),
                "avgCost": p.get('avgCost'),
                "marketPrice": p.get('marketPrice'),
                "marketValue": p.get('marketValue'),
                "unrealizedPNL": p.get('unrealizedPNL'),
                "currency": p.get('currency'),
                "timestamp": data.get('timestamp')
            })
        
        sync_broker_positions_and_log_trades("IB", new_ib_positions)

        logger.info(f"✅ IB 數據同步完成！(資產: ${snapshot_data['net_liquidation']}, 持倉數: {len(new_ib_positions)})")
        return True

    except Exception as e:
        logger.error(f"❌ 同步過程發生異常：{e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = sync_ib()
    sys.exit(0 if success else 1)
