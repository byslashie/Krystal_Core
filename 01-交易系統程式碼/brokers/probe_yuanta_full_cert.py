import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

import YuantaOneAPI

print("--- Searching for ANY Certification related types/methods ---")
for type_name in dir(YuantaOneAPI):
    t = getattr(YuantaOneAPI, type_name)
    if hasattr(t, "GetMethods"):
        try:
            for m in t.GetMethods():
                if "Cert" in m.Name or "Pfx" in m.Name or "Load" in m.Name:
                    print(f"Type: {type_name}, Method: {m.Name}")
        except:
            pass

# Also check for enums or properties
for type_name in dir(YuantaOneAPI):
    if "Cert" in type_name or "Store" in type_name:
        print(f"Candidate Type: {type_name}")
