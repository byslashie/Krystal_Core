import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import YuantaOneAPITrader

api = YuantaOneAPITrader()

print("--- RQ Method Signature ---")
# Attempt to inspect the RQ method
try:
    print(api.RQ.__doc__)
except:
    print("No doc for RQ")

# Print all public methods with their signatures if possible
import System
from System.Reflection import BindingFlags

methods = api.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance)
for method in methods:
    params = method.GetParameters()
    param_str = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params])
    print(f"{method.Name}({param_str})")

print("\n--- Checking for Account Classes ---")
import YuantaOneAPI
for name in dir(YuantaOneAPI):
    if "Account" in name or "Position" in name or "Inventory" in name:
        print(name)
