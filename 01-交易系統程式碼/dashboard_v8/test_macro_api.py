import requests
import json
import os

try:
    r = requests.get('http://localhost:9999/api/macro-indicators')
    r.raise_for_status()
    data = r.json()
    with open('macro_test.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Success: macro_test.json created")
except Exception as e:
    print(f"Error: {e}")
