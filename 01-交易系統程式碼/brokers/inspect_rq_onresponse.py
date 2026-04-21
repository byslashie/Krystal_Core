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

print("--- RQ Method Details ---")
# Get all methods named RQ
methods = [m for m in api.GetType().GetMethods() if m.Name == "RQ"]
for m in methods:
    print(f"Name: {m.Name}")
    print(f"ReturnType: {m.ReturnType}")
    params = m.GetParameters()
    for p in params:
        print(f"  Param: {p.Name}, Type: {p.ParameterType}")

print("\n--- OnResponse Details ---")
events = [e for e in api.GetType().GetEvents() if e.Name == "OnResponse"]
for e in events:
    print(f"Name: {e.Name}")
    print(f"EventHandlerType: {e.EventHandlerType}")
    # Inspect the delegate signature
    invoke = e.EventHandlerType.GetMethod("Invoke")
    params = invoke.GetParameters()
    for p in params:
        print(f"  Delegate Param: {p.Name}, Type: {p.ParameterType}")
