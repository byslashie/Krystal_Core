import re

path = r'h:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\dashboard_v8\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any occurrence of '/api/strategy/...' with `${API_BASE}/api/strategy/...`
new_content = re.sub(r"'(/api/strategy/[^']+)'", r'`${API_BASE}\1`', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Replaced strings in {path}")
