# brokers/yuanta_probe.py

import pythonnet
pythonnet.load("netfx")

import clr
import os
import sys




def main():
    dll_folder = os.path.join(os.getcwd(), "lib")
    dll_path = os.path.join(dll_folder, "YuantaOneAPI.dll")

    print("Python:", sys.version)
    print("CWD:", os.getcwd())
    print("DLL folder:", dll_folder)
    print("DLL path:", dll_path)
    print("DLL exists:", os.path.exists(dll_path))

    if dll_folder not in sys.path:
        sys.path.append(dll_folder)

    # 用「完整路徑」載入（比只寫組件名穩）
    ref = clr.AddReference(dll_path)
    print("Loaded assembly:", ref.FullName)

    import System
    asm = System.Reflection.Assembly.LoadFile(dll_path)
    types = asm.GetTypes()

    # 印出所有公開類別（你要找的就是 API 主類別 & enum）
    print("\n=== Public Types (Top 80) ===")
    shown = 0
    for t in types:
        if t.IsPublic:
            print(t.FullName)
            shown += 1
            if shown >= 80:
                break

    # 幫你抓「看起來像主 API」的候選
    keywords = ["Yuanta", "OneAPI", "API", "Client", "cls", "Environment", "Log", "enum"]
    print("\n=== Candidates ===")
    for t in types:
        name = t.FullName or ""
        if any(k.lower() in name.lower() for k in keywords):
            if t.IsPublic:
                print(name)

if __name__ == "__main__":
    main()
