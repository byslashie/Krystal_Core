#!/usr/bin/env python
"""
簡化的 Flask 應用 - 僅用於測試 /ib 路由
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/ib-test')
def ib_test():
    """測試路由"""
    return '<h1>✅ Flask 運行正常</h1>'

@app.route('/ib')
def ib_dashboard():
    """IB 持倉儀表板"""
    print("\n[/ib] 路由被訪問")

    try:
        # 獲取當前目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, 'ib_positions.html')

        print(f"[DEBUG] 尋找檔案: {html_path}")
        print(f"[DEBUG] 檔案存在? {os.path.exists(html_path)}")

        if not os.path.exists(html_path):
            print(f"[ERROR] 檔案不存在!")
            return jsonify({'status': 'error', 'message': 'File not found'}), 404

        # 讀取檔案
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"[SUCCESS] 讀取成功! 大小: {len(content)} bytes")
            return content

    except Exception as e:
        print(f"[EXCEPTION] 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard_v7')
def dashboard_v7():
    """Dashboard V7 儀表板"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, 'dashboard_v7', 'index.html')

        if not os.path.exists(html_path):
            return jsonify({'status': 'error', 'message': 'dashboard_v7/index.html not found'}), 404

        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 簡化版 Flask 應用啟動")
    print("="*60)
    print("訪問: http://localhost:8888/ib")
    print("訪問: http://localhost:8888/ib-test")
    print("="*60 + "\n")

    app.run(debug=False, host='127.0.0.1', port=8888)
