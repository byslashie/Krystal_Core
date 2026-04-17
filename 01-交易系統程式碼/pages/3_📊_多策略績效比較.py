import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime
from io import StringIO
import requests
import json
import urllib3
import sys
from pathlib import Path

# 导入UI主题
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme

# 忽略 urllib3 的 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== Page Config =====================
st.set_page_config(layout="wide", page_title="Multi-Strategy Comparison", page_icon="📊", initial_sidebar_state="expanded")

# 应用现代主题
apply_theme(st)

# ===================== Styles =====================
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(91, 71, 217, 0.2);
        text-align: center;
    }
    .delta-positive { color: #10B981; font-weight: bold; }
    .delta-negative { color: #EF4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("📊 多策略績效比較工具 (Multi-Strategy Comparison)")

# ===================== Path Config =====================
STRATEGY_DIR = r"g:\我的雲端硬碟\Krystal_AI_Trading_System\data\strategies"
if not os.path.exists(STRATEGY_DIR):
    os.makedirs(STRATEGY_DIR)

# ===================== Helper Functions =====================

def _norm_col(s):
    if s is None: return ""
    s = str(s).strip().lower()
    for a, b in {"（": "(", "）": ")", "　": " ", "_": "", "-": "", "/": "", "\\": ""}.items():
        s = s.replace(a, b)
    s = s.replace(" ", "")
    return s

def _find_first(df, candidates):
    cand_list = list(candidates) if isinstance(candidates, (list, tuple)) else [candidates]
    norm_map = {_norm_col(c): c for c in df.columns}
    for c in cand_list:
        n = _norm_col(c)
        if n in norm_map: return norm_map[n]
    for ncol, orig in norm_map.items():
        for c in cand_list:
            n = _norm_col(c)
            if n and (n in ncol or ncol in n): return orig
    return None

def process_strategy_df(file_path_or_buffer, name, base_cap=1000000):
    try:
        # 1. 讀取檔案
        xl = None
        sheets = {}
        if name.endswith(".csv"):
            try:
                if hasattr(file_path_or_buffer, 'seek'): file_path_or_buffer.seek(0)
                df_raw = pd.read_csv(file_path_or_buffer, encoding="cp950")
            except:
                try:
                    if hasattr(file_path_or_buffer, 'seek'): file_path_or_buffer.seek(0)
                    df_raw = pd.read_csv(file_path_or_buffer, encoding="utf-8")
                except:
                    if hasattr(file_path_or_buffer, 'seek'): file_path_or_buffer.seek(0)
                    df_raw = pd.read_csv(file_path_or_buffer)
            sheets["Single"] = df_raw
        else:
            xl = pd.ExcelFile(file_path_or_buffer)
            for s in xl.sheet_names:
                sheets[s] = xl.parse(s)

        # 2. 定義處理單一 DataFrame 的內部函數
        def find_cols_and_process(df_in, sheet_type="Daily"):
            df = df_in.copy()
            # 嘗試去掉前幾行 metadata
            if len(df.columns) < 3 or df.columns[0].startswith("Unnamed"):
                best_df = df
                for i in range(15): # Increase search depth
                    if i + 1 >= len(df_in): break
                    test_df = df_in.iloc[i+1:].reset_index(drop=True)
                    test_df.columns = df_in.iloc[i].values
                    if len(test_df.columns) > 3 and not str(test_df.columns[0]).startswith("Unnamed"):
                        best_df = test_df
                        break
                df = best_df

            # 擴充 Date 欄位關鍵字
            date_candidates = ["日期", "時間", "出場時間", "出場日期", "close time", "exit time", "date", "datetime", 
                               "平倉時間", "平倉日期", "Time", "Date", "Entry Time", "進場時間"]
            
            # 擴充 PnL 欄位關鍵字
            pnl_candidates = ["獲利金額", "總獲利", "pnl", "profit", "獲利", "損益", "淨損益", 
                              "平倉損益", "單筆損益", "Net Profit", "Realized PnL"]
            
            # 擴充 Return 欄位
            ret_candidates = ["報酬率", "return", "roi", "ret", "Percent", "百分比"]

            col_out_time = _find_first(df, date_candidates)
            col_pnl = _find_first(df, pnl_candidates)
            col_ret = _find_first(df, ret_candidates)
            
            # Debug info
            # st.write(f"Sheet ({sheet_type}) Columns Found: Time={col_out_time}, PnL={col_pnl}")
            
            if not col_out_time or not col_pnl: return None, None

            df[col_out_time] = pd.to_datetime(df[col_out_time], errors="coerce")
            df = df.dropna(subset=[col_out_time]).sort_values(col_out_time).set_index(col_out_time)
            
            def clean_num(series):
                s = series.astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False).str.replace(' NTD', '', regex=False).str.strip()
                return pd.to_numeric(s, errors='coerce').fillna(0)

            df["pnl_val"] = clean_num(df[col_pnl])
            
            # 計算 ret_val
            if col_ret:
                s_str = df[col_ret].astype(str).str.replace('%','',regex=False).str.replace(',','',regex=False).str.strip()
                s_val = pd.to_numeric(s_str, errors='coerce').fillna(0)
                if not s_val.empty:
                    q80 = s_val.abs().quantile(0.80)
                    if q80 > 1.5: s_val = s_val / 100.0
                    df["ret_val"] = s_val
            else:
                # 僅對 Daily 進行 cumsum 偵測
                if sheet_type == "Daily":
                    is_cum = any(x in col_pnl for x in ["總", "equity", "cum", "累計"])
                    if not is_cum and len(df) > 10:
                        is_mostly_monotonic = (df["pnl_val"].diff() >= 0).mean() > 0.9
                        if is_mostly_monotonic and df["pnl_val"].iloc[-1] > df["pnl_val"].iloc[0] * 2:
                            is_cum = True
                    
                    if is_cum:
                        df["ret_val"] = df["pnl_val"].diff().fillna(0) / base_cap
                        df["pnl_val"] = df["pnl_val"].diff().fillna(0)
                    else:
                        df["ret_val"] = df["pnl_val"] / base_cap
                else:
                    # Trade List: Return = PnL / Base (Approx)
                     df["ret_val"] = df["pnl_val"] / base_cap

            return df, col_out_time

        # 3. 分類 Sheet
        df_daily = None
        df_trade = None
        
        # 尋找 Daily 表 (優先級: 每日 > Daily > Equity)
        target_daily_sheet = None
        for k in ["每日", "Daily", "報表", "Equity"]:
             for s in sheets:
                 if k in s: target_daily_sheet = s; break
             if target_daily_sheet: break

        if not target_daily_sheet and len(sheets) == 1:
            target_daily_sheet = list(sheets.keys())[0]
            
        if target_daily_sheet:
            processed_daily, _ = find_cols_and_process(sheets[target_daily_sheet], "Daily")
            if processed_daily is not None: df_daily = processed_daily

        # 尋找 Trade 表 (優先級: 交易分析 > Trade > 明細)
        target_trade_sheet = None
        # 用戶指定優先： "交易分析"
        for k in ["交易分析", "交易明細", "Trade Analysis", "Trade List", "交易", "Trade", "分析", "Analysis"]:
             for s in sheets:
                 if k in s: target_trade_sheet = s; break
             if target_trade_sheet: break
        
        # 避免 Daily 和 Trade 抓到同一張表 (除非只有一張)
        if target_trade_sheet == target_daily_sheet and len(sheets) > 1:
             # 再找一次，排除 daily sheet
             target_trade_sheet = None
             for k in ["交易分析", "交易明細", "Trade Analysis", "Trade List", "交易", "Trade", "分析", "Analysis"]:
                 for s in sheets:
                     if s != target_daily_sheet and k in s: target_trade_sheet = s; break
                 if target_trade_sheet: break

        if target_trade_sheet:
            processed_trade, found_col_time = find_cols_and_process(sheets[target_trade_sheet], "Trade")
            if processed_trade is not None: 
                df_trade = processed_trade
        
        if df_daily is None and df_trade is None: return None

        # Fallback
        is_fallback = False
        if df_daily is None and df_trade is not None: df_daily = df_trade.copy()
        if df_trade is None and df_daily is not None: 
             df_trade = df_daily.copy() # Fallback to daily
             is_fallback = True

        return {
            "daily": df_daily,
            "trade": df_trade,
            "source_daily": target_daily_sheet,
            "source_trade": target_trade_sheet if not is_fallback else f"{target_daily_sheet} (Fallback)",
            "is_fallback": is_fallback
        }, (df_daily.index if df_daily is not None else df_trade.index)

    except Exception as e:
        st.error(f"解析 {name} 失敗: {e}")
        return None

def calculate_metrics(strategy_data, name):
    if strategy_data is None: return {}
    
    df_daily = strategy_data.get('daily')
    df_trade = strategy_data.get('trade')
    source_trade = strategy_data.get('source_trade', 'Unknown')
    
    metrics = {}
    
    # 1. Daily Metrics
    if df_daily is not None and not df_daily.empty:
        pnl = df_daily["pnl_val"]
        ret = df_daily["ret_val"].dropna()
        net_profit = pnl.sum()
        cum_pnl = pnl.cumsum()
        dd_amt = cum_pnl - cum_pnl.cummax()
        mdd_amt = dd_amt.min()
        
        if not ret.empty and len(ret) > 1:
            nav = (1 + ret).cumprod()
            mdd_pct = (nav / nav.cummax() - 1.0).min()
            try: years = (df_daily.index[-1] - df_daily.index[0]).days / 365.25
            except: years = 1.0
            years = max(years, 0.1)
            cagr = (nav.iloc[-1])**(1/years) - 1 if nav.iloc[-1] > 0 else -1
            sharpe = (ret.mean() * 252) / (ret.std() * np.sqrt(252) + 1e-12)
            downside_ret = ret[ret < 0]
            downside_std = downside_ret.std() * np.sqrt(252) if not downside_ret.empty else 1e-12
            sortino = (ret.mean() * 252) / (downside_std + 1e-12)
            calmar = cagr / abs(mdd_pct) if mdd_pct != 0 else np.nan
        else:
            cagr = mdd_pct = sharpe = sortino = calmar = 0
            
        metrics.update({
            "總淨利 ($)": net_profit, "年化報酬 (CAGR)": cagr * 100,
            "最大回撤 (MDD %)": mdd_pct * 100, "最大回撤 ($)": mdd_amt, 
            "夏普比率": sharpe, "索提諾比率 (Sortino)": sortino, "卡瑪比率 (Calmar)": calmar
        })
    else:
        metrics.update({
            "總淨利 ($)": 0, "年化報酬 (CAGR)": 0, "最大回撤 (MDD %)": 0, 
            "夏普比率": 0, "索提諾比率 (Sortino)": 0, "卡瑪比率 (Calmar)": 0
        })

    # 2. Trade Metrics
    target_df = df_trade if df_trade is not None else df_daily
    
    if target_df is not None and not target_df.empty:
        pnl_t = target_df["pnl_val"]
        active_pnl = pnl_t[pnl_t != 0]
        
        count = len(target_df)
        win_rate = (active_pnl > 0).mean() if not active_pnl.empty else 0
        
        wins = active_pnl[active_pnl > 0]
        losses = active_pnl[active_pnl < 0]
        avg_win = wins.mean() if not wins.empty else 0
        avg_loss = abs(losses.mean()) if not losses.empty else 1e-9
        win_loss_ratio = avg_win / avg_loss
        profit_factor = wins.sum() / abs(losses.sum()) if not losses.empty else np.inf
        
        p = win_rate
        b = win_loss_ratio
        kelly = p - (1 - p) / b if b > 0 and p > 0 else 0
        expectancy = p * b
        
        metrics.update({
            f"獲利因子 (PF)": profit_factor,
            f"勝率 (%)": win_rate * 100,
            f"風報比": win_loss_ratio,
            f"期望值": expectancy,
            f"凱利準則 (%)": kelly * 100,
            f"交易筆數": count,
            "資料來源": source_trade  # 顯式顯示來源
        })
    else:
        metrics.update({
            "獲利因子 (PF)": 0, "勝率 (%)": 0, 
             "風報比": 0, "期望值": 0, "凱利準則 (%)": 0, "交易筆數": 0,
             "資料來源": "N/A"
        })

    metrics["策略名稱"] = name
    return metrics

# ===================== Data Loading =====================

# 收合提示
st.sidebar.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(91, 71, 217, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 12px;
    text-align: center;
    font-size: 12px;
    color: #6B7280;
">
    💡 點擊左上角 ≡ 收合此面板
</div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 檔案管理")
base_capital = st.sidebar.number_input("💰 假設初始資金 ($)", value=1000000, step=100000, help="用於計算報酬率與淨值曲線的基準資本。")
uploaded_files = st.sidebar.file_uploader("上傳策略 CSV/Excel", accept_multiple_files=True, type=["csv", "xlsx", "xls"])
scan_folder = st.sidebar.button("🔄 掃描 data/strategies 資料夾")

if "strategies" not in st.session_state:
    st.session_state.strategies = {}

# Force clear strategies on scan to ensure fresh load
if st.sidebar.button("🗑️ 清除所有快取 (Reset)", type="primary"):
    st.session_state.strategies = {}
    st.experimental_rerun()

if "strategies" not in st.session_state:
    st.session_state.strategies = {}

# Force clear strategies on scan to ensure fresh load
if scan_folder:
    st.session_state.strategies = {} 
    for f in os.listdir(STRATEGY_DIR):
        if f.endswith((".csv", ".xlsx", ".xls")):
            path = os.path.join(STRATEGY_DIR, f)
            res = process_strategy_df(path, f, base_capital)
            if res: st.session_state.strategies[f] = res[0]

if uploaded_files:
    # We should probably clear strategies if new files are uploaded to avoid confusion, 
    # but user might want to compare with existing. Let's keep append behavior but clear if user re-uploads same name.
    for uf in uploaded_files:
        res = process_strategy_df(uf, uf.name, base_capital)
        if res: st.session_state.strategies[uf.name] = res[0]

if not st.session_state.strategies:
    st.info("請上傳檔案或掃描資料夾以開始比較。")
    st.stop()

# ===================== Selection UI =====================
selected_names = st.multiselect("選擇要比較的策略", options=list(st.session_state.strategies.keys()), default=list(st.session_state.strategies.keys()))
if not selected_names:
    st.warning("請至少選擇一個策略。")
    st.stop()

# ===================== Metrics Table =====================
st.subheader("📋 績效指標對照")
comparison_rows = [calculate_metrics(st.session_state.strategies[name], name) for name in selected_names]
comp_df = pd.DataFrame(comparison_rows).set_index("策略名稱")

# 表格樣式與顏色標示
def color_expectancy(val):
    if val < 0.5: color = '#ffcccc' # 🔴 較低
    elif val < 0.8: color = '#fff3cd' # 🟡 中等
    else: color = '#d4edda' # 🟢 優異
    return f'background-color: {color}'

def color_rr_ratio(val):
    if val < 1.0: color = '#ffcccc' # 🔴 虧損風險大
    elif val < 2.0: color = '#fff3cd' # 🟡 常規水平
    else: color = '#d4edda' # 🟢 高風報比 (優質)
    return f'background-color: {color}'

st.dataframe(comp_df.style.format({
    "總淨利 ($)": "{:,.0f}", "年化報酬 (CAGR)": "{:.2f}%", "最大回撤 (MDD %)": "{:.2f}%",
    "最大回撤 ($)": "{:,.0f}",
    "夏普比率": "{:.2f}", "索提諾比率 (Sortino)": "{:.2f}", "卡瑪比率 (Calmar)": "{:.2f}",
    "獲利因子 (PF)": "{:.2f}", "勝率 (%)": "{:.2f}%", "風報比": "{:.2f}", "期望值": "{:.2f}",
    "凱利準則 (%)": "{:.2f}%", "交易筆數": "{:,.0f}",
    "資料來源": "{}"
}).applymap(color_expectancy, subset=['期望值'])
  .applymap(color_rr_ratio, subset=['風報比']), use_container_width=True)

with st.expander("💡 績效指標解釋 (Metrics Glossary)"):
    st.markdown("""
    - **年化報酬 (CAGR)**: 策略的幾何平均年增長率。
    - **最大回撤 (MDD %)**: 淨值從最高點回落的最大幅度，衡量策略最糟糕時的虧損風險。
    - **夏普比率 (Sharpe Ratio)**: 衡量「風險/報酬比」。數值 > 1 表示策略表現良好，> 2 非常優秀。
    - **索提諾比率 (Sortino Ratio)**: 與夏普類似，但只考慮「下跌」帶來的波動，對於怕虧損的投資者更有參考價值。
    - **卡瑪比率 (Calmar Ratio)**: 年化報酬除以最大回撤。通常 > 2 被認為是很棒的穩定策略。
    - **獲利因子 (Profit Factor)**: 總獲利除以總虧損。> 1 代表獲利，> 1.5 代表具備穩定的競爭優勢。
    - **風報比 (Risk/Reward Ratio)**: 平均賺多少除以平均賠多少。衡量每承擔 1 元風險能換取多少報酬。
        - **🔴 < 1.0**: 入不敷出，需極高勝率才能獲利。
        - **🟡 1.0 ~ 2.0**: 一般水平，大眾交易系統常見區間。
        - **🟢 > 2.0**: **高風報比**，具備「大賺小賠」的優秀基因。
    - **期望值 (Expectancy)**: 勝率 × 風報比。衡量單次交易平均能帶來的潛在回饋。
        - **🔴 < 0.5**: 低於損益兩平點 (若不計手續費)。
        - **🟡 0.5 ~ 0.8**:具備盈利基礎，但穩定性中等。
        - **🟢 > 0.8**: **高品質交易邏輯**，長期獲利潛力強。
    - **凱利準則 (Kelly %)**: 根據盈虧比與勝率推導出的理想下注仓位比例。
    """)

with st.expander("📚 交易聖經：勝率 vs 風報比對照矩陣 (Win Rate & R:R Cheatsheet)"):
    st.markdown("""
    這張矩陣表揭示了量化交易的核心：**獲利不只靠勝率，更靠風報比（賺賠比）。**
    - **風報比 1:3** 代表「賠 1 元時，平均賺 3 元」 (數值 = 3.0)。
    - **十進位數值 (1.3)** 代表「1 : 1.3」，表示每承擔 1 元風險換取 1.3 元獲利。
    
    **標色說明：**
    - **🔴 區域 (LOSS)**：長期交易會導致資金縮水。
    - **⚪ 區域 (BREAK EVEN)**：損益兩平點。
    - **🟢 區域 (PROFIT)**：具備長期正期望值。
    """)
    
    # 建立 Cheatsheet 數據
    rr_labels = ["1:1 (Ratio 1.0)", "1:2 (Ratio 2.0)", "1:3 (Ratio 3.0)", "1:4 (Ratio 4.0)", "1:5 (Ratio 5.0)"]
    wr_labels = ["20%", "30%", "40%", "50%", "60%"]
    
    data = [
        ["🔴 虧損", "🔴 虧損", "🔴 虧損", "⚪ 兩平", "🟢 獲利"], # 1:1
        ["🔴 虧損", "🔴 虧損", "🟢 獲利", "🟢 獲利", "🟢 獲利"], # 1:2
        ["🔴 虧損", "🟢 獲利", "🟢 獲利", "🟢 獲利", "🟢 獲利"], # 1:3
        ["⚪ 兩平", "🟢 獲利", "🟢 獲利", "🟢 獲利", "🟢 獲利"], # 1:4
        ["🟢 獲利", "🟢 獲利", "🟢 獲利", "🟢 獲利", "🟢 獲利"], # 1:5
    ]
    
    chart_df = pd.DataFrame(data, index=rr_labels, columns=wr_labels)
    chart_df.index.name = "風報比 (風險 : 報酬)"
    
    def style_cheatsheet(val):
        if "獲利" in val: color = '#d4edda' 
        elif "兩平" in val: color = '#e2e3e5' 
        else: color = '#f8d7da' 
        return f'background-color: {color}; color: black; font-weight: bold; text-align: center;'

    st.table(chart_df.style.applymap(style_cheatsheet))
    
    st.info("💡 **核心提醒：** 您的策略風報比顯示為 **1.3**，代表它是 **1 : 1.3** 的水平。若要獲利，勝率必須穩定維持在 **44% 以上** (參考 1:1 到 1:2 之間的區間)。")

# 綜合評價排名
if len(selected_names) >= 1:
    st.markdown("### 🏆 策略綜合評比摘要 (Best Strategy Summary)")
    # 簡單權重評分：夏普 (40%) + 卡瑪 (40%) + 勝率 (20%) -> 均標準化
    def get_rank_score(row):
        # 標準化避免維度不一
        sharpe_score = row['夏普比率'] / (comp_df['夏普比率'].max() + 1e-9)
        calmar_score = row['卡瑪比率 (Calmar)'] / (comp_df['卡瑪比率 (Calmar)'].max() + 1e-9)
        win_score = row['勝率 (%)'] / (comp_df['勝率 (%)'].max() + 1e-9)
        return (sharpe_score * 0.4) + (calmar_score * 0.4) + (win_score * 0.2)

    rank_df = comp_df.copy()
    rank_df['綜合得分'] = rank_df.apply(get_rank_score, axis=1)
    best_strat_name = rank_df['綜合得分'].idxmax()
    best_row = rank_df.loc[best_strat_name]
    
    c1, c2 = st.columns([1, 3])
    with c1:
        st.success(f"**綜合推薦：{best_strat_name}**")
        st.metric("綜合評分", f"{best_row['綜合得分']:.2f}")
    with c2:
        # 增加策略風格自動診斷
        rr = best_row['風報比']
        wr = best_row['勝率 (%)']
        
        # 根據新的數據範圍調整診斷邏輯
        if rr > 5.0 and wr > 60:
            style_desc = "🦄 **聖杯級策略 (Holy Grail)**：極高勝率搭配極高風報比，這是量化交易的終極目標。"
        elif rr > 3.0 and wr > 50:
            style_desc = "🚀 **超級趨勢型**：具備強大的獲利爆發力，且勝率維持在水準之上。"
        elif rr > 2.0 and wr < 40:
            style_desc = "🎯 **趨勢跟隨型**：高風報比，靠「大賺」彌補低勝率，淨值波動可能較大。"
        elif rr < 1.5 and wr > 60:
            style_desc = f"🛡️ **高勝率穩健型**：風報比 {rr:.1f} 雖屬常規，但靠 **{wr:.0f}% 的高勝率** 換取穩定的收益期望。"
        elif rr > 1.5 and wr > 45:
            style_desc = "💎 **全能平衡型**：兼具不錯的勝率與風報比，是量化交易中的理想目標。"
        else:
            style_desc = "⚙️ **常規型策略**：各項指標均衡，建議持續觀察回撤控制。"
            
        st.write(f"**策略風格分析：** \n{style_desc}")
        
        # 動態生成下方的 Trading Tip
        if rr < 1.5:
            tip_msg = f"風報比 **{rr:.1f}** 雖不算極高，但在統計學上，只要您的勝率能撐在 **{50 if rr > 1 else 60}% 以上**，這就是一台穩定的印鈔機。"
        elif rr > 3.0:
            tip_msg = f"風報比高達 **{rr:.1f}**，這意味著您每筆虧損能換取 **{rr:.1f} 倍** 的獲利，即使勝率稍低也能大幅獲利。"
        else:
            tip_msg = f"風報比 **{rr:.1f}** 處於健康區間，請繼續保持目前的進出場紀律。"
            
        st.info(f"💡 **交易室筆記：** {tip_msg}")

# ===================== Radar Chart =====================
st.subheader("🕸️ 策略維度分析 (Radar Chart)")
def create_radar_chart(df_metrics):
    categories = ['年化報酬', '夏普比率', '勝率', '獲利因子', '風險控制(1/MDD)']
    fig = go.Figure()
    # 欄位映射
    cols_to_norm = {'年化報酬 (CAGR)': '年化報酬', '夏普比率': '夏普比率', '勝率 (%)': '勝率', '獲利因子 (PF)': '獲利因子'}
    
    for name, row in df_metrics.iterrows():
        values = []
        for col_orig in cols_to_norm:
            if col_orig in row:
                val = row[col_orig]; mx = df_metrics[col_orig].max(); mn = df_metrics[col_orig].min()
                values.append((val - mn) / (mx - mn + 1e-12) if mx != mn else 0.5)
            else:
                 values.append(0)

        # Risk control norm
        if '最大回撤 (MDD %)' in row:
            dd = abs(row['最大回撤 (MDD %)']); mx_dd = abs(df_metrics['最大回撤 (MDD %)']).max(); mn_dd = abs(df_metrics['最大回撤 (MDD %)']).min()
            values.append(1 - (dd - mn_dd) / (mx_dd - mn_dd + 1e-12) if mx_dd != mn_dd else 0.5)
        else:
            values.append(0)

        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=name))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)
    return fig
st.plotly_chart(create_radar_chart(comp_df), use_container_width=True)

# ===================== NAV Chart =====================
st.subheader("📈 淨值曲線 (NAV) 比較")
fig = go.Figure()
for name in selected_names:
    # Fix: Access ['daily'] from dict
    strat_data = st.session_state.strategies[name]
    df = strat_data.get('daily')
    
    if df is not None and not df.empty and "ret_val" in df.columns:
        ret = df["ret_val"].dropna()
        if not ret.empty:
            nav = (1 + ret).cumprod()
            fig.add_trace(go.Scatter(x=ret.index, y=nav, mode="lines", name=name))
fig.update_layout(xaxis_title="時間", yaxis_title="淨值 (起點=1)", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# ===================== Drawdown Chart =====================
st.subheader("📉 回撤曲線 (Drawdown %) 比較")
fig_dd_all = go.Figure()
for name in selected_names:
    strat_data = st.session_state.strategies[name]
    df = strat_data.get('daily')
    if df is not None and not df.empty and "ret_val" in df.columns:
        ret = df["ret_val"].dropna(); nav = (1 + ret).cumprod()
        dd_pct = (nav / nav.cummax() - 1.0) * 100
        fig_dd_all.add_trace(go.Scatter(x=ret.index, y=dd_pct, mode="lines", name=f"{name} DD%", fill='tozeroy'))

fig_dd_all.update_layout(xaxis_title="時間", yaxis_title="Drawdown %", hovermode="x unified")
st.plotly_chart(fig_dd_all, use_container_width=True)

# ===================== Optimization Analysis (A vs B) =====================
st.divider()
st.subheader("🔬 優化前後分析 (A vs B)")
col1, col2 = st.columns(2)
base_strat = col1.selectbox("選擇原始版本 (Baseline)", options=selected_names, index=0)
opt_strat = col2.selectbox("選擇優化版本 (Optimized)", options=selected_names, index=min(1, len(selected_names)-1))

if base_strat and opt_strat:
    # 這裡 calculate_metrics 已經適配 dict 輸入，直接傳入即可
    m1 = calculate_metrics(st.session_state.strategies[base_strat], base_strat)
    m2 = calculate_metrics(st.session_state.strategies[opt_strat], opt_strat)
    
    def show_delta(label, val1, val2, higher_is_better=True, is_pct=False):
        delta = val2 - val1; good = (delta > 0) if higher_is_better else (delta < 0)
        class_name = "delta-positive" if good else "delta-negative"
        fmt = "{:.2f}%" if is_pct else "{:,.2f}"; delta_str = (fmt.format(delta) if not is_pct else "{:+.2f}%".format(delta))
        return f"**{label}**: {fmt.format(val2)} ( <span class='{class_name}'>{delta_str}</span> )"
        
    with st.expander("優化成效分析報告", expanded=True):
        st.markdown(f"#### 自 {base_strat} 到 {opt_strat} 的變更摘要")
        c1, c2, c3 = st.columns(3)
        c1.markdown(show_delta("總淨利 ($)", m1["總淨利 ($)"], m2["總淨利 ($)"]), unsafe_allow_html=True)
        c1.markdown(show_delta("夏普比率", m1["夏普比率"], m2["夏普比率"]), unsafe_allow_html=True)
        c2.markdown(show_delta("勝率 (%)", m1["勝率 (%)"], m2["勝率 (%)"], is_pct=True), unsafe_allow_html=True)
        c2.markdown(show_delta("交易筆數", m1["交易筆數"], m2["交易筆數"], higher_is_better=False), unsafe_allow_html=True)
        c3.markdown(show_delta("MDD (%)", m1["最大回撤 (MDD %)"], m2["最大回撤 (MDD %)"], higher_is_better=False, is_pct=True), unsafe_allow_html=True)
        c3.markdown(show_delta("最大回撤 ($)", m1["最大回撤 ($)"], m2["最大回撤 ($)"], higher_is_better=False), unsafe_allow_html=True)
        
        fig_dd = go.Figure()
        for name in [base_strat, opt_strat]:
            # Fix: Access ['daily']
            strat_data = st.session_state.strategies[name]
            df = strat_data.get('daily')
            if df is not None and not df.empty and "ret_val" in df.columns:
                ret = df["ret_val"].dropna(); nav = (1 + ret).cumprod()
                dd = (nav / nav.cummax() - 1.0) * 100
                fig_dd.add_trace(go.Bar(x=ret.index, y=dd, name=f"{name} DD%"))
        fig_dd.update_layout(title="回撤幅度 (Drawdown %) 比較", barmode='overlay', yaxis_title="Drawdown %")
        st.plotly_chart(fig_dd, use_container_width=True)
        
        st.divider(); st.markdown("### 🤖 AI 智能優化點評")
        if st.button("🚀 生成 AI 分析報告"):
            try:
                from dotenv import load_dotenv
                load_dotenv(r"g:\我的雲端硬碟\Krystal_AI_Trading_System\api.env")
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key: st.error("未找到 OPENROUTER_API_KEY。")
                else:
                    with st.spinner("AI 正在分析數據並撰寫報告中..."):
                        prompt = f"你是專業量化交易導師。請對比：\n原始策略: {base_strat}\n- 淨利: {m1['總淨利 ($)']:.0f}, CAGR: {m1['年化報酬 (CAGR)']:.2f}%, MDD: {m1['最大回撤 (MDD %)']:.2f}%, 夏普: {m1['夏普比率']:.2f}\n優化策略: {opt_strat}\n- 淨利: {m2['總淨利 ($)']:.0f}, CAGR: {m2['年化報酬 (CAGR)']:.2f}%, MDD: {m2['最大回撤 (MDD %)']:.2f}%, 夏普: {m2['夏普比率']:.2f}\n請提供專業點評與具體建議（中文）。"
                        response = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            verify=False, timeout=30,
                            data=json.dumps({"model": "google/gemini-pro-1.5", "messages": [{"role": "user", "content": prompt}]})
                        )
                        
                        if response.status_code != 200:
                            st.error(f"API 請求失敗 (HTTP {response.status_code})：{response.text}")
                        else:
                            result = response.json()
                            if 'choices' in result and len(result['choices']) > 0:
                                ai_msg = result['choices'][0]['message']['content']
                                st.info("AI 分析建議如下：")
                                st.markdown(ai_msg)
                            else:
                                st.warning("API 回傳結構異常，未找到分析結果。")
                                st.json(result)
            except Exception as e:
                st.error(f"AI 分析過程序發生錯誤：{e}")

# ===================== Monthly Compare =====================
st.divider(); st.subheader("🗓️ 月度報酬對應比 (Monthly Correlation)")
if len(selected_names) >= 2:
    all_monthly = []
    for name in selected_names:
        # Fix: Access ['daily']
        strat_data = st.session_state.strategies[name]
        df = strat_data.get('daily')
        if df is not None and not df.empty and "ret_val" in df.columns:
            monthly = df.groupby([df.index.year, df.index.month])['ret_val'].apply(lambda x: (1 + x).prod() - 1)
            monthly.name = name; all_monthly.append(monthly)
    
    if all_monthly:
        m_df = pd.concat(all_monthly, axis=1).fillna(0)
        corr = m_df.corr()
        fig_corr = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, colorscale='RdBu', zmin=-1, zmax=1))
        fig_corr.update_layout(title="策略月度報酬相關性 (相關性越低越好，利於組合)")
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("無法生成月度對比：缺乏足夠的日報表數據。")
st.sidebar.divider()
st.sidebar.info(f"📍 當前頁面：`2_📊_多策略績效比較.py` \n💡 建議：將優化前與優化後的檔案放入資料夾，點擊「掃描」進行深度對比。")
