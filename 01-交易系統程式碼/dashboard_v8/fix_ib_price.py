#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 IB 持倉的現價問題
使用 Yahoo Finance 補充缺失的 currentPrice
"""

import sqlite3
import yfinance as yf

DB_PATH = "broker_positions.db"

def get_price(symbol):
    """從 Yahoo Finance 獲取股價"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except:
        pass
    return None

# 連接數據庫
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 找所有 IB 持倉且 currentPrice 為 NULL 或 0
c.execute("""
    SELECT id, symbol, currentPrice 
    FROM broker_positions 
    WHERE broker = 'ib' AND (currentPrice IS NULL OR currentPrice = 0)
""")

rows = c.fetchall()
print(f"找到 {len(rows)} 個 IB 持倉需要補充現價\n")

for row_id, symbol, current_price in rows:
    price = get_price(symbol)
    if price:
        print(f"📈 {symbol:10} 現價: ${price:.2f}")
        c.execute(
            "UPDATE broker_positions SET currentPrice = ? WHERE id = ?",
            (price, row_id)
        )
    else:
        print(f"❌ {symbol:10} 無法獲取股價")

conn.commit()
conn.close()

print("\n✅ 現價更新完成！重新刷新網頁查看。")
