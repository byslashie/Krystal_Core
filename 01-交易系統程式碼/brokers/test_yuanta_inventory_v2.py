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
    try:
        # e is usually an EventArgs containing the response
        # Yuanta API OnResponse standard args: sender: object, e: OnResponseEventArgs
        print(f"  ResultNo: {getattr(e, 'ResultNo', 'N/A')}")
        print(f"  FunctionID: {getattr(e, 'FunctionID', 'N/A')}")
        print(f"  Data: {getattr(e, 'Data', 'N/A')}")
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

    time.sleep(5) 
    
    print("\n--- Inspecting RQ ---")
    print(f"type(api.RQ): {type(api.RQ)}")
    
    print("\n--- Sending RQ(0015) - Stock Position ---")
    helper = YuantaDataHelper()
    
    try:
        # Try direct call
        res = api.RQ("0015", helper)
        print(f"RQ(0015) direct call result: {res}")
    except Exception as err:
        print(f"Direct call failed: {err}")
        try:
            # Try Overloads
            res = api.RQ.Overloads[str, YuantaDataHelper]("0015", helper)
            print(f"RQ(0015) via Overloads result: {res}")
        except Exception as err2:
            print(f"Overloads call failed: {err2}")
    
    # Wait for response
    print("Waiting 15 seconds for events...")
    for i in range(15):
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
