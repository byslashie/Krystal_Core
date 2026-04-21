#!/usr/bin/env python
"""
簡單 API 測試腳本
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, name):
    """測試 API 端點"""
    print(f"\n{'='*60}")
    print(f"[測試] {name}")
    print(f"{'='*60}")

    try:
        if method == "GET":
            res = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        else:
            res = requests.post(f"{BASE_URL}{endpoint}", timeout=10)

        print(f"[OK] 狀態碼: {res.status_code}")

        try:
            data = res.json()
            print(f"[OK] 回應格式: JSON")
            print(f"[內容]:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(f"[WARNING] 回應不是 JSON")
            print(f"[內容] {res.text[:500]}")

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] 無法連接到 {BASE_URL}")
        print(f"   請確認 Flask 服務已啟動 (python app_html_flask.py)")
    except Exception as e:
        print(f"[ERROR] 錯誤: {e}")

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print(f"\n[API 測試開始] ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"[目標]: {BASE_URL}\n")

    # 測試 IB API
    test_endpoint("GET", "/api/ib-account-summary", "IB 帳戶摘要")

    # 測試 Yuanta API
    test_endpoint("GET", "/api/yuanta-account-summary", "Yuanta 帳戶摘要")

    # 測試健康檢查
    test_endpoint("GET", "/api/health", "健康檢查")

    print(f"\n{'='*60}")
    print(f"[測試完成]\n")
