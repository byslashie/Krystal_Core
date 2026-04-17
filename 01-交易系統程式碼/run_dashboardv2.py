#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DashboardV2 Startup Script"""

import os
import sys
import webbrowser
import time
from app_html_flask import app

if __name__ == '__main__':
    print("=" * 60)
    print("Starting DashboardV2 Server")
    print("=" * 60)
    print()
    print("URL: http://localhost:8888/v2")
    print()
    print("Press CTRL+C to stop")
    print("=" * 60)
    print()

    # Auto-open browser after delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:8888/v2')
        except:
            pass

    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start Flask
    try:
        app.run(
            host='127.0.0.1',
            port=8888,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print()
        print("Server stopped")
