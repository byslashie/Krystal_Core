import sqlite3
import os
from pathlib import Path

# 使用與 app.py 一致的路徑邏輯
db_path = Path(r"c:\Projects\Krystal_完整系統\01-交易系統程式碼\dashboard_v8\broker_positions.db")
if not db_path.exists():
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(str(db_path))
c = conn.cursor()
try:
    c.execute("SELECT * FROM equity_snapshots ORDER BY date DESC LIMIT 20;")
    rows = [r for r in c.fetchall()]
    if not rows:
        print("Table equity_snapshots is empty.")
    else:
        for row in rows:
            print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
