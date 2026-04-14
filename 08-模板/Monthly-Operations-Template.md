---
title: Monthly Ops – <% tp.date.now("YYYY-MM") %>
type: ops_monthly
---

# 📅 月度流程（<% tp.date.now("YYYY-MM") %>）

## 1) Classifiers（M1/M2/N3）
- [ ] M1：更新 macro_state / regime_score  📅 <% tp.date.now("YYYY-MM-05") %>
- [ ] M2：更新季節性旗標（TOM/FOMC/財報季/結算） 📅 <% tp.date.now("YYYY-MM-05") %>
- [ ] N3：彙總本月趨勢狀態與信心分數 📅 <% tp.date.now("YYYY-MM-05") %>

## 2) D1 決策 & A1 配置
- [ ] 產出 D1：`decision_<% tp.date.now("YYYYMM") %>.yaml`（含 overrides 說明） 📅 <% tp.date.now("YYYY-MM-06") %>
- [ ] 產出 A1：`allocation_<% tp.date.now("YYYYMM") %>.csv` 📅 <% tp.date.now("YYYY-MM-07") %>

## 3) Strategies（S1/S3/S4/S5）
- [ ] 升/降權與啟停確認（依 D1 + N3） 📅 <% tp.date.now("YYYY-MM-07") %>
- [ ] 新版規則如有 → 在 Versions/ 建 `v___`（Summary/變更點） 📅 <% tp.date.now("YYYY-MM-08") %>
- [ ] 回測（Backtests）附件歸檔（equity/monthly/trades + frontmatter 指標） 📅 <% tp.date.now("YYYY-MM-08") %>

## 4) Risk / Monitoring / EXE
- [ ] R1：本月風控參數檢視（停損比例/連虧 N / 事件日白名單） 📅 <% tp.date.now("YYYY-MM-09") %>
- [ ] R2：VaR/CVaR 限額與警報門檻確認 📅 <% tp.date.now("YYYY-MM-09") %>
- [ ] EXE：路由/重試策略 & API health 檢查 📅 <% tp.date.now("YYYY-MM-09") %>

## 5) 報告與備份
- [ ] 05-Reports：撰寫「七段式」月報（觀測→數據→策略→回測→配置→風控→部署） 📅 <% tp.date.now("YYYY-MM-10") %>
- [ ] N1：備份與通知（本月決策/配置/告警摘要） 📅 <% tp.date.now("YYYY-MM-10") %>

## 6) Registry（策略總表）
- [ ] 更新上線策略/版本（status: online/offline/testing + 指標） 📅 <% tp.date.now("YYYY-MM-10") %>
