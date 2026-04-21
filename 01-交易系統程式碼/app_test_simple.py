"""簡化版 Flask 應用 - 用於診斷"""
from flask import Flask, jsonify

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    """簡單測試路由"""
    print("Index route called!", flush=True)
    return jsonify({'status': 'ok', 'message': 'Hello from Flask!'})

@app.route('/api/test')
def test_api():
    """API 測試"""
    return jsonify({'test': 'success'})

if __name__ == '__main__':
    print("[*] 簡化 Flask 應用啟動在 http://localhost:5501")
    app.run(debug=False, port=5501)
