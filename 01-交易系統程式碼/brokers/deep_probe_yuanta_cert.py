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

print("--- Searching for ANY member with 'Cert' or 'pfx' via Reflection ---")
import System
from System.Reflection import BindingFlags

# Search in the class
methods = api.GetType().GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
for m in methods:
    if "Cert" in m.Name or "pfx" in m.Name:
        print(f"Method: {m.Name}")

props = api.GetType().GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
for p in props:
    if "Cert" in p.Name or "pfx" in p.Name:
        print(f"Property: {p.Name}")

fields = api.GetType().GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)
for f in fields:
    if "Cert" in f.Name or "pfx" in f.Name:
        print(f"Field: {f.Name}")

# Search in the whole assembly
asm = api.GetType().Assembly
for t in asm.GetTypes():
    if "Cert" in t.Name or "pfx" in t.Name:
        print(f"Type: {t.FullName}")
