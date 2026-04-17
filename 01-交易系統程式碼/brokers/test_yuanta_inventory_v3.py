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

def on_response(data):
    print(f"\n[EVENT] OnResponse triggered!")
    print(f"type(data): {type(data)}")
    try:
        # data might be a comma-separated string or a structured object
        print(f"Content: {data}")
        # Try to inspect members if it's an object
        if not isinstance(data, str):
            for m in dir(data):
                if not m.startswith('__'):
                    print(f"  {m}: {getattr(data, m, 'N/A')}")
    except Exception as err:
        print(f"  Error inspecting data: {err}")

def main():
    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(False)
    
    # Try adding with 1 param
    try:
        api.OnResponse += on_response
        print("Registered on_response with 1 param")
    except Exception as e:
        print(f"Failed to register with 1 param: {e}")
        def on_response_2(sender, e):
            on_response(e)
        api.OnResponse += on_response_2
        print("Registered on_response_2 with 2 params")

    print("Connecting...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(3)
    
    print(f"Logging in with {account}...")
    ok = api.Login(account, password)
    print(f"Login result: {ok}")
    
    if not ok:
        return

    time.sleep(5) 
    
    print("\n--- Sending RQ(0015) - Stock Position ---")
    helper = YuantaDataHelper()
    helper.initial()
    helper.SetFunctionID("0015")
    
    # In some versions, you need to set account in the helper too
    # helper.SetTYuantaStkAccount(...)
    # But usually RQ(account, helper) is enough
    
    try:
        res = api.RQ(account, helper)
        print(f"RQ('{account}', helper) result: {res}")
    except Exception as err:
        print(f"RQ call failed: {err}")
    
    # Wait for response
    print("Waiting 15 seconds for events...")
    for i in range(15):
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
