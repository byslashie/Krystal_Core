import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import YuantaOneAPITrader, enumEnvironmentMode, enumLogType, YuantaDataHelper

# Load .env
load_dotenv()

account = os.getenv("YUANTA_ACCOUNT", "").strip()
password = os.getenv("YUANTA_PASSWORD", "").strip()

def on_response(sender, e):
    print(f"\n[EVENT] OnResponse triggered!")
    print(f"DEBUG: e type: {type(e)}")
    # Try to list members of e
    try:
        for m in dir(e):
            if not m.startswith('__'):
                val = getattr(e, m, "N/A")
                print(f"  {m}: {val}")
    except Exception as err:
        print(f"  Error inspecting e: {err}")

def main():
    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(False)
    
    api.OnResponse += on_response
    
    print("Connecting...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(3)
    
    print(f"Logging in with {account}...")
    ok = api.Login(account, password)
    print(f"Login result: {ok}")
    
    if not ok:
        return

    time.sleep(5) # Wait for login sequence
    
    print("\n--- Sending RQ(0015) - Stock Position ---")
    helper = YuantaDataHelper()
    # For Stock Position 0015, we might need to set the account type if it supports multiple
    # But usually just calling it might work if already logged in
    
    res = api.RQ("0015", helper)
    print(f"RQ(0015) sent: {res}")
    
    # Wait for response
    print("Waiting 10 seconds for events...")
    for i in range(10):
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
