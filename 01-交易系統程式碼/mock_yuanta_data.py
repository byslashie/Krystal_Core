"""
模擬 Yuanta 庫存數據生成器
用於測試 Dashboard v7 同步功能
"""
import json
from datetime import datetime

def generate_mock_positions():
    """生成模擬庫存數據"""
    return {
        "status": "success",
        "data": [
            {
                "symbol": "0050",
                "name": "元大台灣50",
                "quantity": 948,
                "avgPrice": 32.45,
                "currentPrice": 35.20,
                "market_value": 33377.6,
                "profit_loss": 2625.6,
                "profit_rate": 7.86,
                "broker": "元大",
                "timestamp": datetime.now().isoformat()
            },
            {
                "symbol": "006208",
                "name": "富邦台50",
                "quantity": 1471,
                "avgPrice": 28.15,
                "currentPrice": 30.85,
                "market_value": 45360.35,
                "profit_loss": 3979.35,
                "profit_rate": 9.63,
                "broker": "元大",
                "timestamp": datetime.now().isoformat()
            },
            {
                "symbol": "3158",
                "name": "唯晶科技",
                "quantity": 1000,
                "avgPrice": 15.50,
                "currentPrice": 16.80,
                "market_value": 16800,
                "profit_loss": 1300,
                "profit_rate": 8.39,
                "broker": "元大",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "summary": {
            "total_market_value": 95537.95,
            "total_profit_loss": 7905.0,
            "total_profit_rate": 8.27,
            "update_time": datetime.now().isoformat()
        }
    }

def save_mock_data():
    """保存模擬數據到 JSON 文件"""
    data = generate_mock_positions()

    with open("mock_positions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[OK] 模擬數據已生成：mock_positions.json")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    return data

if __name__ == "__main__":
    save_mock_data()
