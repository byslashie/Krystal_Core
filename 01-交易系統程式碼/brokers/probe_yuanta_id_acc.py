import pythonnet
pythonnet.load('netfx')
import clr
import os
import sys

LIB_DIR = os.path.join(os.getcwd(), 'lib')
sys.path.append(LIB_DIR)
clr.AddReference('YuantaOneAPI')

from YuantaOneAPI import TYuantaIDAccount

print("--- TYuantaIDAccount Members ---")
acc = TYuantaIDAccount()
for m in dir(acc):
    print(m)
