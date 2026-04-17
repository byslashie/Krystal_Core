#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試 Flask 應用"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).parent / 'broker_positions.db'

def get_db_positions():
    """從本地數據庫讀取持倉"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM broker_positions LIMIT 1')
        positions = [dict(row) for row in c.fetchall()]
        conn.close()
        return positions
    except Exception as e:
        print(f"DB ERROR: {e}")
        return []

@app.route('/')
def index():
    return "Hello World"

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/broker-positions')
def api_broker_positions():
    positions = get_db_positions()
    return jsonify({
        'status': 'success',
        'count': len(positions),
        'data': positions
    })

if __name__ == '__main__':
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} {rule.methods}")

    print("\nStarting Flask on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
