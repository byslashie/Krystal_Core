---
title: Krystal Skills Registry
description: 所有 Skill 的註冊和使用指南
---

# 🎯 Krystal Skills Registry

本資料夾包含所有可用的 Skill。使用方式：

## 📋 已註冊的 Skills

### 1. `/strategy-reflection` 
**Krystal 的策略反思夥伴**

核心決策框架，包含 8 個鏡頭：
- 交易員思維（成本效益）
- 哲學家思維（價值對齐）
- PM 思維（系統檢查）
- 健康決策框架（證據+低成本+快驗）
- 痛點 vs 流量陷阱（自媒體）
- 風險管理（連虧停手）
- 注意力管理（單一上下文）
- PDCA 迭代（反饋迴路）

**檔案**：`krystal_strategy_reflection_partner.md`

**使用例**：
```
用戶：「幫我用八鏡頭框架分析這個決策」
Claude：[按照 8 個鏡頭逐一分析]
```

---

### 2. `/daily-check`
**四重身份日程檢查**

快速查詢「現在應該做什麼」，包括：
- 每日時程表（09:00-23:00）
- 週一～週日 特殊時段
- 身份切換規則（允許/禁止）
- 衝突解決優先級

**檔案**：`four_identities_daily_schedule.md`

**使用例**：
```
用戶：「現在 14:30，我要做什麼？」
Claude：[查閱日程] 「現在是 PM 工作時段，應該深度專注」
```

---

### 3. `/self-media-strategy`
**自媒體內容戰略**

內容生態和變現路徑，包括：
- 三大支柱（交易系統 + 人生規劃 + 身心平衡）
- TA 分析和痛點驅動
- 內容日曆框架
- 變現時線（2027.Q1 課程）

**檔案**：`self_media_content_strategy.md`

**使用例**：
```
用戶：「我的自媒體應該怎麼規劃？」
Claude：[按照三支柱框架分析內容方向和變現策略]
```

---

### 4. `/quick-ref`
**快速參考卡**

3 秒內快速查閱，包括：
- 時段快查
- 8 鏡頭檢查表
- 禁止行為清單
- 低 FODMAP 食物清單
- 交易進場條件
- 3-6-12 月檢查點

**檔案**：`quick_reference_v2_may2026.md`

**使用例**：
```
用戶：「快速參考」
Claude：[回傳快速參考卡的相關部分]
```

---

## 🚀 如何使用

### 方式 1：直接提及 Skill 名稱
```
「幫我用策略反思夥伴分析」
「檢查日程」
「自媒體戰略建議」
```

### 方式 2：用 `/` 命令呼叫（需在支持的環境中）
```
/strategy-reflection
/daily-check
/self-media-strategy
/quick-ref
```

### 方式 3：針對性請求
```
「用八鏡頭框架評估這個想法」
「現在應該做什麼？」
「檢查我的自媒體內容方向」
「給我快速參考」
```

---

## 📁 檔案結構

```
skills/
├─ README.md                                  (本文件)
├─ krystal_strategy_reflection_partner.md    (Skill #1)
├─ four_identities_daily_schedule.md         (Skill #2)
├─ self_media_content_strategy.md            (Skill #3)
└─ quick_reference_v2_may2026.md             (Skill #4)
```

---

## 🔄 Skill 維護

- **更新頻率**：每月檢查一次（特別是日程和自媒體策略）
- **修改流程**：編輯相應 .md 檔 → 更新 Git → 同步內存
- **新增 Skill**：在本 README 中註冊 → 在 skills/ 建立檔案 → 更新 MEMORY.md

---

**最後更新**：2026-05-16  
**維護者**：Krystal
