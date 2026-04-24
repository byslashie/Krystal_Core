---
name: superpowers
description: 在開始任何對話時使用 - 建立如何尋找與使用技能的機制，要求在任何回應前先調用 Skill 工具。
---

# Superpower Skill

## 核心邏輯
如果你認為有 1% 的機會某個技能適用於當前任務，你「必須」調用該技能。這不是可選的，而是強制執行的。

## 指令優先級
1. 使用者的明確指令（CLAUDE.md, GEMINI.md 等）— 最高優先
2. Superpowers 技能 — 覆蓋預設系統行為
3. 預設系統提示 — 最低優先

## 使用規範
- 在給出最終答案前，必須檢查 `.agents/skills` 目錄。
- 優先尋找與任務相關的專用技能（如 ui-ux-pro-max, xs-skill 等）。
- 確保所有輸出的品質符合最高標準。
