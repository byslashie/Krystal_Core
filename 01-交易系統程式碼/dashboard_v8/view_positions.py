#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看本地持倉數據"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'broker_positions.db'

def view_positions():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM broker_positions ORDER BY broker, symbol')
    positions = c.fetchall()
    
    print("\n" + "="*80)
    print("本地持倉數據")
    print("="*80)
    print(f"{'Symbol':<10} {'Position':>10} {'Avg Cost':>12} {'Market Price':>12} {'Broker':<15}")
    print("-"*80)
    
    for p in positions:
        print(f"{p['symbol']:<10} {p['position']:>10.2f} ${p['avgCost']:>11.2f} ${p['marketPrice']:>11.2f} {p['broker'] or 'N/A':<15}")
    
    print("-"*80)
    print(f"總計: {len(positions)} 筆持倉")
    
    # 查詢最後同步時間
    c.execute('SELECT MAX(synced_at) FROM broker_positions')
    last_sync = c.fetchone()[0]
    print(f"最後同步: {last_sync}")
    
    conn.close()

if __name__ == '__main__':
    view_positions()
