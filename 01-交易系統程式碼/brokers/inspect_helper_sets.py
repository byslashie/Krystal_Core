import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import YuantaDataHelper

helper = YuantaDataHelper()

print("--- SetFunctionID Details ---")
methods = [m for m in helper.GetType().GetMethods() if m.Name == "SetFunctionID"]
for m in methods:
    params = m.GetParameters()
    param_info = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params])
    print(f"{m.Name}({param_info})")

print("\n--- All Set methods in YuantaDataHelper ---")
methods = [m for m in helper.GetType().GetMethods() if m.Name.startswith("Set")]
for m in methods:
    params = m.GetParameters()
    param_info = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params])
    print(f"{m.Name}({param_info})")
