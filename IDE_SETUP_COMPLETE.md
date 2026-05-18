---
title: Claude Code IDE Skill 註冊完成
date: 2026-05-17
status: completed
---

# ✅ Claude Code IDE Skill 正式註冊完成

## 🎯 已完成的配置

### 1. VSCode 編輯器設置 ✓
```
位置：.vscode/settings.json
內容：
  - Claude Skills 啟用
  - 自動載入 Skill 清單
  - 編輯器格式化規則
  - Python/Markdown 專用設置
```

### 2. Skills Manifest 定義 ✓
```
位置：skills/manifest.json
內容：
  - 4 個 Skill 的完整定義
  - 每個 Skill 的命令、描述、用途、範例
  - Skill 分組（決策、生產力、內容、參考）
  - 自動激活設置
```

### 3. Claude 專案配置 ✓
```
位置：claude.json
內容：
  - 專案元數據
  - Workspace 配置
  - Skill 路徑和註冊表
  - 命令覆蓋設置
  - 擴展配置
```

### 4. Claude 內部記錄 ✓
```
位置：.claude/skills.json
位置：.claude/SKILLS_SETUP.md
內容：
  - Skill 註冊記錄
  - 設置維護指南
```

### 5. Skills 文件整理 ✓
```
skills/
├─ README.md                                 (索引)
├─ manifest.json                            (Manifest)
├─ krystal_strategy_reflection_partner.md   (Skill #1)
├─ four_identities_daily_schedule.md        (Skill #2)
├─ self_media_content_strategy.md           (Skill #3)
└─ quick_reference_v2_may2026.md            (Skill #4)
```

---

## 🚀 現在需要做什麼

### 步驟 1：重啟 IDE

```bash
# 方式 1：關閉並重新開啟 VSCode / Claude Code IDE
# 方式 2：在 IDE 中執行 Command Palette (⌘Shift P)
#         搜索 "Developer: Reload Window"
```

### 步驟 2：驗證 Skill 已載入

重啟後，在 IDE 中嘗試：
```
/strategy-r[Tab]  → 應該顯示自動完成
/daily-c[Tab]     → 應該顯示自動完成
/self-m[Tab]      → 應該顯示自動完成
/quick-r[Tab]     → 應該顯示自動完成
```

### 步驟 3：測試 Skill

```
輸入：/strategy-reflection
應該出現：8 鏡頭決策框架的完整說明

輸入：/daily-check
應該出現：當前時段應做的事

輸入：/self-media-strategy
應該出現：自媒體內容戰略分析

輸入：/quick-ref
應該出現：快速參考卡內容
```

---

## 📋 配置文件清單

| 文件 | 位置 | 用途 | 修改頻率 |
| --- | --- | --- | --- |
| `claude.json` | 根目錄 | Claude Code 專案配置 | 每月 |
| `.vscode/settings.json` | `.vscode/` | VSCode 編輯器設置 | 很少 |
| `skills/manifest.json` | `skills/` | Skills 清單和元數據 | 每月 |
| `.claude/skills.json` | `.claude/` | Skill 註冊記錄 | 每月 |
| `skills/README.md` | `skills/` | Skills 索引 | 每月 |
| `.claude/SKILLS_SETUP.md` | `.claude/` | 設置指南 | 參考用 |

---

## 🔄 未來維護

### 新增 Skill 流程

1. 在 `skills/` 中建立新 `.md` 檔
2. 編輯 `skills/manifest.json` 添加新 Skill 定義
3. 編輯 `.claude/skills.json` 添加記錄
4. 更新 `skills/README.md` 索引
5. Git commit 並同步內存

### 更新現有 Skill

1. 編輯對應的 `skills/*.md` 檔案
2. 更新 `skills/manifest.json` 中的版本號
3. Git commit
4. IDE 無需重啟（Skill 檔案會自動重新載入）

---

## ⚡ 快速命令

```bash
# 檢查配置是否完整
grep -r "skills" claude.json .vscode/settings.json skills/manifest.json

# 驗證 Manifest 格式
jq . skills/manifest.json | head -20

# 查看所有已註冊的 Skills
jq '.skills[].id' skills/manifest.json
```

---

## 🆘 如果出現問題

### 問題：重啟後仍看不到 `/` 命令
**解決**：
1. 確認 `claude.json` 在專案根目錄
2. 確認 `skills/manifest.json` 存在且格式正確
3. 檢查 `.vscode/settings.json` 中的 `claude.skills` 設置
4. 嘗試 `Developer: Reload Window`

### 問題：自動完成不顯示
**解決**：
1. 檢查 IDE 的 Skill 擴展是否啟用
2. 檢查 `manifest.json` 中的 `enabled: true`
3. 檢查 Skill ID 格式是否正確（只能用字母、數字、連字號）

### 問題：Skill 無法執行
**解決**：
1. 檢查 Skill 檔案路徑是否正確
2. 檢查 `.md` 檔案是否存在
3. 檢查 IDE 是否有讀取檔案的權限
4. 查看 IDE 的錯誤日誌

---

## 📞 支援

- 配置指南：`.claude/SKILLS_SETUP.md`
- Skills 索引：`skills/README.md`
- 專案規則：`CLAUDE.md` (根目錄)

---

**配置完成時間**：2026-05-17 13:31  
**配置版本**：1.0  
**下一步**：🔄 重啟 IDE → ✅ 驗證 Skill 已載入 → 🚀 開始使用

