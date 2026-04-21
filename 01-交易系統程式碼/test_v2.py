#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal test app for /v2"""

from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

@app.route('/v2')
def dashboard_v2():
    return render_template('dashboardV2.html')

@app.route('/')
def index():
    return 'DashboardV2 Test App Running'

if __name__ == '__main__':
    print("Starting minimal test app on http://localhost:8888/v2")
    app.run(host='127.0.0.1', port=8888, debug=False)
