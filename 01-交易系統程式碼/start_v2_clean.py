#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clean startup script for DashboardV2 - starts Flask app properly"""

import os
import sys
import subprocess
import time
import signal

print("=" * 70)
print("🚀 DashboardV2 Clean Startup")
print("=" * 70)

# Kill any existing Python processes on port 8888
print("\n[1] Cleaning up existing processes...")
try:
    # Use Windows taskkill to force kill all python.exe processes
    # This is a bit blunt but ensures clean restart
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                   stderr=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL,
                   shell=True)
    print("   ✓ Killed existing Python processes")
except Exception as e:
    print(f"   Warning: Could not kill processes: {e}")

time.sleep(2)

# Change to the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app
print("\n[2] Loading Flask application...")
try:
    from app_html_flask import app
    print("   ✓ Flask app loaded successfully")
except Exception as e:
    print(f"   ✗ Error loading Flask app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify templates exist
print("\n[3] Verifying templates...")
template_files = [
    'templates/dashboardV2.html',
    'templates/pages/risk.html',
    'templates/pages/performance.html',
    'templates/pages/monitoring.html',
    'templates/pages/trading.html',
    'templates/pages/strategies.html',
    'templates/pages/intel.html'
]

for template in template_files:
    if os.path.exists(template):
        size = os.path.getsize(template)
        print(f"   ✓ {template} ({size} bytes)")
    else:
        print(f"   ✗ Missing: {template}")

# Start Flask server
print("\n[4] Starting Flask server on http://localhost:8888/v2...")
print("   Press CTRL+C to stop")
print("=" * 70)
print()

try:
    app.run(
        host='127.0.0.1',
        port=8888,
        debug=False,
        use_reloader=False,
        threaded=True
    )
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n✗ Error starting Flask: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
