import sys
import os
import json

# 強制 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


def normalize_content(content: str) -> str:
    """
    [CRITICAL FIX] 正規化內容字串
    
    處理從命令列傳入時的特殊字符問題：
    1. 將字面的 \\n 轉換為真正的換行符
    2. 將字面的 \\t 轉換為真正的 Tab
    3. 處理反引號 code block 的轉義問題
    """
    # 將字面的 \\n 和 \\t 轉換為真正的換行/Tab
    content = content.replace("\\n", "\n")
    content = content.replace("\\t", "\t")
    
    # 處理 code block：有時 ``` 會變成 ` 或被轉義
    # 如果發現單獨的反引號接著語言標記，嘗試修復
    import re
    # 修復 `xs\n 這種模式為 ```xs\n
    content = re.sub(r'(?<!\`)`(xs|python|javascript|json|bash|sql|html|css|markdown)\n', r'```\1\n', content)
    # 修復結尾的單獨 ` 為 ```
    content = re.sub(r'\n`(?=\n|$)', r'\n```', content)
    
    return content


def write_note():
    """
    寫入筆記到 JSON 檔案
    
    Usage:
        模式 1 (直接內容): 
            python write_note.py <filename> <title> <content> [type]
        
        模式 2 (從檔案讀取 - 推薦用於複雜內容): 
            python write_note.py <filename> --from-file <content_file> <title> [type]
        
        模式 3 (從 stdin 讀取 - 推薦用於程式呼叫):
            echo "內容" | python write_note.py <filename> --stdin <title> [type]
            或在 PowerShell: 
            $content | python write_note.py <filename> --stdin <title> [type]
    
    Examples:
        write_note.py "output.json" "標題" "簡短內容" "implementation"
        write_note.py "output.json" --from-file "content.md" "標題" "implementation"
        Get-Content content.md | python write_note.py "output.json" --stdin "標題" "implementation"
    """
    
    # 檢查模式
    if len(sys.argv) >= 3 and sys.argv[2] == "--stdin":
        # 模式 3: 從 stdin 讀取內容
        if len(sys.argv) < 4:
            print("Usage: echo \"content\" | python write_note.py <filename> --stdin <title> [type]")
            sys.exit(1)
        
        filename = sys.argv[1]
        title = sys.argv[3]
        note_type = sys.argv[4] if len(sys.argv) > 4 else "plan"
        
        # 從 stdin 讀取內容
        try:
            # 設定 stdin 為 UTF-8
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(encoding='utf-8')
            content = sys.stdin.read()
            print(f"📥 從 stdin 讀取內容: {len(content)} 字元")
        except Exception as e:
            print(f"❌ 讀取 stdin 失敗: {str(e)}")
            sys.exit(1)
    
    elif len(sys.argv) >= 4 and sys.argv[2] == "--from-file":
        # 模式 2: 從檔案讀取內容
        if len(sys.argv) < 5:
            print("Usage: python write_note.py <filename> --from-file <content_file> <title> [type]")
            sys.exit(1)
        
        filename = sys.argv[1]
        content_file = sys.argv[3]
        title = sys.argv[4]
        note_type = sys.argv[5] if len(sys.argv) > 5 else "plan"
        
        # 讀取內容檔案
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"📄 從檔案讀取內容: {content_file} ({len(content)} 字元)")
        except FileNotFoundError:
            print(f"❌ 找不到內容檔案: {content_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 讀取檔案失敗: {str(e)}")
            sys.exit(1)
    
    else:
        # 模式 1: 直接從參數讀取內容
        if len(sys.argv) < 4:
            print("Usage: python write_note.py <filename> <title> <content> [type]")
            print("   或: python write_note.py <filename> --from-file <content_file> <title> [type]")
            print("   或: echo \"content\" | python write_note.py <filename> --stdin <title> [type]")
            sys.exit(1)
        
        filename = sys.argv[1]
        title = sys.argv[2]
        content = sys.argv[3]
        note_type = sys.argv[4] if len(sys.argv) > 4 else "plan"
        
        # [CRITICAL] 正規化從命令列傳入的內容
        content = normalize_content(content)
        
        # [WARNING] 檢查內容是否可能被截斷
        if len(content) < 100 and ('```' in title or '"' in title):
            print("⚠️ 警告：內容可能被 shell 截斷，建議使用 --from-file 或 --stdin 模式")

    # 組合資料
    data = {
        "type": note_type,
        "title": title,
        "content": content
    }

    # 寫入 JSON
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功寫入檔案: {filename}")
        print(f"   標題: {title}")
        print(f"   內容長度: {len(content)} 字元")
    except Exception as e:
        print(f"❌ 寫入失敗: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    write_note()