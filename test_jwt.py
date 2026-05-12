import time
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os

# Monkey-patch time to 2024 if we want, but let's first check normal
creds = service_account.Credentials.from_service_account_file('01-交易系統程式碼/credentials.json', scopes=["https://www.googleapis.com/auth/spreadsheets"])
try:
    creds.refresh(Request())
    print("SUCCESS normal")
except Exception as e:
    print(f"FAILED normal: {e}")

# Now patch time to 2024
import datetime
# 2024-05-11 timestamp is roughly 1715418000
real_time = time.time
def fake_time():
    return real_time() - (2 * 365 * 24 * 3600)  # subtract 2 years

time.time = fake_time
creds = service_account.Credentials.from_service_account_file('01-交易系統程式碼/credentials.json', scopes=["https://www.googleapis.com/auth/spreadsheets"])
try:
    creds.refresh(Request())
    print("SUCCESS patched")
except Exception as e:
    print(f"FAILED patched: {e}")

