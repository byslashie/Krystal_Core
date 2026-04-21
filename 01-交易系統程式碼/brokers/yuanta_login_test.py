# brokers/yuanta_login_test.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import pythonnet
pythonnet.load("netfx")
import clr

# 1) 設定路徑與載入 DLL
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.append(str(LIB_DIR))

# 讀 .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

clr.AddReference("YuantaOneAPI")

from YuantaOneAPI import YuantaOneAPITrader, enumEnvironmentMode, enumLogType

def main():
    print("=== Yuanta Login Test ===")
    account = os.getenv("YUANTA_ACCOUNT", "").strip()
    password = os.getenv("YUANTA_PASSWORD", "").strip()
    env = os.getenv("YUANTA_ENV", "PROD").upper()
    
    print(f"ENV: {env}")
    print(f"ACCOUNT: {account}")

    if not account or not password:
        print("❌ 錯誤：.env 缺少 YUANTA_ACCOUNT 或 YUANTA_PASSWORD")
        return

    try:
        api = YuantaOneAPITrader()
        api.SetLogType(enumLogType.COMMON)
        api.SetPopUpMsg(False)
        
        mode = enumEnvironmentMode.PROD if env == "PROD" else enumEnvironmentMode.UAT
        
        print("1) Calling Open()...")
        api.Open(mode)
        
        import time
        print("Waiting for initialization (2s)...")
        time.sleep(2.0)
        
        print("2) Calling Login()...")
        # 這裡可能會拋出 NullReferenceException 如果 DLL 或環境有問題
        ok = api.Login(account, password)
        print(f"Login() return value: {ok}")
        
        if ok:
            print("✅ 指令已送出。請確認 Windows 憑證存放區已有正確憑證。")
        else:
            print("⚠️ Login() 回傳 False，請檢查帳號密碼或環境設定。")

    except Exception as e:
        print(f"❌ 發生異常：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
