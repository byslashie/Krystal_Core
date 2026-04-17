import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

import YuantaOneAPI

print("--- Inspecting YuantaOneAPI Members ---")
for item in dir(YuantaOneAPI):
    print(item)

print("\n--- Deep Inspection of YuantaOneAPITrader ---")
from YuantaOneAPI import YuantaOneAPITrader
api = YuantaOneAPITrader()
methods = api.GetType().GetMethods()
for m in methods:
    if any(k in m.Name.lower() for k in ["cert", "pfx", "load", "set"]):
        params = m.GetParameters()
        p_str = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params])
        print(f"{m.Name}({p_str})")
