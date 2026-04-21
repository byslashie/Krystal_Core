"""最小化 Flask 應用 - 診斷用"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Hello from Minimal Flask App</h1>'

if __name__ == '__main__':
    print("[*] 最小化 Flask 應用啟動在 http://localhost:8080")
    app.run(host='127.0.0.1', port=8080, debug=False)
