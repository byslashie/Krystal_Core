import os
import sys
import subprocess
from pathlib import Path

def main():
    # 取得專案根目錄 (Krystal_完整系統)
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    if sys.platform == "win32":
        bat_path = repo_root / "01-交易系統程式碼" / "START_DASHBOARD_V8.bat"
        print(f"📍 偵測到 Windows 系統，準備啟動: {bat_path}")
        if not bat_path.exists():
            print(f"❌ 找不到檔案: {bat_path}")
            sys.exit(1)
        # Windows 使用 os.startfile 確保能正確啟動 cmd 視窗並駐留
        os.startfile(str(bat_path))
        
    elif sys.platform == "darwin":
        # 如果是 Mac，使用您原本的腳本路徑
        mac_path = "/Users/chenyu/Desktop/Krystal_完整系統/01-交易系統程式碼/啟動交易系統.command"
        print(f"📍 偵測到 macOS 系統，準備啟動: {mac_path}")
        if not Path(mac_path).exists():
            print(f"⚠️ 找不到絕對路徑檔案: {mac_path}")
            print("嘗試使用相對路徑...")
            mac_path = str(repo_root / "01-交易系統程式碼" / "啟動交易系統.command")
            
        subprocess.Popen(['open', mac_path])
        
    else:
        print(f"❌ 不支援的作業系統: {sys.platform}")

if __name__ == "__main__":
    main()
