# 🛠️ 如何在瀏覽器中測試頁面加載

## ⚠️ **重要提示**

`loadPage('trading')` 不是 PowerShell 命令！

這是 **JavaScript 代碼**，應該在**瀏覽器的開發者工具 Console 中運行**，而不是在 PowerShell 中。

---

## 📖 **正確的診斷步驟**

### **第 1 步：確保 Flask 應用正在運行**

在 PowerShell 中，進入項目目錄並啟動 Flask：

```powershell
cd G:\我的雲端硬碟\Krystal_AI_Trading_System
python app_html_flask.py
```

✅ 你應該看到類似的輸出：
```
[*] Flask 應用啟動...
[*] 訪問: http://localhost:5000
[*] 數據層狀態: OK
 * Running on http://127.0.0.1:5000
```

### **第 2 步：在瀏覽器中打開應用**

1. 打開任何瀏覽器 (Chrome、Firefox、Safari 等)
2. 進入 URL：`http://localhost:5000`
3. 你應該看到 Krystal AI 儀表板頁面

### **第 3 步：打開瀏覽器開發者工具**

| 瀏覽器 | 快捷鍵 |
|--------|--------|
| Chrome / Edge | **F12** |
| Firefox | **F12** |
| Safari | **Cmd+Option+I** |

### **第 4 步：進入 Console 標籤**

- 點擊頂部的 **Console** 標籤
- 或者按 **Ctrl+Shift+J** (Windows) 或 **Cmd+Option+J** (Mac)

### **第 5 步：在 Console 中粘貼代碼**

在 Console 的輸入框中（通常在底部，有 `>` 符號），複製粘貼：

```javascript
loadPage('trading');
```

然後按 **Enter**

### **第 6 步：觀察結果**

#### ✅ **成功的情況：**

Console 中應該看到：
```
Loading page: trading
Calling loadTradingPage
Found pages: 5
Page element found: true (ID: trading-page)
Page activated: trading
Trading data loaded: {app: "running", ...}
```

頁面應該立即切換到「💹 實盤交易」頁面。

#### ❌ **出現錯誤：**

如果看到紅色錯誤信息，比如：
```
Error in loadPage: TypeError: Cannot read property 'app' of undefined
```

這意味著有具體的問題需要修復。請複製完整的錯誤信息並報告。

---

## 🧪 **完整的測試腳本**

為了快速測試所有頁面，在 Console 中複製粘貼以下代碼：

```javascript
// === 完整診斷腳本 ===
console.log('開始頁面測試...\n');

// 測試 1: 檢查函數
console.log('--- 步驟 1: 檢查函數 ---');
console.log('loadPage 函數:', typeof loadPage);

// 測試 2: 列出所有頁面
console.log('\n--- 步驟 2: 檢查頁面元素 ---');
const pages = Array.from(document.querySelectorAll('.page')).map(p => ({
    id: p.id,
    active: p.classList.contains('active')
}));
console.table(pages);

// 測試 3: 測試儀表板頁面
console.log('\n--- 步驟 3: 測試儀表板頁面 ---');
loadPage('dashboard');

// 測試 4: 延遲後測試交易頁面
setTimeout(() => {
    console.log('\n--- 步驟 4: 測試交易頁面 ---');
    loadPage('trading');
}, 1000);

// 測試 5: 延遲後測試策略頁面
setTimeout(() => {
    console.log('\n--- 步驟 5: 測試策略頁面 ---');
    loadPage('strategies');
}, 2000);

console.log('✅ 測試完成！觀察上方的頁面是否變化。');
```

複製上面的所有代碼，粘貼到 Console 中，按 Enter。

**預期行為：**
- 頁面應該依次切換到 3 個不同的頁面
- Console 中應該看到對應的日誌消息

---

## 🎯 **按鈕點擊測試**

### **方法 1: 直接在瀏覽器中點擊**

1. 在儀表板中，查看頂部的 5 個按鈕：
   - 📊 儀表板
   - 💹 實盤交易
   - 📁 策略管理
   - 📈 多策略對比
   - ⚙️ 進階分析

2. 點擊「💹 實盤交易」按鈕

3. 頁面應該立即切換

4. 打開 Console (F12) 查看是否有錯誤信息

### **方法 2: 通過 Console 點擊**

在 Console 中輸入：
```javascript
document.querySelector('[data-page="trading"]').click();
```

然後按 Enter。

---

## 📋 **故障排查清單**

| 問題 | 檢查項 | 修復方案 |
|------|--------|--------|
| Console 中沒有任何日誌 | JavaScript 文件是否加載？ | 檢查 Network 標籤，看 dashboard.js 是否加載 |
| 看到 "loadPage is not defined" | 函數是否定義？ | 刷新頁面 (Ctrl+F5)，確保 JavaScript 完全加載 |
| 看到 API 錯誤 | API 是否可訪問？ | 測試 curl http://localhost:5000/api/status |
| 頁面閃爍但沒有內容 | loadXXXPage 函數是否執行？ | 查看完整的 Console 輸出，尋找錯誤 |
| 按鈕無法點擊 | onclick 屬性是否存在？ | 檢查 HTML 源代碼，看按鈕是否有 onclick |

---

## 🔗 **有用的鏈接**

### **測試 API 端點**

在瀏覽器中訪問（或在 PowerShell 中用 curl）：

- 系統狀態: http://localhost:5000/api/status
- 績效指標: http://localhost:5000/api/metrics
- 策略列表: http://localhost:5000/api/strategies
- 圖表數據: http://localhost:5000/api/chart-data
- 持倉管理: http://localhost:5000/api/holdings

### **檢查日誌文件**

在 PowerShell 中：
```powershell
Get-Content flask_app.log -Tail 20
```

---

## 💡 **常見誤解**

### ❌ 錯誤：在 PowerShell 中運行 JavaScript

```powershell
PS> loadPage('trading')  # ❌ 錯誤！這是 PowerShell，不是 JavaScript
```

### ✅ 正確：在瀏覽器 Console 中運行

```javascript
// 在瀏覽器 Console (F12) 中：
loadPage('trading')  // ✅ 正確！
```

---

## 🎓 **瀏覽器 Console 快速教程**

### **什麼是 Console？**

Console 是瀏覽器內置的工具，讓你：
- 查看 JavaScript 錯誤信息
- 直接執行 JavaScript 代碼
- 調試應用程序

### **如何進入 Console？**

1. **在頁面上點擊滑鼠右鍵**
2. **選擇「檢查」(Inspect)** 或「檢查元素」
3. **點擊頂部的「Console」標籤**

或者直接按 **F12**

### **如何執行代碼？**

在 Console 底部的輸入框中：
1. 輸入或粘貼代碼
2. 按 **Enter** 執行

### **如何查看日誌？**

所有的 `console.log()` 輸出都會在 Console 中顯示。

---

## 🆘 **仍然無法工作？**

### **快速修復步驟：**

1. **強制刷新瀏覽器**
   ```
   Ctrl+F5 (Windows)
   Cmd+Shift+R (Mac)
   ```

2. **清除瀏覽器緩存**
   ```
   Ctrl+Shift+Delete
   然後點擊「清除數據」
   ```

3. **重新啟動 Flask**
   ```
   在 PowerShell 中按 Ctrl+C 停止
   然後再次運行：python app_html_flask.py
   ```

4. **使用無痕窗口**
   ```
   Ctrl+Shift+N (Chrome)
   Ctrl+Shift+P (Firefox)
   Cmd+Shift+N (Safari)
   ```

5. **檢查 Network 標籤**
   - 打開 F12
   - 點擊「Network」標籤
   - 刷新頁面
   - 查看所有資源是否加載成功（HTTP 200）

---

## 📞 **需要更多幫助？**

如果以上步驟都無法解決，請提供：

1. **完整的 Console 輸出**（複製所有文本）
2. **你期望看到的結果**
3. **實際看到的結果**
4. **使用的瀏覽器和版本**
5. **Flask 是否正在運行** (是否看到 "Running on http://127.0.0.1:5000")

---

**現在試試吧！🚀**

1. ✅ 確保 Flask 正在運行
2. ✅ 訪問 http://localhost:5000
3. ✅ 按 F12 打開 Console
4. ✅ 複製粘貼 `loadPage('trading');`
5. ✅ 按 Enter

應該會看到頁面切換到「💹 實盤交易」！

祝成功！🎉
