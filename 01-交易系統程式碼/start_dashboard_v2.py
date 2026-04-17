#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Startup script for DashboardV2 - with auto-browser opening"""

import os
import sys
import webbrowser
import time
import threading
from datetime import datetime

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
try:
    from app_dashboard_v2 import app
    print("✓ Flask app loaded")
except ImportError as e:
    print(f"✗ Failed to import Flask app: {e}")
    print("\nMake sure app_dashboard_v2.py exists in the current directory")
    sys.exit(1)

def open_browser():
    """Open browser after a delay to allow Flask to start"""
    time.sleep(3)
    try:
        print("\n📱 Opening browser to http://localhost:8888/v2...")
        webbrowser.open('http://localhost:8888/v2')
    except Exception as e:
        print(f"   Note: Could not open browser: {e}")

# Start browser in background thread
browser_thread = threading.Thread(target=open_browser, daemon=True)
browser_thread.start()

# Start Flask
print("\n" + "=" * 70)
print("🚀 DashboardV2 Flask Server")
print("=" * 70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"URL:     http://localhost:8888/v2")
print(f"\nPress CTRL+C to stop")
print("=" * 70 + "\n")

try:
    app.run(
        host='127.0.0.1',
        port=8888,
        debug=False,
        use_reloader=False,
        threaded=True
    )
except KeyboardInterrupt:
    print("\n✓ Server stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n✗ Fatal error: {e}")
    sys.exit(1)
