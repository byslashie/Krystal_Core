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

def on_response(*args):
    print(f"\n[EVENT] OnResponse triggered! (Args count: {len(args)})")
    for i, val in enumerate(args):
        print(f"  [{i}]: {val} (type: {type(val)})")
    
    # args[4] is usually the data string
    if len(args) >= 5 and isinstance(args[4], str):
        print(f"  Data string: {args[4]}")

def main():
    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(False)
    
    # Register with 1 param as discovered by reflection
    api.OnResponse += on_response

    print("Connecting...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(3)
    
    print(f"Logging in with {account}...")
    ok = api.Login(account, password)
    print(f"Login result: {ok}")
    
    if not ok:
        return

    print("Waiting 10s for login to finalize...")
    time.sleep(10) 
    
    print("\n--- Sending RQ(0015) - Stock Position ---")
    helper = YuantaDataHelper()
    helper.initial()
    # "0015" -> Byte by Byte
    helper.SetFunctionID(ord('0'), ord('0'), ord('1'), ord('5'))
    
    try:
        # First arg is account number
        print(f"Calling api.RQ('{account}', helper)...")
        res = api.RQ(account, helper)
        print(f"RQ result: {res}")
    except Exception as err:
        print(f"RQ call failed: {err}")
        import traceback
        traceback.print_exc()
    
    # Wait for response
    print("Waiting 30 seconds for all potential events...")
    for i in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
