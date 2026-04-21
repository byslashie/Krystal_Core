import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import YuantaOneAPITrader, YuantaDataHelper

helper = YuantaDataHelper()
print("--- YuantaDataHelper Members ---")
for m in dir(helper):
    print(m)

# Try to see if there are predefined command constants in enum environment or something
import YuantaOneAPI
print("\n--- All in YuantaOneAPI ---")
for m in dir(YuantaOneAPI):
    print(m)
