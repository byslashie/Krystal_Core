# 🤖 Telegram Bot 快速設定指南

## 步驟 1：建立 Bot

1. 在 Telegram 中搜尋 **@BotFather**
2. 點擊開始，發送：`/newbot`
3. 按照提示：
   - Bot 名稱：例如 `ShipMonitor_Bot` (顯示名稱)
   - Bot 用戶名：例如 `ShipMonitor_Bot_Krystal` (必須唯一，以 _bot 結尾)
   - BotFather 會返回 **Token**，複製存起來

✅ **你的 Token 格式**：`123456789:ABCDEFGHIJKLMNOPqrstuvwxyz`

## 步驟 2：建立私人群組或頻道

**選項 A：個人聊天（推薦）**
- 用你的 Telegram 帳號找到 Bot，點擊「開始」
- Bot 會傳來歡迎訊息
- 複製你的個人 ID（見下文方法）

**選項 B：私人群組**
- 建立私人群組，加入你的 Bot
- 右鍵點擊群組 → 複製連結，會看到 `-123456789` 的 ID

## 步驟 3：獲取你的 Chat ID

### 方法 1：簡易法（推薦）
貼上以下連結到瀏覽器：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```
然後訪問：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
- 向你的 Bot 發送任何訊息
- 重新載入上面的連結
- 在 JSON 中找 `"chat":{"id":XXXXX}` → **XXXXX 就是你的 Chat ID**

### 方法 2：用 Python 快速測試
```python
import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
print(requests.get(url).json())
```

## 步驟 4：保存環境變數

在你的 `.env` 檔案中添加：
```
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPqrstuvwxyz
TELEGRAM_CHAT_ID=-123456789
```

## 步驟 5：測試

執行：
```bash
python -c "
from telegram import Bot
import os

bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
chat_id = os.getenv('TELEGRAM_CHAT_ID')
bot.send_message(chat_id=chat_id, text='🚢 Ship Monitor 系統已連接！')
"
```

你應該會在 Telegram 上看到訊息。

## 🔗 有用的連結

- BotFather 官方：https://t.me/botfather
- Telegram API 文檔：https://core.telegram.org/bots/api
- Python-telegram-bot 文檔：https://python-telegram-bot.readthedocs.io/

---

✅ 完成後，你的 Bot 就可以開始傳送船舶監測告警了！
