"""
decode_yuanta_binary.py
分析 20.103.0.22 回傳的 binary 欄位，用於找出：
- 未實現損益 offset
- 現價 offset
- 市值 offset
- 可賣股數 offset

使用方式（盤中，32-bit Python）：
  .venv_yuanta32_new\\Scripts\\python.exe brokers\\decode_yuanta_binary.py
"""
import pythonnet
pythonnet.load("netfx")
import clr, os, sys, time, struct
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "lib"))
load_dotenv(PROJECT_ROOT / ".env")

clr.AddReference("YuantaOneAPI")
from YuantaOneAPI import YuantaOneAPITrader, YuantaDataHelper, enumEnvironmentMode, enumLogType

account = os.getenv("YUANTA_ACCOUNT", "").strip()
password = os.getenv("YUANTA_PASSWORD", "").strip()

raw_bytes_holder = [None]

def on_response(*args):
    if len(args) < 5:
        return
    result_no = args[1]
    strIndex  = str(args[2]).strip()
    obj_value = args[4]

    if "20.103.0.22" not in strIndex and result_no not in (0,) and "20.103.0.22" not in str(obj_value):
        if "Byte[]" in str(type(obj_value)):
            pass  # might still be the response
        else:
            return

    if "Byte[]" in str(type(obj_value)):
        py_bytes = bytes(obj_value)
        raw_bytes_holder[0] = py_bytes
        print(f"\n[RESPONSE] Got {len(py_bytes)} bytes for strIndex='{strIndex}', ResultNo={result_no}")
        decode_all_fields(py_bytes)

def decode_all_fields(data: bytes):
    header = struct.unpack('>I', data[0:4])[0]
    print(f"Header (record count?): {header}")

    # 第一筆記錄從 byte 4 開始
    rec_start = 4
    rec = data[rec_start:]

    # 找帳號
    acct_raw = rec[0:22]
    try:
        acct_str = acct_raw.decode('ascii').rstrip('\x00')
        print(f"Account: '{acct_str}'")
    except:
        print(f"Account raw: {acct_raw.hex()}")

    # 股票代號 (offset 55, 12 bytes)
    try:
        stk_code = rec[55:67].decode('cp950').rstrip('\x00').strip()
        print(f"Stock code: '{stk_code}'")
    except:
        print(f"Stock code raw: {rec[55:67].hex()}")

    # 股票名稱 (offset 67, 30 bytes)
    try:
        stk_name = rec[67:97].decode('cp950').rstrip('\x00').strip()
        print(f"Stock name: '{stk_name}'")
    except:
        pass

    print(f"\n{'Offset':>8} | {'Int64 (BE)':>18} | {'/ 100':>12} | {'/ nos':>12} | Note")
    print("-" * 80)

    stk_nos = None
    for offset in range(89, 200, 4):
        if offset + 8 > len(rec):
            break
        chunk = rec[offset:offset+8]
        try:
            val = struct.unpack('>q', chunk)[0]
        except:
            continue

        note = ""
        if val == 0:
            continue

        # 股數特徵：正整數，合理範圍
        if 1 <= val <= 1_000_000 and stk_nos is None:
            note = "<-- 可能是股數?"
            if 100 <= val <= 100_000:
                stk_nos = val
                note = "<-- 股數 (推測)"

        div100 = val / 100.0
        div_nos = f"{val/stk_nos:.2f}" if stk_nos and stk_nos > 0 else "-"

        print(f"{offset:>8} | {val:>18} | {div100:>12.2f} | {div_nos:>12} | {note}")

    # 也儲存到檔案讓 64-bit 分析
    out_path = PROJECT_ROOT / "data" / "yuanta_binary_dump.hex"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(data.hex(), encoding='ascii')
    print(f"\nRaw hex saved to: {out_path}")

def main():
    api = YuantaOneAPITrader()
    api.SetLogType(enumLogType.COMMON)
    api.SetPopUpMsg(False)
    api.OnResponse += on_response

    print("Connecting PROD...")
    api.Open(enumEnvironmentMode.PROD)
    time.sleep(5)

    print(f"Login {account}...")
    api.Login(account, password)
    time.sleep(12)

    print("Sending RQ 20.103.0.22...")
    helper = YuantaDataHelper()
    helper.initial()
    helper.SetFunctionID(20, 103, 0, 22)
    helper.SetUInt(1)
    helper.SetTByte(account, 22)
    api.RQ(account, helper)

    print("Waiting 20s for response...")
    for i in range(20):
        time.sleep(1)
        print(".", end="", flush=True)
        if raw_bytes_holder[0] is not None:
            break
    print()

    if raw_bytes_holder[0] is None:
        print("No response received.")
    else:
        print("Done. Check data/yuanta_binary_dump.hex for full analysis.")

if __name__ == "__main__":
    main()
