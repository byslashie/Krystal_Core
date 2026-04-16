---
title: Daily Run – <% tp.date.now("YYYY-MM-DD") %>
type: ops_daily
---

# 📒 日常 Runbook（<% tp.date.now("YYYY-MM-DD ddd") %>）

## 盤前
- [ ] 檢查資料更新（價格/指標/旗標）
- [ ] 事件白名單（M2）確認
- [ ] EXE 連線健康檢查

## 盤中
- [ ] R2 警報監看（DD/VaR）
- [ ] 例外事件紀錄（策略暫停/降權）

## 盤後
- [ ] Sx 成交/績效回寫（positions/perf/trades）
- [ ] 異常歸檔（exe_log / alerts）
- [ ] 翌日待辦建立
