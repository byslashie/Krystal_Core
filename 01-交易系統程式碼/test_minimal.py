#!/usr/bin/env python
"""最簡單的 Flask 應用"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World'

@app.route('/ib-test')
def test():
    return 'Test OK'

if __name__ == '__main__':
    print("啟動最小化 Flask...")
    app.run(debug=False, host='127.0.0.1', port=9999)
