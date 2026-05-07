#!/usr/bin/env python3
"""啟動腳本 - 確保 UTF-8 編碼 + 清理舊進程"""
import sys, os, io, subprocess

# 強制 UTF-8（解決 Windows cp950 問題）
os.environ['PYTHONUTF8'] = '1'
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
except Exception:
    pass

PORT = 9999

# 清理佔用 port 的舊進程
def kill_port(port):
    try:
        result = subprocess.run(
            ['netstat', '-ano'], capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        pids = set()
        for line in result.stdout.splitlines():
            if f':{port}' in line and 'LISTEN' in line:
                parts = line.split()
                if parts:
                    pids.add(parts[-1])
        my_pid = str(os.getpid())
        for pid in pids:
            if pid != my_pid and pid != '0':
                subprocess.run(['taskkill', '/F', '/PID', pid],
                             capture_output=True, encoding='utf-8', errors='replace')
                print(f'[*] Killed old process PID {pid} on port {port}')
    except Exception as e:
        print(f'[!] Port cleanup failed: {e}')

kill_port(PORT)

import time
time.sleep(1)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import app

print(f'\n[*] Starting server on http://localhost:{PORT}\n')
app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)
