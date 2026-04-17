#!/usr/bin/env python3
"""
整合測試 - 驗證所有 API 端點
"""

import requests
import time
import sys
import json
from pathlib import Path

BASE_URL = "http://localhost:5000"
CSV_FILE = "260401_台股強勢股加碼-兩次_UTF8.csv"

# 色彩代碼
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_result(test_name, passed, message=""):
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"{status} | {test_name}")
    if message:
        print(f"    → {message}")

def test_backend_health():
    """測試後端健康狀態"""
    print(f"\n{BOLD}=== 測試 1: 後端健康檢查 ==={RESET}")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200
        print_result("Health Check", passed, f"狀態碼: {response.status_code}")
        return passed
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_csv_import():
    """測試 CSV 導入 API"""
    print(f"\n{BOLD}=== 測試 2: CSV 導入 ==={RESET}")
    try:
        csv_path = Path(CSV_FILE)
        if not csv_path.exists():
            print_result("CSV 導入", False, f"找不到文件: {CSV_FILE}")
            return False

        with open(csv_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/api/strategy/import", files=files, timeout=10)

        passed = response.status_code == 200 and response.json().get('status') == 'success'
        data = response.json()
        if passed:
            trades = data.get('preview', {}).get('total_trades', 0)
            profit = data.get('preview', {}).get('total_profit', 0)
            print_result("CSV 導入", True, f"成功解析 {trades} 筆交易，總獲利 {profit:.2f}")
        else:
            print_result("CSV 導入", False, data.get('message', '未知錯誤'))
        return passed
    except Exception as e:
        print_result("CSV 導入", False, str(e))
        return False

def test_charts_api():
    """測試圖表 API"""
    print(f"\n{BOLD}=== 測試 3: 專業圖表 API ==={RESET}")
    try:
        csv_path = Path(CSV_FILE)
        with open(csv_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/api/strategy/import/charts", files=files, timeout=10)

        passed = response.status_code == 200 and response.json().get('status') == 'success'
        data = response.json()
        if passed:
            metrics = data.get('metrics', {})
            print_result("圖表 API", True, f"CAGR: {metrics.get('cagr')}% | Sharpe: {metrics.get('sharpe_ratio')}")
        else:
            print_result("圖表 API", False, data.get('message', '未知錯誤'))
        return passed
    except Exception as e:
        print_result("圖表 API", False, str(e))
        return False

def main():
    print(f"\n{BOLD}{YELLOW}========================================{RESET}")
    print(f"{BOLD}Krystal AI Dashboard v8 - 整合測試{RESET}")
    print(f"{BOLD}{YELLOW}========================================{RESET}")

    print(f"\n{YELLOW}確保 Flask 服務器正在運行在 http://localhost:5000{RESET}")
    print(f"測試開始...")

    results = []
    results.append(("後端健康檢查", test_backend_health()))

    if results[0][1]:
        results.append(("CSV 導入", test_csv_import()))
        results.append(("專業圖表 API", test_charts_api()))

    # 總結
    print(f"\n{BOLD}{YELLOW}========================================{RESET}")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"{BOLD}測試結果: {passed}/{total} 通過{RESET}")

    if passed == total:
        print(f"{GREEN}✅ 所有測試通過！{RESET}")
        return 0
    else:
        print(f"{RED}❌ {total - passed} 個測試失敗{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
