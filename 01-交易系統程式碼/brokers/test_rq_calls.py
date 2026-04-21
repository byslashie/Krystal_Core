import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import YuantaOneAPITrader, YuantaDataHelper

api = YuantaOneAPITrader()
helper = YuantaDataHelper()
helper.initial()
helper.SetFunctionID(ord('0'), ord('0'), ord('1'), ord('5'))

account = "D222061405"

print("--- Calling RQ with various methods ---")

try:
    print("1. Direct call api.RQ(account, helper):")
    res = api.RQ(account, helper)
    print(f"   Result: {res}")
except Exception as e:
    print(f"   Error: {e}")

try:
    print("\n2. Call with YuantaOneAPITrader.RQ(api, account, helper):")
    res = YuantaOneAPITrader.RQ(api, account, helper)
    print(f"   Result: {res}")
except Exception as e:
    print(f"   Error: {e}")

try:
    print("\n3. Call with api.RQ.Overloads[str, YuantaDataHelper](account, helper):")
    # Note: Need to import str or use System.String
    import System
    res = api.RQ.Overloads[System.String, YuantaDataHelper](account, helper)
    print(f"   Result: {res}")
except Exception as e:
    print(f"   Error: {e}")

try:
    print("\n4. Call via Reflection Invoke:")
    method = api.GetType().GetMethod("RQ", (System.String, YuantaDataHelper))
    res = method.Invoke(api, (account, helper))
    print(f"   Result: {res}")
except Exception as e:
    print(f"   Error: {e}")
