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

load_dotenv()
account = os.getenv("YUANTA_ACCOUNT", "").strip()
password = os.getenv("YUANTA_PASSWORD", "").strip()

def on_response(*args):
    print(f"\n[EVENT] OnResponse triggered! Args: {len(args)}")
    for i, arg in enumerate(args):
        print(f"  [{i}]: {arg}")

def main():
    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(True)
    api.OnResponse += on_response
    
    print("Open()...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(3)
    
    print(f"Login({account})...")
    ok = api.Login(account, password)
    print(f"Login result: {ok}")
    
    if not ok: return
    time.sleep(5)
    
    print("\n--- Test 1: RQ(account, helper) with char ords ---")
    h1 = YuantaDataHelper()
    h1.initial()
    h1.SetFunctionID(ord('0'), ord('0'), ord('1'), ord('5'))
    res = api.RQ(account, h1)
    print(f"Test 1 result: {res}")
    time.sleep(5)
    
    print("\n--- Test 2: RQ(account, helper) with string ---")
    h2 = YuantaDataHelper()
    h2.initial()
    # some versions take string
    try:
        h2.SetFunctionID("0015")
        res = api.RQ(account, h2)
        print(f"Test 2 result: {res}")
    except Exception as e:
        print(f"Test 2 failed: {e}")
    time.sleep(5)

if __name__ == "__main__":
    main()
