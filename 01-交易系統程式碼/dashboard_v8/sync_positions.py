#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 Google Sheets 持倉到本地 SQLite 數據庫
手動運行：python sync_positions.py
"""

import sqlite3
import sys
import io
from pathlib import Path

# 設定標準輸出編碼
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加父目錄到 path，以便導入 sheets_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from sheets_utils import read_sheet_data_with_cache

DB_PATH = Path(__file__).parent / 'broker_positions.db'

def init_db():
    """初始化本地 SQLite 數據庫"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS broker_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        position REAL,
        avgCost REAL,
        currentPrice REAL,
        marketValue REAL,
        unrealizedPnL REAL,
        broker TEXT,
        currency TEXT,
        timestamp DATETIME,
        synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        count INTEGER,
        status TEXT
    )''')

    conn.commit()
    conn.close()

def sync_from_google_sheets():
    """從 Google Sheets 同步持倉到本地數據庫"""
    try:
        print("[*] 開始從 Google Sheets 同步...")

        # 讀取 Google Sheets 的 broker_positions
        df = read_sheet_data_with_cache('broker_positions')
        if df is None or df.empty:
            print("❌ 無法從 Google Sheets 讀取數據")
            return False

        # 清空舊數據
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('DELETE FROM broker_positions')

        # 寫入新數據
        import pandas as pd
        for _, row in df.iterrows():
            def safe_float(val, default=None):
                """安全轉換為浮點數"""
                if pd.isna(val) or val == '' or val is None:
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            # 對應 Google Sheets 的欄位名稱
            # Google Sheets: 時間 → timestamp
            # Google Sheets: 券商 → broker
            # Google Sheets: currentPrice → marketPrice
            # Google Sheets: unrealizedPnL → unrealizedPNL

            symbol = str(row.get('symbol', '')).strip()
            if not symbol:
                continue  # 跳過空行

            c.execute('''INSERT INTO broker_positions
                (symbol, position, avgCost, currentPrice, marketValue, unrealizedPnL, broker, currency, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    symbol,
                    safe_float(row.get('position')),
                    safe_float(row.get('avgCost')),
                    safe_float(row.get('currentPrice')),
                    safe_float(row.get('marketValue')),
                    safe_float(row.get('unrealizedPnL')),
                    str(row.get('券商', row.get('broker', ''))).strip(),
                    str(row.get('currency', '')).strip(),
                    str(row.get('時間', row.get('timestamp', ''))).strip()
                )
            )

        # 記錄同步日誌
        count = len(df)
        c.execute('INSERT INTO sync_log (count, status) VALUES (?, ?)',
                 (count, 'success'))
        conn.commit()
        conn.close()

        print(f"✅ 同步成功：{count} 筆持倉數據")
        return True

    except Exception as e:
        print(f"❌ 同步失敗: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Broker Positions 同步 - 帶驗證")
    print("="*60 + "\n")

    # 步驟 1: 初始化本地數據庫
    print("[步驟 1/3] 初始化本地數據庫...")
    init_db()
    print()

    # 步驟 2: 同步數據
    print("[步驟 2/3] 從 Google Sheets 同步數據...")
    sync_from_google_sheets()
    print()

    # 步驟 3: 驗證同步結果
    print("[步驟 3/3] 驗證同步結果...")
    try:
        from validate_broker_schema import BrokerPositionsValidator
        validator = BrokerPositionsValidator()
        is_valid = validator.validate()

        if not is_valid:
            print("\n⚠️  警告：驗證發現問題")
            print("請運行: python validate_broker_schema.py 進行自動修復")
        else:
            print("\n✅ 同步完成且數據驗證通過！")
    except ImportError:
        print("\n⚠️  驗證器模組不可用，跳過驗證")
        print("提示：運行 python validate_broker_schema.py 來驗證數據")
