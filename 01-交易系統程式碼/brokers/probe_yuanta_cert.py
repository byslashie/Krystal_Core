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

print("--- Searching for Cert/Login methods ---")
for m in dir(api):
    if "Cert" in m or "Login" in m or "Load" in m or "Set" in m:
        print(m)
