# 🔍 頁面加載問題診斷指南

## 問題說明
某些頁面（實盤交易、策略管理）無法正常打開或顯示為空白。

## 快速診斷步驟

### 步驟 1: 打開開發者工具
```
按 F12 打開瀏覽器開發者工具
```

### 步驟 2: 進入 Console 標籤
```
點擊 "Console" 標籤
```

### 步驟 3: 點擊問題按鈕
點擊「💹 實盤交易」或「📁 策略管理」按鈕，然後查看 Console 中的輸出。

### 步驟 4: 查看日誌消息
應該看到類似的日誌消息：

**預期輸出（正常情況）:**
```
Loading page: trading
Calling loadTradingPage
Found pages: 5
Page element found: true (ID: trading-page)
Page activated: trading
Trading data loaded: {app: "running", ...}
```

**或:**
```
Loading page: strategies
Calling loadStrategiesPage
Found pages: 5
Page element found: true (ID: strategies-page)
Page activated: strategies
```

---

## 常見問題及解決方案

### 問題 1: 看到 "Page element not found" 錯誤

**錯誤信息:**
```
Error in loadPage: Page element not found: trading-page
```

**原因:** HTML 中的頁面 div 沒有找到

**解決方案:**
```bash
# 驗證 HTML 中是否有這些元素
curl http://localhost:5000/ | grep "id=\".*-page\""
```

應該看到：
```
id="dashboard-page"
id="trading-page"
id="strategies-page"
id="comparison-page"
id="analysis-page"
```

### 問題 2: 看到 "Error loading trading data" 或類似的 API 錯誤

**錯誤信息:**
```
Error loading trading data: TypeError: Cannot read property 'app' of undefined
```

**原因:** API 返回格式不正確，或 API 無法訪問

**解決方案:**
```bash
# 測試 API 端點
curl http://localhost:5000/api/status
curl http://localhost:5000/api/strategies
curl http://localhost:5000/api/chart-data
```

驗證響應格式是否為：
```json
{
  "status": "success",
  "data": { ... }
}
```

或者直接返回數據：
```json
{
  "app": "running",
  ...
}
```

### 問題 3: Console 中沒有任何日誌消息

**原因:** JavaScript 文件可能沒有加載或有語法錯誤

**解決方案:**

1. **檢查 Network 標籤**
   - 打開 Network 標籤
   - 重新加載頁面 (Ctrl+R 或 Cmd+R)
   - 查找 `dashboard.js`
   - 應該看到 HTTP 200 狀態碼

2. **強制清除緩存**
   ```
   Ctrl+Shift+Delete (Windows)
   Cmd+Shift+Delete (Mac)
   ```

3. **檢查 Sources 標籤**
   - 打開 Sources 標籤
   - 展開左側的 static/js 文件夾
   - 點擊 dashboard.js
   - 應該看到完整的 JavaScript 代碼

### 問題 4: 按鈕點擊後頁面閃爍但沒有加載內容

**原因:** 頁面 div 被顯示，但 loadXXXPage() 函數執行有誤

**解決方案:**

1. 查看完整的 Console 輸出
2. 查找任何紅色的錯誤消息
3. 檢查是否有 API 錯誤

---

## 手動測試指令

### 在 Console 中直接測試 loadPage 函數

**步驟:**
1. 打開 Console (F12 → Console)
2. 複製並粘貼以下命令：

```javascript
// 測試 loadPage 函數是否可用
console.log('loadPage function:', typeof loadPage);

// 測試頁面元素是否存在
console.log('Pages found:', document.querySelectorAll('.page').length);

// 列出所有頁面 ID
document.querySelectorAll('.page').forEach(p => {
    console.log('Page ID:', p.id, 'Display:', getComputedStyle(p).display);
});

// 手動調用 loadPage
loadPage('trading');
```

**預期輸出:**
```
loadPage function: function
Pages found: 5
Page ID: dashboard-page Display: none
Page ID: trading-page Display: block
Page ID: strategies-page Display: none
Page ID: comparison-page Display: none
Page ID: analysis-page Display: none
Loading page: trading
...
```

---

## API 測試

### 測試交易頁面所需的 API

在瀏覽器或終端中測試：

```bash
# 獲取系統狀態（交易頁面需要）
curl http://localhost:5000/api/status

# 應該返回類似：
{
  "app": "running",
  "data_layer": true,
  "brokers": {
    "ib": false,
    "yuanta": false,
    "schwab": false
  },
  "timestamp": "..."
}
```

### 測試策略管理頁面所需的 API

```bash
# 獲取策略列表（策略頁面需要）
curl http://localhost:5000/api/strategies

# 應該返回類似：
{
  "status": "success",
  "data": [
    {
      "策略名稱": "Wave Strategy",
      ...
    },
    ...
  ]
}
```

---

## CSS 驗證

### 檢查 .page 樣式是否正確

在 Console 中執行：

```javascript
// 檢查 CSS 樣式
const pageElement = document.getElementById('trading-page');
const styles = getComputedStyle(pageElement);

console.log('Display:', styles.display);
console.log('Visibility:', styles.visibility);
console.log('Opacity:', styles.opacity);
console.log('Position:', styles.position);
```

**預期值（當頁面是 active 時）:**
```
Display: block
Visibility: visible
Opacity: 1
Position: static (或 relative)
```

---

## JavaScript 驗證

### 檢查所有必需的函數是否已定義

在 Console 中執行：

```javascript
// 檢查所有必需的函數
const functions = [
    'loadPage',
    'loadDashboardPage',
    'loadTradingPage',
    'loadStrategiesPage',
    'loadComparisonPage',
    'loadAnalysisPage',
    'setupUploadForm',
    'setupBrokerButtons'
];

functions.forEach(func => {
    console.log(`${func}:`, typeof window[func] === 'function' ? '✅' : '❌');
});
```

**預期輸出:**
```
loadPage: ✅
loadDashboardPage: ✅
loadTradingPage: ✅
loadStrategiesPage: ✅
loadComparisonPage: ✅
loadAnalysisPage: ✅
setupUploadForm: ✅
setupBrokerButtons: ✅
```

---

## 完整診斷流程

### 1. 驗證應用狀態

```bash
curl http://localhost:5000/api/status
```

✅ 應看到 `"app": "running"`

### 2. 驗證 HTML 完整性

```bash
curl http://localhost:5000/ | grep -c "id=\".*-page\""
```

✅ 應返回 `5`

### 3. 驗證 JavaScript 加載

```bash
curl http://localhost:5000/static/js/dashboard.js | grep -c "function loadPage"
```

✅ 應返回 `1`

### 4. 驗證 CSS 加載

```bash
curl http://localhost:5000/static/css/dashboard.css | grep -c ".page.active"
```

✅ 應返回 `1`

### 5. 在瀏覽器中測試

- 按 F12 打開開發者工具
- 在 Console 中運行函數驗證指令
- 點擊頁面按鈕
- 查看日誌輸出

---

## 提交問題時的信息清單

如果以上步驟都無法解決問題，請收集以下信息：

- [ ] 瀏覽器類型和版本
  ```
  例如: Chrome 120.0
  ```

- [ ] Console 中的完整錯誤信息（截圖）

- [ ] 點擊按鈕時的完整日誌輸出

- [ ] `curl http://localhost:5000/api/status` 的完整輸出

- [ ] `curl http://localhost:5000/static/js/dashboard.js | head -100` 的前 100 行

- [ ] Flask 日誌文件內容（`flask_app.log`）

---

## 快速修復清單

如果遇到問題，依次嘗試以下步驟：

1. ☐ 強制刷新瀏覽器 (Ctrl+F5 或 Cmd+Shift+R)
2. ☐ 清除瀏覽器緩存 (Ctrl+Shift+Delete)
3. ☐ 重啟 Flask 應用
4. ☐ 打開無痕窗口測試
5. ☐ 檢查瀏覽器 Console 中的錯誤
6. ☐ 檢查 Network 標籤中的 HTTP 響應狀態
7. ☐ 驗證所有 API 端點是否正常工作
8. ☐ 驗證 HTML、CSS、JavaScript 文件是否正確加載

---

## 有用的 Console 命令

### 快速診斷腳本

複製以下完整腳本到 Console 中一次執行所有診斷：

```javascript
console.log('=== 完整診斷開始 ===');

// 1. 檢查函數
console.log('\n--- 函數檢查 ---');
['loadPage', 'loadTradingPage', 'loadStrategiesPage'].forEach(f => {
    console.log(f + ':', typeof window[f] === 'function' ? '✅' : '❌');
});

// 2. 檢查頁面元素
console.log('\n--- 頁面元素檢查 ---');
const pages = document.querySelectorAll('.page');
console.log('頁面總數:', pages.length);
pages.forEach(p => {
    const display = getComputedStyle(p).display;
    console.log(`${p.id}: ${display === 'block' ? '✅ 顯示' : '隱藏'}`);
});

// 3. 檢查按鈕
console.log('\n--- 按鈕檢查 ---');
const buttons = document.querySelectorAll('.nav-btn');
console.log('按鈕總數:', buttons.length);

// 4. 手動測試頁面切換
console.log('\n--- 手動測試頁面切換 ---');
console.log('正在加載交易頁面...');
loadPage('trading');

console.log('=== 診斷完成 ===');
```

---

## 後續步驟

1. **使用上述指令進行診斷**
2. **記錄輸出結果**
3. **根據輸出結果進行相應的修復**
4. **如仍有問題，提供診斷信息給開發者**

---

**祝診斷順利！** 🔍
