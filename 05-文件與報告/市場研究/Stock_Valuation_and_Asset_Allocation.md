# 《景氣循環到選股策略》個股評估與 Krystal AI 系統選股器實作指南 (完整擴充版)

本文件旨在將「個股基本面分析」與「動態估值模型」轉化為 **Krystal AI 交易系統**的資料庫欄位要求與選股過濾器 (Screener) 腳本。內容已大幅擴充包含實戰案例解析、完整的風險控制參數，以及具體的評價演算法邏輯。

---

## 1. 贏勢股基本面四大面向分析：Krystal AI 資料庫所需欄位 (Database Schema)

要在系統內做到「全自動化」篩選，您的資料庫中每一檔個股都需要具備以下數據點，並實作交叉比對：

### A. 長期競爭力 (Long-term Competitiveness)
*   **數據點 1：市場份額排名 (Market Share Rank)**：該企業在其細分市場的市佔率。若位居 Top 3，在運算池中給予加分。
*   **數據點 2：規模護城河 (Scale Moat)**：追蹤長期資本支出 (CapEx) 是否顯著高於同行（例如台積電在先進製程的投入），並轉化為營收規模（營收差距倍數）。

### B. 成長力模組 (Growth Potential)
*   **數據點 3：潛在市場規模年均複合增長率 (TAM CAGR)**：例如 AI 伺服器、矽智財 (IP) 產業的預估成長率若 `> 10%`，其所屬概念股池優先納入。
*   **數據點 4：單一大客戶依賴度與供應商等級**：系統可對接供應鏈關聯資料庫。若客戶群涵蓋全球前五大科技巨頭（如 Apple, Nvidia）且為獨家或第一供應商，自動標記為「高成長潛能」。

### C. 獲利品質模組 (Profitability)
*   **數據點 5：三率趨勢 (Margins Trend)**：
    *   計算 **毛利率 (Gross Margin)** 與 **營業利益率 (Operating Margin)** 是否連兩季季增 (QoQ > 0)。這代表公司產品不需降價求售，具備定價權（反映高金含量產品組合的成效）。
*   **數據點 6：高獲利產品組合佔比 (Product Mix %)**：針對財報中的高毛利業務條線，建立「該業務佔比持續升高」的檢測邏輯。

### D. 系統避險與風險雷達系統 (Risk Alerts)
*   **數據警報 1：存貨週轉天數 (Days Sales of Inventory, DSI)**：
    *   *系統觸發條件*：若連續 2 季 `本季 DSI > 去年同期 DSI` 且整體產業仍在衰退，Krystal AI 發佈【庫存積壓警報】，該檔個股自買入候選名單剔除。
*   **數據警報 2：市場預期與估值過熱 (Expectation Overheat)**：
    *   *系統觸發條件*：若本益比飆升速度大於 EPS 成長速度的 2 倍以上，或機構分析師群開始下修盈餘預期，切換為「只賣不買」模式。

---

## 2. 系統自動化：三通道動態估值模型切換 (Dynamic Valuation Models)

Krystal AI 系統不應單以「本益比」橫掃全市場。請在後端撰寫一組 Router (路由器) 條件判斷式，針對股票基本面態樣自動切換不同的估值通道線：

### 📈 模型一：本益比 (PE) 河流圖通道
*   **系統判定條件 (Router Condition)**：`連續 3 年 EPS > 0 AND 營收穩定成長`
*   **適用範圍**：穩健獲利型企業（如：蘋果、台積電）。
*   **Krystal AI 計算邏輯**：
    *   基準公式：`預期目標價 = 預估未來 4 季 EPS 加總 × 過去 3-5 年合理本益比均值 (或區間區段)`。
    *   **買進觸發點**：過去 3 年 PE Band 的下緣區間（例如 `-1 倍標準差`）。
    *   **賣出觸發點**：過去 3 年 PE Band 的上緣區間（例如 `+1.5 倍標準差`）。

### 📉 模型二：股價淨值比 (PB) 河流圖通道
*   **系統判定條件 (Router Condition)**：`近三年內曾出現 EPS < 0 或 屬於景氣循環/重資產板塊 (Sector in ['金融', '鋼鐵', '航運', '記憶體'])`
*   **適用範圍**：受景氣大波動影響、資產導向或營運不穩定的股票。
*   **Krystal AI 計算邏輯**：
    *   基準公式：`預期目標價 = 最近一季每股淨值 (BVPS) × 過去 3-5 年歷史合理 PB 區間`。
    *   *避坑指南*：在股價淨值比極高時（通常此時 EPS 暴衝，導致本益比看起來非常低），應判斷為賣出時機；反之，PB 低於歷史均值，往往是景氣落底的買點。

### 🚀 模型三：股價營收比 (PS) 河流圖通道
*   **系統判定條件 (Router Condition)**：`近期 EPS < 0 (虧損) AND 近三年平均營收 CAGR > 20%`
*   **適用範圍**：營收正在爆發期的新創 SaaS、AI 或生技科技股（如虧損時期的 Snowflake）。
*   **Krystal AI 計算邏輯**：
    *   基準公式：`預期目標價 = 預估未來一年每股營收 (SPS) × 歷史 PS 倍數`。
    *   **防錯機制**：在系統層級，必須加入「毛利率 (Gross Margin)」輔助驗證。若毛利率下滑，代表公司是用犧牲獲利、削價競爭換取營收擴張，系統應判定該 PS 估值失效！

### 📊 模型四：現金流量折現法 (DCF) 參考通道
*   **適用範圍**：穩定收息股（如公用事業）。
*   *備註*：在量化系統中，因變數干擾大，DCF 模型通常只做為輔助參考，不建議作為絕對且單一的長線量化開倉條件。

---

## 3. Krystal AI 成長股選股腳本 (實戰微調版 Pseudo-code)

利用課程中提到的矽智財龍頭 Synopsys (或如同台積電的高護城河公司) 作為基準，我們可以把選股程式碼優化如下：

```python
def krystal_screener_growth_leaders(stock_list):
    recommended_candidates = []
    
    for stock in stock_list:
        # 第一關：產業趨勢紅利 (TAM CAGR) 需 > 10%
        if stock.industry_metrics.expected_cagr < 0.10: 
            continue
            
        # 第二關：優於同業的獲利動能 (預期 EPS 成長 > 15%)
        if stock.financials.fwd_eps_growth_1yr < 0.15: 
            continue
            
        # 第三關：企業定價霸權與產品含金量 (毛利率檢定)
        if stock.financials.gross_margin < 0.40:
            continue
        # 且毛利率不得呈現連續衰退
        if not stock.financials.is_gross_margin_expanding(periods=2):
            continue
            
        # 第四關：庫存積水風險過濾 (DSI Check)
        if stock.risk_factors.is_dsi_increasing_abnormally():
            log_warning(f"剔除 {stock.ticker}：庫存週轉天數異常惡化")
            continue
            
        # 第五關：動態估值路徑選擇
        if stock.financials.is_profitable_for_3_years():
            valuation_band = calculate_pe_band(stock)
        elif stock.financials.revenue_3yr_cagr > 0.20:
            valuation_band = calculate_ps_band(stock)
        else:
            valuation_band = calculate_pb_band(stock)
            
        # 最終判定：股價落入歷史合理/低估通道地帶
        if stock.current_price < valuation_band.fair_value_upper_limit:
            # 計算潛在獲利空間 (Upside Potential)
            upside = (valuation_band.target_price - stock.current_price) / stock.current_price
            recommended_candidates.append({
                "ticker": stock.ticker,
                "strategy": "Growth Leader",
                "valuation_model_used": valuation_band.model_name,
                "upside_potential": upside
            })

    # 依照潛在獲利空間由大到小排序返回
    return sort_by_upside(recommended_candidates)
```
