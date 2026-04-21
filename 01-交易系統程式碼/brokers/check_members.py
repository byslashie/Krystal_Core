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
print(f"Has OnExecution: {hasattr(api, 'OnExecution')}")
print(f"Has OnResponse: {hasattr(api, 'OnResponse')}")

print("\n--- All members ---")
for m in dir(api):
    print(m)
