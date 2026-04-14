import sys
import os
import datetime
import json
from pathlib import Path

# [CRITICAL Fix for Windows CP950]
# 強制將標準輸出設為 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def get_smart_output_dir():
    """
    智慧偵測存檔路徑：
    假設腳本位置在: skill_root/[skill_name]/scripts/save_work.py
    目標存檔位置: skill_root/docs/[skill_name]/
    """
    try:
        # 1. 取得腳本所在的絕對路徑
        current_script_path = Path(__file__).resolve()

        # 2. 往上找兩層 (scripts -> skill_name)
        skill_dir = current_script_path.parent.parent
        skill_name = skill_dir.name

        # 3. 往上找一層 (skill_name -> skill_root)
        skill_root = skill_dir.parent

        # 4. 組合目標路徑: skill_root/docs/[skill_name]
        target_dir = skill_root / "docs" / skill_name
        return target_dir

    except Exception:
        # 發生任何錯誤，回退到當前目錄下的 docs
        return Path(os.getcwd()) / "docs" / "unknown_skill"

def save_work(data, output_dir=None):
    # 1. 設定儲存路徑
    if output_dir:
        # 如果使用者有指定參數，優先使用
        base_dir = Path(output_dir)
    else:
        # 否則使用智慧偵測
        base_dir = get_smart_output_dir()
        
    # 建立目錄
    if not base_dir.exists():
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return f"❌ Error creating directory {base_dir}: {e}"

    # [Compatibility Fix] 同時支援 title 和 topic
    title = data.get("title") or data.get("topic") or "Untitled"
    
    # 確保內容是字串
    content = data.get("content", "")
    if not isinstance(content, str):
        content = str(content)
    
    # [CRITICAL FIX] 將字面的 \\n 轉換為真正的換行符
    # 當內容從命令列傳入時，\n 會被當作字面文字 "\\n"
    content = content.replace("\\n", "\n")
    
    # 2. 取得今日日期與時間
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")   # e.g., 2025-12-30
    time_str = now.strftime("%H%M%S")     # e.g., 165005
    
    # 3. 檔名安全化處理
    invalid_chars = '<>:"/\\|?*'
    safe_title = "".join([c if c not in invalid_chars else '-' for c in title])
    safe_title = safe_title.strip()

    # [Smart Deduplication] 智慧去重邏輯
    if safe_title.startswith(date_str):
        safe_title = safe_title[len(date_str):].lstrip("-_ ")

    # 4. 組合最終檔名：YYYY-MM-DD_HHMMSS_Title.md
    filename = f"{date_str}_{time_str}_{safe_title}.md"
    file_path = base_dir / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            # 在檔案開頭記錄完整生成時間
            full_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"# {title}\n> Generated: {full_timestamp}\n> Skill: {base_dir.name}\n\n{content}")
        return f"✅ Saved to: {file_path}"
    except Exception as e:
        return f"❌ Error saving: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
        # Check for optional output directory argument
        target_dir = None
        if len(sys.argv) > 2:
            target_dir = sys.argv[2]
            
        if os.path.exists(input_file):
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(save_work(data, target_dir))
            except Exception as e:
                print(f"Error processing JSON: {e}")
    else:
        print("Usage: python save_work.py <input.json> [output_directory]")