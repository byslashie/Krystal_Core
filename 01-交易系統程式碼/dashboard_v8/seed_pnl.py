import sqlite3
from datetime import datetime, timedelta
import random

db_path = r"c:\Projects\Krystal_完整系統\01-交易系統程式碼\dashboard_v8\broker_positions.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 獲取今日日期
today = datetime.now()
target_pnl = 143360.0  # 基於剛才查詢到的數值

try:
    for i in range(20, 0, -1):
        date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        # 模擬成長與波動：每天損益稍微跳動 +- 2000
        sim_pnl = target_pnl - (i * 1500) + random.uniform(-2000, 2000)
        
        c.execute('''INSERT OR REPLACE INTO equity_snapshots
                     (date, total_pnl_twd, notes, usd_twd_rate)
                     VALUES (?, ?, ?, ?)''',
                  (date_str, round(sim_pnl, 2), "[Simulated]", 32.3))
    
    conn.commit()
    print("Successfully seeded 20 days of simulated data.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
