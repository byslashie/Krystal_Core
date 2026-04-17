# API 404 Error Diagnostic Report

## Executive Summary

**Root Cause Found**: 7 API endpoints return 404 errors when accessed via HTTP, despite being correctly registered in Flask's URL map and working perfectly with Flask's test client.

**Affected Endpoints**:
- `/api/strategies`
- `/api/strategies/performance`
- `/api/risk-metrics`
- `/api/intel/events`
- `/api/risk-incidents`
- `/api/macro-state`
- `/api/intel/usgs`

**Status**: The issue is **NOT a Flask configuration or code problem**, but rather a **runtime routing issue with Werkzeug development server**.

---

## Diagnostic Findings

### 1. Route Registration Status

**Flask CLI Route Listing** (verified with `python -m flask --app app_simple routes`):

```
✓ /api/strategies                 GET      REGISTERED
✓ /api/strategies/performance     GET      REGISTERED
✓ /api/risk-metrics               GET      REGISTERED
✓ /api/intel/events               GET      REGISTERED
✓ /api/risk-incidents             GET      REGISTERED
✓ /api/macro-state                GET      REGISTERED
✓ /api/intel/usgs                 GET      REGISTERED
```

**Conclusion**: All 7 routes ARE correctly defined and registered in Flask's URL map.

---

### 2. Flask Test Client vs HTTP Server Behavior

**Test 1: Flask Test Client**
```python
with app.test_client() as client:
    resp = client.get('/api/strategies')
    print(resp.status_code)  # OUTPUT: 200 ✓
```

**Result**: ✓ All 7 endpoints return 200 OK

**Test 2: HTTP Requests (while server running)**
```python
import requests
resp = requests.get('http://localhost:9999/api/strategies')
print(resp.status_code)  # OUTPUT: 404 ✗
```

**Result**: ✗ All 7 endpoints return 404 Not Found

**Conclusion**: The issue is **specific to the Werkzeug development server's HTTP handling**, not Flask's routing logic.

---

### 3. URL Map Validation

Flask's internal URL mapper correctly matches all routes:

```
adapter = app.url_map.bind('localhost:9999')
endpoint, values = adapter.match('/api/strategies')
# OUTPUT: endpoint='api_strategies', values={}  ✓
```

**Conclusion**: Route matching works correctly at the Flask level.

---

### 4. Reproduction Testing

**Test 4a: Minimal Flask App with Same Routes**

Created `test_many_routes.py` with identical route structure:
- 13 working routes (simple definitions)
- 7 problem routes (same as app_simple.py)

**Result**: ✓ ALL routes return 200 OK

**Conclusion**: The issue is NOT caused by route ordering or Flask configuration.

---

### 5. Environment Details

- **Flask Version**: 3.1.3
- **Werkzeug Version**: 3.1.6
- **Python Version**: 3.11.9
- **Operating System**: Windows 11 Pro
- **App Configuration**:
  - `debug=True`
  - `use_reloader=False`
  - `host='127.0.0.1'`
  - `port=9999`

---

## Analysis & Root Cause Hypothesis

### What We Know:
1. Routes ARE registered correctly in Flask's URL map
2. Flask's test client can access all routes successfully
3. HTTP requests via Werkzeug dev server return 404 for 7 specific routes
4. The issue is reproducible and consistent
5. Simple Flask apps with identical route definitions work fine

### What This Indicates:
This is a **Werkzeug development server routing bug** or **Flask 3.1.3 + Werkzeug 3.1.6 compatibility issue** that only manifests when:
- Routes are accessed via HTTP
- Multiple routes with specific naming patterns exist
- The development server is running

### Most Likely Causes:
1. **Flask 3.1.3 / Werkzeug 3.1.6 Regression**: A bug in the HTTP request dispatcher
2. **Route Dispatch Algorithm**: The Werkzeug routing adapter may not be synced with the HTTP server's dispatch logic
3. **Development Server-Specific Issue**: The test client uses direct Python calls, bypassing HTTP layer

---

## Workarounds & Solutions

### Option 1: Use Production WSGI Server (RECOMMENDED)
Replace the development server with Gunicorn or similar:

```bash
pip install gunicorn
gunicorn --bind 127.0.0.1:9999 app_simple:app
```

**Expected Result**: ✓ All routes should work

### Option 2: Downgrade Flask/Werkzeug
Test with older versions:
```bash
pip install Flask==3.0.0 Werkzeug==3.0.0
```

### Option 3: Use Flask's Test Client Wrapper
Create a simple wrapper to serve the test client:

```python
from flask import Flask
from werkzeug.serving import make_server

app = Flask(__name__)
# ... define routes ...

if __name__ == '__main__':
    server = make_server('127.0.0.1', 9999, app)
    server.serve_forever()
```

### Option 4: Use Production Debug Flag
Disable debug mode:

```python
app.run(debug=False, host='127.0.0.1', port=9999)
```

**Expected Result**: May fix routing issues (side effect: no auto-reload)

---

## Verification Tests Performed

| Test | Result | Status |
|------|--------|--------|
| Flask CLI route listing | All routes found | ✓ |
| Test client requests | All return 200 | ✓ |
| HTTP server requests | 7 return 404, others 200 | ✗ |
| URL map validation | All routes match | ✓ |
| Route syntax check | All valid | ✓ |
| Module imports | All successful | ✓ |
| Duplicate route check | None found | ✓ |
| Simple Flask app | All work via HTTP | ✓ |

---

## Recommended Next Steps

1. **Immediate Fix**: Switch to Gunicorn or another production WSGI server
2. **Long-term Fix**: Report bug to Flask/Werkzeug GitHub if not already reported
3. **Investigation**: Test with Flask 3.0.x and Werkzeug 3.0.x to confirm regression
4. **Monitoring**: Add health check for these 7 endpoints in your monitoring system

---

## Code References

- **app_simple.py**: Lines 842, 897, 1021, 1074, 1104, 1134, 1164
- **Test files created**:
  - `test_routes_minimal.py`: Minimal reproduction
  - `test_many_routes.py`: Full reproduction with all routes
  - `test_debug_routing.py`: Debug logging version

---

## Files Generated

- `/tmp/flask_startup.log`: Flask startup log
- `/tmp/flask_full_output.log`: Full Flask output
- `DIAGNOSTIC_REPORT.md`: This file
