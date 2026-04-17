# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import gspread
    from google.oauth2.service_account import Credentials
    
    sheet_key = os.getenv("GOOGLE_SHEET_KEY", "")
    creds_file = "credentials.json"
    
    if not sheet_key:
        print("ERROR: GOOGLE_SHEET_KEY not in .env")
        exit(1)
    
    if not os.path.exists(creds_file):
        print("ERROR: credentials.json not found")
        exit(1)
    
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_file, scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(sheet_key)
    ws = sheet.worksheet("broker_positions")
    data = ws.get_all_records()
    
    if data:
        print("\n=== 元大最新庫存 (最後5筆) ===\n")
        for row in data[-5:]:
            print(row)
    else:
        print("No positions found")
        
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
