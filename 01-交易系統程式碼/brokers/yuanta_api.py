# brokers/yuanta_api.py
# Pythonnet 正規版：憑證走 Windows Cert Store（不要 SetCert/LoadCert）
import os
import sys
from pathlib import Path
from datetime import datetime
import struct

from dotenv import load_dotenv

# ===== 1) 讀 .env（固定讀專案根目錄）=====
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ===== 2) 準備 DLL 路徑 =====
# 你的 DLL 放在專案根目錄 /lib
LIB_DIR = PROJECT_ROOT / "lib"
if not LIB_DIR.exists():
    raise RuntimeError(f"找不到 lib 資料夾：{LIB_DIR}")

# pythonnet 需要能在 sys.path 找到 DLL
sys.path.append(str(LIB_DIR))

# ===== 3) Import pythonnet / clr（僅 Windows）=====
import platform
import time

_CLR_OK = False
_CLR_ERR = None

if platform.system() == "Windows":
    try:
        import pythonnet
        # pythonnet 3.x 需要指定載入 netfx (或用預設)
        try:
            pythonnet.load("netfx")
        except:
            pass
        import clr  # pythonnet 提供
        _CLR_OK = True
    except Exception as e:
        _CLR_OK = False
        _CLR_ERR = e
else:
    # macOS / Linux：不嘗試 import clr
    _CLR_OK = False
    _CLR_ERR = RuntimeError("Yuanta API 只支援 Windows (.NET Framework)")
    class clr_stub:
        def AddReference(self, name):
            raise _CLR_ERR
    clr = clr_stub()

# ===== 4) AddReference DLL =====
DLL_NAME = "YuantaOneAPI"
if _CLR_OK:
    try:
        asm = clr.AddReference(DLL_NAME)
        # 強制使用多種協定包含 TLS 1.2
        clr.AddReference("System")
        import System.Net
        protocols = System.Net.SecurityProtocolType.Tls12
        try:
            protocols |= System.Net.SecurityProtocolType.Tls11 | System.Net.SecurityProtocolType.Tls
        except:
            pass
        System.Net.ServicePointManager.SecurityProtocol = protocols
        
        # 繞過憑證驗證 (排除 UAT 憑證問題)
        def validation_callback(sender, cert, chain, errors):
            return True
        System.Net.ServicePointManager.ServerCertificateValidationCallback = \
            System.Net.Security.RemoteCertificateValidationCallback(validation_callback)
            
        print(f"DEBUG: TLS protocols and Cert Bypass enabled.")
    except Exception as e:
        raise RuntimeError(
            f"clr.AddReference('{DLL_NAME}') 失敗。\n"
            f"請確認 {LIB_DIR} 內有 {DLL_NAME}.dll，且 DLL 未被封鎖。\n"
            f"原始錯誤：{e}"
        )
else:
    asm = None

# ===== 5) 匯入元大命名空間/類別 =====
if _CLR_OK:
    from YuantaOneAPI import (
        YuantaOneAPITrader,
        enumEnvironmentMode,
        enumLogType,
    )
else:
    class YuantaOneAPITrader: pass
    class enumEnvironmentMode: pass
    class enumLogType: pass

def _env_mode() -> str:
    v = (os.getenv("YUANTA_ENV") or "PROD").strip().upper()
    return "UAT" if v in ("UAT", "TEST", "SANDBOX") else "PROD"

def yuanta_login() -> YuantaOneAPITrader:
    if not _CLR_OK:
        raise RuntimeError(
            "無法 import clr（pythonnet 未正常安裝或環境不一致）。"
            "\n- 目前 OS: " + platform.system() +
            "\n- Windows 請用 venv 的 python 重新安裝："
            " .\\.venv\\Scripts\\python.exe -m pip install -U pythonnet"
            "\n- 若你在 macOS：元大 DLL 只能在 Windows 執行，"
            "請改用 Windows 執行節點或同步成交資料。"
            "\n原始錯誤：" + str(_CLR_ERR)
        )

    """
    ✅ Pythonnet 正規登入方式：
    - 不用 SetCert/LoadCert
    - 憑證必須先安裝到 Windows（Current User / Personal）
    """
    # 下面接你原本的程式碼...
    account = (os.getenv("YUANTA_ACCOUNT") or "").strip()
    password = (os.getenv("YUANTA_PASSWORD") or "").strip()

    if not account or not password:
        raise RuntimeError("❌ .env 缺少 YUANTA_ACCOUNT / YUANTA_PASSWORD")

    env = _env_mode()
    target_env = enumEnvironmentMode.PROD if env == "PROD" else enumEnvironmentMode.UAT

    print(f"DEBUG: .env loaded: {ENV_PATH}")
    print(f"DEBUG: lib_dir={LIB_DIR}")
    print(f"DEBUG: Assembly loaded: {asm.FullName}")
    print(f"DEBUG: env={env}, account={account}")

    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(True)

    # === 用一個標誌來追蹤登入狀態 ===
    login_confirmed = [False]  # 使用列表以便在嵌套函數中修改
    login_error = [None]

    # 監聽所有事件以便除錯和登入確認
    def on_all_resp(intMark, dwIndex, strIndex, objHandle, objValue):
        try:
            # 印出所有事件細節（協助除錯）
            print(f"  [RAW_EVENT] intMark={intMark}, dwIndex={dwIndex}, strIndex='{strIndex}', data={str(objValue)[:80]}")
            if intMark == 0:  # 連線/系統事件
                print(f"  [CONN_EVENT] dwIndex={dwIndex}, {objValue}")
            elif intMark == 1:  # 查詢回應事件
                # 依 PDF：intMark=1, dwIndex=0 → 總帳/子帳登入成功
                if dwIndex == 0:
                    login_confirmed[0] = True
                    print(f"  [LOGIN_CONFIRMED] Login OK (dwIndex=0)")
                elif dwIndex == 3:
                    login_error[0] = 3
                    print(f"  [LOGIN_ERROR] 尚未登入 (dwIndex=3)")
                elif dwIndex == 4:
                    login_error[0] = 4
                    print(f"  [LOGIN_ERROR] 帳號錯誤 (dwIndex=4)")
                elif dwIndex == 9:
                    login_error[0] = 9
                    print(f"  [LOGIN_ERROR] 憑證異常 (dwIndex=9)")
                elif dwIndex == 7:
                    print(f"  [ERROR] SocketRPRead失敗 (dwIndex=7)")
                else:
                    print(f"  [RESPONSE] dwIndex={dwIndex}, data={str(objValue)[:80]}")
        except Exception as e:
            print(f"  [EVENT_HANDLER_ERROR] {e}")

    try:
        api.OnResponse += on_all_resp
    except Exception as e:
        print(f"  [Warning] 無法註冊 OnResponse 事件：{e}")

    # 1) Open
    print(f"Open() 連線環境：{env}")
    api.Open(target_env)

    # 延遲拉長到 5 秒，確保背景連線與 SSL Handshake 完成
    print("等待 API 初始化與連線 (5s)...")
    time.sleep(5.0)

    # 2) Login（直接用原始帳號，不填充 null bytes）
    print("Login() 送出登入...")
    ok = api.Login(account, password)

    if ok:
        print("Login() 已送出（回傳 True）")
    else:
        print("Login() 回傳 False（帳號格式/環境/參數可能有誤）")

    # 3) 等待登入確認（最多 10 秒）
    print("[WAIT] 等待登入確認中...")
    for i in range(10):
        if login_confirmed[0]:
            print(f"  [OK] 登入確認成功！")
            break
        time.sleep(1)
        print(f"  ... {i+1}s")

    if not login_confirmed[0]:
        print(f"  [WARN] 登入確認未收到，繼續嘗試...")

    return api


class YuantaFillContainer:
    """容器：用來捕獲元大 API 的非同步事件（成交回報）"""
    def __init__(self):
        self.fills = []
        self.positions = []  # 新增：暫存庫存資料

    def on_response(self, *args):
        """
        元大 OnResponse 事件回呼 (5 個參數)
        [1]: ResultNo (int)
        [2]: FunctionID (str)
        [3]: ResultMsg (str)
        [4]: Data (str)
        """
        if len(args) < 5:
            return
            
        result_no = args[1]
        function_id = str(args[2]).strip()
        result_msg = str(args[3]).strip()
        obj_value = args[4]
        data_str = ""
        
        # 處理 System.Byte[]
        if "Byte[]" in str(type(obj_value)):
            try:
                # 轉為 Python bytes
                py_bytes = bytes(obj_value)
                # 嘗試解碼為 cp950 (成功代表可能是字串格式)
                try:
                    data_str = py_bytes.decode('cp950').strip('\x00').strip()
                except:
                    # 否則轉為 hex 方便除錯
                    data_str = f"HEX:{py_bytes.hex()}"
            except:
                data_str = "[Bytes Conversion Failed]"
        else:
            data_str = str(obj_value).strip()
        
        print(f"DEBUG: Yuanta OnResponse triggered! ResultNo={result_no}, ID={function_id}, Type={type(obj_value)}, Data={data_str}")

        # === 詳細日誌：記錄所有響應 ===
        # 這有助於診斷登入、認證等非查詢類的響應
        if result_no == 0:
            print(f"  [OK] {data_str}")
        elif result_no == 7:
            print(f"  [NOT_LOGGED_IN] {data_str}")
        else:
            print(f"  [ResultNo={result_no}] {data_str}")

        # RtnCode=141 是正常的憑證驗證回應，不應中止後續處理
        # 只記錄但繼續處理其他數據
        if "141" in data_str or "憑證" in data_str:
            print(f"[CERT] Yuanta 偵測到憑證相關回應（RtnCode=141）：{data_str}")

        # 0015 或 20.103.0.22 是證券庫存查詢
        if "0015" in function_id or "20.103.0.22" in function_id or \
           "0015" in data_str or "20.103.0.22" in data_str:
            if "執行異常" not in data_str:
                if "Byte[]" in str(type(obj_value)):
                    try:
                        py_bytes = bytes(obj_value)
                        # 20.103.0.22 格式解析 (依據元大手冊)
                        # 前 4 bytes 是筆數 (或 header)，每筆長度固定
                        if len(py_bytes) > 4:
                            count = struct.unpack('>I', py_bytes[0:4])[0] if len(py_bytes) >= 4 else 0
                            # 實測發現 count 可能很大或是其他意義，我們用長度遍歷
                            # 單筆長度估計為 200 (依據手冊欄位加總)
                            record_size = 200 # 保守估計，後面解析用 offset
                            
                            # 遍歷所有可能紀錄 (UAT/PROD 筆數通常不多)
                            # 每一筆 offset 相對位移，這裡直接依據手冊的 Absolute Offset
                            # 帳號(22), 交易類別(2), 市場(1), 名稱(30), 代號(12), 名稱(30), 股數(8), 均價(8)
                            # 因為是流動長度，我們抓取關鍵代號的位置
                            # 依據手冊: 帳號(0), 代號(55), 股數(97), 均價(105)
                            # 扣除 header 4 bytes 後，每筆間距通常是 180~200
                            # 我們尋找 Account String 的出現來切分
                            account_pattern = bytes(os.getenv("YUANTA_ACCOUNT") or "S989", 'ascii')
                            
                            start_idx = 4
                            while start_idx + 150 < len(py_bytes):
                                try:
                                    # 尋找下一個帳號出發點
                                    chunk = py_bytes[start_idx : start_idx + 200]
                                    stk_code = py_bytes[start_idx + 55 : start_idx + 67].decode('cp950').strip('\x00').strip()
                                    stk_name = py_bytes[start_idx + 67 : start_idx + 97].decode('cp950').strip('\x00').strip()
                                    
                                    # 手冊偏移量 (0-based): 股數(97), 均價(105), 成本(113)
                                    stk_nos = struct.unpack('>q', py_bytes[start_idx + 97 : start_idx + 105])[0]
                                    # offset 105: avgCost × 10000（冗餘欄位）
                                    field_105 = struct.unpack('>q', py_bytes[start_idx + 105 : start_idx + 113])[0]
                                    # offset 113: 總成本（NTD），/ stk_nos = 均價/股
                                    stk_total_cost = struct.unpack('>q', py_bytes[start_idx + 113 : start_idx + 121])[0]

                                    # offset 137 hi(4B): 可賣股數
                                    sellable = struct.unpack('>I', py_bytes[start_idx + 141 : start_idx + 145])[0]

                                    # offset 161 lo(4B): 現價 × 10000
                                    current_price = struct.unpack('>I', py_bytes[start_idx + 161 : start_idx + 165])[0] / 10000.0 if start_idx + 165 <= len(py_bytes) else 0.0
                                    # offset 169: [買入價 × 10000 | 賣出價 × 10000]
                                    bid_price = struct.unpack('>I', py_bytes[start_idx + 169 : start_idx + 173])[0] / 10000.0 if start_idx + 173 <= len(py_bytes) else 0.0
                                    ask_price = struct.unpack('>I', py_bytes[start_idx + 173 : start_idx + 177])[0] / 10000.0 if start_idx + 177 <= len(py_bytes) else 0.0
                                    # offset 177: [漲停 × 10000 | 跌停 × 10000]
                                    limit_up   = struct.unpack('>I', py_bytes[start_idx + 177 : start_idx + 181])[0] / 10000.0 if start_idx + 181 <= len(py_bytes) else 0.0
                                    limit_down = struct.unpack('>I', py_bytes[start_idx + 181 : start_idx + 185])[0] / 10000.0 if start_idx + 185 <= len(py_bytes) else 0.0

                                    # 均價 = 總成本 / 股數
                                    avg_cost = float(stk_total_cost) / float(stk_nos) if stk_nos > 0 else 0.0

                                    if stk_code and stk_nos > 0:
                                        # 格式：0,0,0,0,Symbol,0,Qty,AvgCost,TotalCost,Field105,0,0,Sellable,CurrentPrice,Bid,Ask,LimitUp,LimitDown
                                        csv_line = (
                                            f"0,0,0,0,{stk_code},0,{stk_nos},{avg_cost:.4f},"
                                            f"{stk_total_cost},{field_105},0,0,"
                                            f"{sellable},{current_price:.4f},{bid_price:.4f},{ask_price:.4f},"
                                            f"{limit_up:.4f},{limit_down:.4f}"
                                        )
                                        self.positions.append(csv_line)
                                        print(f"  [PARSED] {stk_code}: {stk_nos}股, 均價:{avg_cost:.2f}, 現價:{current_price:.2f}, 漲停:{limit_up:.2f}")
                                    
                                    start_idx += 180 # 假設每筆長度 180 (或更高)
                                    # 真正的 record_size 可能不同，我們在 chunk 裡尋找下一個帳號
                                    next_acc = py_bytes.find(account_pattern, start_idx)
                                    if next_acc != -1:
                                        start_idx = next_acc
                                    else:
                                        break
                                except:
                                    break
                        else:
                            self.positions.append(data_str)
                    except Exception as e:
                        print(f"⚠️ 解析二進位庫存失敗: {e}")
                        self.positions.append(data_str)
                else:
                    self.positions.append(data_str)
            else:
                print(f"⚠️ [YUANTA_API] 庫存查詢失敗回報：{data_str}")
        else:
            # 排除明顯的執行異常訊息，避免干擾成交同步
            if "執行異常" not in data_str:
                self.fills.append(data_str)
            else:
                print(f"⚠️ [YUANTA_API] 系統回報異常：{data_str}")

# 全域或單例，方便存取
_container = YuantaFillContainer()

def fetch_fills(api: YuantaOneAPITrader) -> list:
    """
    從捕獲容器中取得累積的成交資料，並清空容器以供下次使用。
    """
    global _container
    data = list(_container.fills)
    _container.fills = []
    return data

def register_events(api: YuantaOneAPITrader):
    """註冊事件監聽器"""
    global _container
    try:
        # 註冊 OnResponse 事件 (注意：pythonnet 3.x 語法)
        # 雖然反射顯示 1 個參數，但實測為 5 個，pythonnet 會自動處理
        api.OnResponse += _container.on_response
        print("Yuanta OnResponse 事件註冊成功")
    except Exception as e:
        print(f"Yuanta 事件註冊失敗：{e}")

def query_stock_positions(api: YuantaOneAPITrader):
    """
    發送證券庫存查詢 (Function ID: 0015)
    """
    global _container
    account = (os.getenv("YUANTA_ACCOUNT") or "").strip()
    if not account:
        print("❌ 查詢失敗：.env 缺少 YUANTA_ACCOUNT")
        return False
        
    try:
        from YuantaOneAPI import YuantaDataHelper
        helper = YuantaDataHelper()
        helper.initial()

        # 使用 20.103.0.22 (SummaryReport 現貨庫存綜合總表)
        # 依規格：SetUInt(1) = 查1個帳號, SetTByte(account, 22) = 帳號欄位(22 bytes)
        helper.SetFunctionID(20, 103, 0, 22)
        helper.SetUInt(1)           # 查詢帳號數量 = 1
        helper.SetTByte(account, 22)  # 帳號字串，欄位長度 22

        print(f"發送庫存查詢 RQ(ID: 20.103.0.22, Account: {account})...")
        ok = api.RQ(account, helper)
        if not ok:
            print("RQ(20.103.0.22) 指令發送失敗")
        return ok
    except Exception as e:
        print(f"❌ RQ(20.103.0.22) 呼叫異常：{e}")
        return False

def fetch_positions(api: YuantaOneAPITrader) -> list:
    """
    從容器中取得暫存的庫存原始數據
    """
    global _container
    data = list(_container.positions)
    _container.positions = []
    return data


def main():
    try:
        api = yuanta_login()
        print("✅ yuanta_login() 流程完成（已建立 API instance）")
        
        # 註冊事件監聽
        register_events(api)
        
        print("下一步：等待成交回報事件 (OnExecution) 並寫入 broker_fills 分頁")
        # 測試呼叫 fetch_fills
        fills = fetch_fills(api)
        print(f"目前緩存成交筆數: {len(fills)}")
        
        # 先不要讓程式秒退（有些登入/事件需要時間）
        print("等待 10 秒測試事件捕獲...")
        import time
        for _ in range(10):
            time.sleep(1)
            f = fetch_fills(api)
            if f:
                print(f"捕獲到新成交：{len(f)}")
        
        input("Press Enter to exit...")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
