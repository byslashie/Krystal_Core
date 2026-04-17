#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Dashboard v8 所有 API 端點
檢查哪些能用，哪些還是 Stub
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:9000"

def test_api(method, endpoint, description):
    """測試單個 API 端點"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)

        status = response.status_code
        try:
            data = response.json()
            # 檢查是否是 Stub（返回空值或 "not configured"）
            if status == 200:
                is_stub = (
                    not data.get('data') and
                    not data.get('accounts') and
                    not data.get('positions') and
                    "not configured" in str(data).lower()
                )
                status_text = "🔴 Stub" if is_stub else "✅ 可用"
            else:
                status_text = f"❌ {status}"
        except:
            status_text = f"❌ {status}"

        print(f"{status_text:12} {method:6} {endpoint:40} - {description}")
        return status == 200

    except requests.exceptions.ConnectionError:
        print(f"❌ 連接失敗   {method:6} {endpoint:40} - {description}")
        return False
    except Exception as e:
        print(f"❌ 錯誤       {method:6} {endpoint:40} - {description}")
        return False

# 測試所有 API
print("=" * 100)
print(f"Dashboard v8 API 端點檢查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)
print()

# 核心 API
print("📊 核心 API（交易 & 投資組合）")
print("-" * 100)
test_api("GET", "/api/trades/open", "未平倉交易")
test_api("GET", "/api/trades/realized", "已平倉交易")
test_api("GET", "/api/ytd-returns", "年初至今回報")
test_api("GET", "/api/portfolio-chart-data", "投資組合圖表數據")
test_api("GET", "/api/positions", "持倉列表")
test_api("GET", "/api/strategies", "交易策略")
print()

# 市場數據
print("📈 市場數據 API")
print("-" * 100)
test_api("GET", "/api/market-indices", "全球股市指數")
test_api("GET", "/api/macro-indicators", "宏觀經濟指標")
test_api("GET", "/api/yahoo-proxy", "實時股價")
print()

# 經紀商集成（Stub）
print("🏦 經紀商集成（應該都是 Stub）")
print("-" * 100)
test_api("GET", "/api/schwab/token-status", "Schwab Token 狀態")
test_api("GET", "/api/schwab-account-summary", "Schwab 帳戶摘要")
test_api("POST", "/api/schwab/sync-positions", "Schwab 同步持倉")
test_api("POST", "/api/schwab/sync-to-sheets", "Schwab 同步到 Sheets")
test_api("GET", "/api/query-ib", "IB 查詢")
test_api("POST", "/api/ib-sync", "IB 同步")
test_api("POST", "/api/sync-yuanta", "元大同步")
print()

# 系統 API
print("⚙️ 系統 API")
print("-" * 100)
test_api("GET", "/health", "健康檢查")
test_api("GET", "/api/test", "測試端點")
print()

# 資料操作
print("💾 資料操作 API")
print("-" * 100)
test_api("POST", "/api/sync-positions", "同步持倉")
test_api("POST", "/api/trades/add", "新增交易")
test_api("POST", "/api/snapshot", "拍攝快照")
test_api("GET", "/api/equity-history", "權益歷史")
print()

print("=" * 100)
print("🔍 檢查完成！")
print("=" * 100)
print()
print("說明：")
print("  ✅ 可用    - API 正常運作，返回真實或樣本數據")
print("  🔴 Stub   - API 已實現但返回空數據或占位符")
print("  ❌ 錯誤   - API 有問題或無法訪問")
print()
