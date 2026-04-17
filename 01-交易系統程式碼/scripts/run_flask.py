#!/usr/bin/env python
"""
Krystal AI 交易系統 - Flask 啟動腳本
自動選擇可用端口，清理舊進程
"""
import socket
import subprocess
import sys
import os
import time

def is_port_available(port):
    """檢查端口是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    except:
        return False

def find_available_port(start_port=5501, end_port=5510):
    """找到第一個可用的端口"""
    for port in range(start_port, end_port + 1):
        if is_port_available(port):
            return port
    return None

def main():
    # 尋找可用端口
    port = find_available_port()

    if port is None:
        print("❌ 錯誤：找不到可用的端口（5501-5510）")
        sys.exit(1)

    print("=" * 50)
    print("  Krystal AI 交易系統 - Flask 應用")
    print("=" * 50)
    print(f"✅ 使用端口: {port}")
    print(f"📱 訪問地址: http://localhost:{port}")
    print("=" * 50)
    print()

    # 修改 app 中的端口設置並運行
    from app_html_flask import app

    try:
        app.run(debug=False, port=port, host='127.0.0.1')
    except KeyboardInterrupt:
        print("\n\n👋 應用已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
