#!/usr/bin/env python3
"""
日記 → Threads 草稿自動生成工具
將日記中的核心洞察萃取，生成 3 種風格的 Threads 文稿

使用方式：
  python journal_to_threads.py              # 處理最新日記
  python journal_to_threads.py --date 2026-04-14  # 指定日期
  python journal_to_threads.py --batch weekly    # 批量處理本週
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import re

# 加入 anthropic SDK
try:
    from anthropic import Anthropic
except ImportError:
    print("錯誤：未安裝 anthropic SDK")
    print("請執行：pip install anthropic")
    sys.exit(1)


class JournalToThreads:
    def __init__(self):
        """初始化，載入環境變數和路徑"""
        self.client = Anthropic()

        # 讀取 API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("錯誤：未設定 ANTHROPIC_API_KEY 環境變數")
            sys.exit(1)

        # 設定路徑
        self.project_root = Path(__file__).parent.parent.parent
        self.journal_dir = self.project_root / "04-個人特質與規劃" / "日記"
        self.output_dir = self.project_root / "11-自媒體專區" / "Threads" / "drafts"

        # 確認目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"✓ 日記目錄：{self.journal_dir}")
        print(f"✓ 輸出目錄：{self.output_dir}")

    def find_latest_journal(self):
        """找出最新的日記檔案"""
        if not self.journal_dir.exists():
            print(f"錯誤：日記目錄不存在 {self.journal_dir}")
            return None

        journals = sorted(self.journal_dir.glob("journal_*.md"), reverse=True)
        if not journals:
            print("錯誤：找不到日記檔案")
            return None

        return journals[0]

    def find_journal_by_date(self, date_str):
        """根據日期找日記"""
        journal_path = self.journal_dir / f"journal_{date_str}.md"
        if not journal_path.exists():
            print(f"錯誤：找不到日記 {journal_path}")
            return None
        return journal_path

    def find_journals_for_week(self):
        """找出本週（過去 7 天）的所有日記"""
        today = datetime.now().date()
        week_start = today - timedelta(days=7)

        journals = []
        for i in range(8):
            date = week_start + timedelta(days=i)
            journal_path = self.journal_dir / f"journal_{date.strftime('%Y-%m-%d')}.md"
            if journal_path.exists():
                journals.append(journal_path)

        return journals

    def read_journal(self, path):
        """讀取日記內容"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"錯誤：無法讀取 {path}：{e}")
            return None

    def extract_insights(self, journal_content):
        """
        使用 Claude 從日記中萃取洞察並生成 Threads 草稿
        返回 3 種風格的草稿
        """

        prompt = """你是一位自媒體內容編輯，專門把深度思考轉化成引人入勝的 Threads 文稿。

我現在給你一篇日記，請你：
1. 找出其中最核心的 1-2 個洞察
2. 確保這些洞察**不洩露隱私細節**（例如人名、具體事件），但**保留普世的人性觀察**
3. 生成 3 種不同風格的 Threads 草稿

## Threads 文稿要求：
- 字數：150-250 字之間
- 風格：口語化、有停頓感（用短句、分行）、引發思考
- 結尾：邀請互動（用問句）
- 誠實但不傷人、有共鳴但不教訓人

## 三種風格：

### 風格 1 - 故事型（「我發現...」開頭）
講一個個人覺察，強調「我也經歷過這個」的親切感

### 風格 2 - 價值型（「給...的你」開頭）
提供一個可操作或可思考的觀點，幫助讀者看到新角度

### 風格 3 - 提問型（以問句開頭）
拋出一個深層的問題，邀請讀者反思和互動

---

## 日記內容：

{journal_content}

---

## 輸出格式（使用 JSON）：

{{
  "date": "YYYY-MM-DD",
  "core_insight": "從日記中萃取的核心洞察（1-2 句）",
  "threads": [
    {{
      "style": "story",
      "title": "故事型",
      "content": "實際的 Threads 文稿"
    }},
    {{
      "style": "value",
      "title": "價值型",
      "content": "實際的 Threads 文稿"
    }},
    {{
      "style": "question",
      "title": "提問型",
      "content": "實際的 Threads 文稿"
    }}
  ],
  "hashtags": ["#標籤1", "#標籤2", "#標籤3"]
}}

開始生成！
"""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.format(journal_content=journal_content)
                    }
                ]
            )

            # 提取 JSON 內容
            content = response.content[0].text

            # 嘗試從回應中找出 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                return result
            else:
                print("警告：無法從回應中提取 JSON 格式")
                return None

        except Exception as e:
            print(f"錯誤：Claude API 呼叫失敗：{e}")
            return None

    def save_drafts(self, date_str, insights):
        """
        將生成的草稿保存到檔案
        返回保存的檔案路徑
        """
        if not insights:
            return None

        filename = f"{date_str}_threads_drafts.md"
        filepath = self.output_dir / filename

        # 組織內容
        content = f"""# Threads 草稿 - {date_str}

**核心洞察：** {insights.get('core_insight', 'N/A')}

---

"""

        for idx, thread in enumerate(insights.get('threads', []), 1):
            content += f"""## {idx}. {thread.get('title', '未命名')}

**風格：** {thread.get('style', 'N/A')}

{thread.get('content', '')}

---

"""

        # 加上標籤
        hashtags = insights.get('hashtags', [])
        if hashtags:
            content += f"**推薦標籤：** {' '.join(hashtags)}\n\n"

        content += f"""---

**生成時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**來源日記：** journal_{date_str}.md
**狀態：** ✏️ 草稿（請審核後再發佈）

## 發佈前檢查清單
- [ ] 內容符合我的聲音
- [ ] 沒有洩露隱私細節
- [ ] 邀請了互動
- [ ] 檢查錯字

選好一篇後，複製到 Threads 發佈，然後將這份檔案備份到 `published/` 資料夾。
"""

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ 草稿已保存：{filepath}")
            return filepath
        except Exception as e:
            print(f"錯誤：無法保存檔案：{e}")
            return None

    def process_single(self, date_str=None):
        """處理單篇日記"""
        # 決定使用哪個日記檔案
        if date_str:
            journal_path = self.find_journal_by_date(date_str)
        else:
            journal_path = self.find_latest_journal()

        if not journal_path:
            print("無法找到日記檔案")
            return False

        print(f"\n📖 處理日記：{journal_path.name}")

        # 讀取日記
        content = self.read_journal(journal_path)
        if not content:
            return False

        # 萃取洞察
        print("🤖 正在讓 Claude 分析日記中的洞察...")
        insights = self.extract_insights(content)

        if not insights:
            print("❌ 無法萃取洞察")
            return False

        # 保存草稿
        date_match = re.search(r'journal_(\d{4}-\d{2}-\d{2})', journal_path.name)
        date_str = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')

        filepath = self.save_drafts(date_str, insights)

        if filepath:
            print(f"\n✅ 成功生成 3 篇 Threads 草稿！")
            print(f"📁 保存位置：{filepath}")
            print("\n接下來請：")
            print("1. 打開上面的檔案，檢視 3 篇草稿")
            print("2. 選擇你最喜歡的一篇")
            print("3. 複製到 Threads 發佈")
            print("4. 將檔案移到 published/ 資料夾存檔")
            return True
        else:
            print("❌ 無法保存草稿")
            return False

    def process_batch_weekly(self):
        """批量處理本週日記"""
        journals = self.find_journals_for_week()
        if not journals:
            print("本週沒有日記")
            return False

        print(f"\n📚 找到 {len(journals)} 篇本週日記")

        success_count = 0
        for journal_path in journals:
            date_match = re.search(r'journal_(\d{4}-\d{2}-\d{2})', journal_path.name)
            date_str = date_match.group(1) if date_match else ""

            content = self.read_journal(journal_path)
            if not content:
                continue

            print(f"\n🔄 處理 {journal_path.name}...")
            insights = self.extract_insights(content)

            if insights:
                self.save_drafts(date_str, insights)
                success_count += 1

        print(f"\n✅ 批量處理完成：{success_count}/{len(journals)} 篇成功")
        return True


def main():
    parser = argparse.ArgumentParser(description="日記 → Threads 草稿自動生成工具")
    parser.add_argument("--date", help="指定日期 (YYYY-MM-DD)", default=None)
    parser.add_argument("--batch", help="批量處理 (weekly)", default=None)

    args = parser.parse_args()

    processor = JournalToThreads()

    if args.batch == "weekly":
        processor.process_batch_weekly()
    else:
        processor.process_single(args.date)


if __name__ == "__main__":
    main()
