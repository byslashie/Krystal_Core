#!/usr/bin/env python
"""
手動測試元大同步腳本
"""
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
venv_32bit = PROJECT_ROOT / ".venv_yuanta32_new" / "Scripts" / "python.exe"
sync_script = PROJECT_ROOT / "brokers" / "sync_yuanta_positions.py"

print("=" * 60)
print("[測試] 元大同步腳本")
print("=" * 60)

# 檢查環境
print(f"\n[檢查] 32-bit Python: {venv_32bit}")
if not venv_32bit.exists():
    print(f"[ERROR] 找不到 32-bit Python")
    sys.exit(1)
print(f"[OK] 32-bit Python 存在")

print(f"\n[檢查] 同步腳本: {sync_script}")
if not sync_script.exists():
    print(f"[ERROR] 找不到同步腳本")
    sys.exit(1)
print(f"[OK] 同步腳本存在")

# 執行同步
print(f"\n[執行] 運行同步腳本...")
print("=" * 60)

try:
    result = subprocess.run(
        [str(venv_32bit), str(sync_script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120
    )

    print(result.stdout)
    if result.stderr:
        print("[STDERR]")
        print(result.stderr)

    print("=" * 60)
    if result.returncode == 0:
        print(f"[OK] 同步成功 (Return Code: 0)")
    else:
        print(f"[ERROR] 同步失敗 (Return Code: {result.returncode})")

except subprocess.TimeoutExpired:
    print("[ERROR] 同步超時 (超過 120 秒)")
except Exception as e:
    print(f"[ERROR] 異常: {e}")
