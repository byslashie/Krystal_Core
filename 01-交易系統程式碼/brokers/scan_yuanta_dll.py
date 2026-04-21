import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

# Add DLL path
LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

import YuantaOneAPI

with open("yuanta_dll_methods_v2.txt", "w", encoding="utf-8") as f:
    f.write("--- Listing ALL types in YuantaOneAPI ---\n")
    asm = YuantaOneAPI.YuantaOneAPITrader().GetType().Assembly
    types = asm.GetTypes()
    for t in types:
        f.write(f"Type: {t.FullName}\n")
        # List methods for each type
        try:
            methods = t.GetMethods()
            for m in methods:
                if any(x in m.Name for x in ["Cert", "Load", "Set", "Initial", "Pfx"]):
                    f.write(f"  Method: {m.Name}\n")
        except:
            pass

