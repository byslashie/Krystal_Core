#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask server for dashboard_v7
Run: python app.py
URL: http://localhost:5000
"""

from flask import Flask, send_from_directory
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

app = Flask(__name__)


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


# The HTML loads this script as: src="dashboard_v7/index_compass_api.js"
# so we need to serve it at /dashboard_v7/index_compass_api.js
@app.route('/dashboard_v7/<path:filename>')
def dashboard_static(filename):
    return send_from_directory(BASE_DIR, filename)


if __name__ == '__main__':
    print("=" * 50)
    print("  Krystal Dashboard v7")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
