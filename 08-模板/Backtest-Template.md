---
title: <%- tp.file.title %>
type: backtest
module: <%* tR = await tp.system.prompt("Module code (e.g., S1)"); tR %>
version: <%* v = await tp.system.prompt("Version (e.g., v002)"); v %>
tag: <%* tg = await tp.system.prompt("Tag (e.g., baseline)"); tg %>
run_date: <%* rd = await tp.system.prompt("Run date (YYYY-MM-DD)"); rd %>
start_date: <%* sd = await tp.system.prompt("Start date (YYYY-MM-DD)"); sd %>
end_date: <%* ed = await tp.system.prompt("End date (YYYY-MM-DD)"); ed %>
benchmark: 60/40
cagr: 
sharpe: 
sortino: 
mdd: 
calmar: 
win_rate: 
trades: 
turnover: 
---

# Summary
- 區間：<% sd %> → <% ed %>（回測於 <% rd %>）
- 版本/標籤：**<% v %> / <% tg %>**
- 成果：CAGR **<>**，Sharpe **<>**，MDD **<>**，Calmar **<>**，勝率 **<>**，交易數 **<>**

## 參數（Parameters）
```yaml
universe: [QQQ, SPY, VTI, IEF, TLT, GLD]
lookbacks: [63, 126, 252]
top_k: 2
weight_method: vol_inv
rebalance: monthly
```
