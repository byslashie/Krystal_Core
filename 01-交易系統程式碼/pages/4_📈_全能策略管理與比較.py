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
from modules.monte_carlo import run_monte_carlo

# 忽略 urllib3 的 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== Page Config =====================
st.set_page_config(layout="wide", page_title="全能策略管理與比較", page_icon="📈", initial_sidebar_state="expanded")

# 应用现代主题
apply_theme(st)

# ===================== Styles =====================
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d0d2d6;
        text-align: center;
    }
    .delta-positive { color: #28a745; font-weight: bold; }
    .delta-negative { color: #dc3545; font-weight: bold; }
    .obsidian-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 20px;
        border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
        border-left: 5px solid #7d4ccf;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 全能策略管理與比較 (Merged Strategy Hub)")

# ===================== Path Config =====================
STRATEGY_DIR = r"g:\我的雲端硬碟\Krystal_AI_Trading_System\data\strategies"
if not os.path.exists(STRATEGY_DIR):
    os.makedirs(STRATEGY_DIR)

import yfinance as yf

# ===================== Helper Functions (Engine) =====================

@st.cache_data(ttl=86400, show_spinner=False)
def load_benchmarks(start_date, end_date):
    import requests
    session = requests.Session()
    session.verify = False # 針對部分 Windows 環境 SSL 憑證問題
    
    symbols = ["SPY", "VOO", "006208.TW"]
    out = {}
    
    # 確保是 Timestamp
    s_ts = pd.to_datetime(start_date)
    e_ts = pd.to_datetime(end_date)
    
    for sym in symbols:
        try:
            # 增加緩衝區間，避免假日導致開頭為空
            buffer_start = s_ts - pd.Timedelta(days=7)
            buffer_end = e_ts + pd.Timedelta(days=3)
            
            raw = yf.download(sym, start=buffer_start, end=buffer_end, 
                              auto_adjust=True, progress=False, session=session, threads=False)
            
            if not raw.empty:
                # 處理 Single/MultiIndex 結構差異
                if isinstance(raw.columns, pd.MultiIndex):
                    close = raw["Close"].iloc[:, 0] if "Close" in raw.columns.levels[0] else raw.iloc[:, 0]
                else:
                    close = raw["Close"] if "Close" in raw.columns else raw.iloc[:, 0]
                
                close = close.dropna()
                if len(close) > 5:
                    # 使用 asof 尋找最接近且「小於等於」開始日期的點
                    # 若 start_date 是週日，asof 會找到週五的價
                    p0 = close.asof(s_ts)
                    if pd.isna(p0) or p0 == 0:
                        p0 = close.iloc[0]
                    
                    series = close / p0
                    # 篩選回正式區間
                    out[sym] = series[series.index >= s_ts]
        except Exception as e:
            continue
    return out

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

        # --- 新增：自動偵測初始資金 ---
        detected_cap = base_cap
        if "整體統計" in sheets:
            stats_df = sheets["整體統計"]
            # 尋找包含「初始資金」的欄位
            for row_idx in range(min(15, len(stats_df))):
                row_vals = [str(x) for x in stats_df.iloc[row_idx].values]
                content = "".join(row_vals)
                if "初始資金" in content:
                    for val in row_vals:
                        if "萬" in val:
                            try:
                                num = float(val.replace("萬", "").replace("元", "").strip())
                                detected_cap = int(num * 10000)
                                break
                            except: pass
                    break
        
        def find_cols_and_process(df_in, sheet_type="Daily", current_cap=1000000):
            df = df_in.copy()
            if len(df.columns) < 3 or df.columns[0].startswith("Unnamed"):
                best_df = df
                for i in range(15):
                    if i + 1 >= len(df_in): break
                    test_df = df_in.iloc[i+1:].reset_index(drop=True)
                    test_df.columns = df_in.iloc[i].values
                    if len(test_df.columns) > 3 and not str(test_df.columns[0]).startswith("Unnamed"):
                        best_df = test_df
                        break
                df = best_df

            date_cand = ["日期", "時間", "出場時間", "出場日期", "close time", "exit time", "date", "datetime", "平倉時間", "平倉日期"]
            pnl_cand = ["獲利金額", "總獲利", "pnl", "profit", "獲利", "損益", "淨損益", "平倉損益", "單筆損益", "Net Profit", "累計獲利金額"]
            ret_cand = ["報酬率", "return", "roi", "ret"]

            col_time = _find_first(df, date_cand)
            col_pnl = _find_first(df, pnl_cand)
            col_ret = _find_first(df, ret_cand)
            
            if not col_time or not col_pnl: return None
            
            df[col_time] = pd.to_datetime(df[col_time], errors="coerce")
            df = df.dropna(subset=[col_time]).sort_values(col_time).set_index(col_time)
            
            def clean_num(series):
                s = series.astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False).str.replace(' NTD', '', regex=False).str.strip()
                return pd.to_numeric(s, errors='coerce').fillna(0)

            raw_pnl = clean_num(df[col_pnl])
            
            is_cum = any(x in str(col_pnl) for x in ["總", "equity", "cum", "累計"])
            if not is_cum and len(df) > 20:
                is_mostly_monotonic = (raw_pnl.diff() >= 0).mean() > 0.85
                if is_mostly_monotonic and raw_pnl.abs().max() > current_cap * 0.1:
                    is_cum = True
            
            if is_cum:
                df["cum_pnl"] = raw_pnl
                df["pnl_val"] = raw_pnl.diff().fillna(raw_pnl.iloc[0])
            else:
                df["pnl_val"] = raw_pnl
                df["cum_pnl"] = raw_pnl.cumsum()
            
            prev_equity = current_cap + df["cum_pnl"].shift(1).fillna(0)
            df["ret_val"] = df["pnl_val"] / prev_equity.replace(0, current_cap)

            if col_ret:
                s_str = df[col_ret].astype(str).str.replace('%','',regex=False).str.replace(',','',regex=False).str.strip()
                s_val = pd.to_numeric(s_str, errors='coerce').fillna(0)
                if not s_val.empty:
                    q80 = s_val.abs().quantile(0.80)
                    if q80 > 1.5: s_val = s_val / 100.0
                    df["orig_ret"] = s_val
            return df

        df_daily = None
        df_trade = None
        target_daily_s = None
        target_trade_s = None
        
        # Search Daily
        for k in ["每日", "Daily", "報表", "Equity"]:
             for s in sheets:
                 if k in s: target_daily_s = s; break
             if target_daily_s: break
        if not target_daily_s and len(sheets) == 1: target_daily_s = list(sheets.keys())[0]
        if target_daily_s:
            df_daily = find_cols_and_process(sheets[target_daily_s], "Daily", detected_cap)

        # Search Trade
        for k in ["交易分析", "交易明細", "Trade Analysis", "Trade List", "交易分析", "明細"]:
             for s in sheets:
                 if k in s and s != target_daily_s: target_trade_s = s; break
             if target_trade_s: break
        if target_trade_s:
            df_trade = find_cols_and_process(sheets[target_trade_s], "Trade", detected_cap)
        
        if df_daily is None and df_trade is None: return None
        if df_daily is None: df_daily = df_trade.copy()
        if df_trade is None: df_trade = df_daily.copy()

        return {
            "daily": df_daily,
            "trade": df_trade,
            "source_daily": target_daily_s,
            "source_trade": target_trade_s if target_trade_s else f"{target_daily_s} (Daily Fallback)",
            "detected_cap": detected_cap
        }
    except Exception as e:
        st.error(f"解析 {name} 失敗: {e}")
        return None

def calculate_metrics(strat_data, name, base_cap=1000000):
    if not strat_data: return {}
    # --- 優先使用 Excel 偵測到的本金 ---
    effective_cap = strat_data.get("detected_cap", base_cap)
    
    df_d = strat_data['daily']
    df_t = strat_data['trade']
    
    # Core (Daily)
    pnl = df_d["pnl_val"]
    cum_p = df_d["cum_pnl"] if "cum_pnl" in df_d.columns else pnl.cumsum()
    ret = df_d["ret_val"].dropna()
    net_p = pnl.sum()
    
    # --- 正確的 MDD % 算法：基於動態權益 (Dynamic Equity) ---
    equity = effective_cap + cum_p
    # 2. 計算歷史最高權益 (Rolling Peak)
    peak = equity.cummax()
    # 3. 計算回撤金額 (DD Amount) = 當前權益 - 歷史最高點
    dd_a = equity - peak
    mdd_a = dd_a.min()
    # 4. 計算回撤百分比 (Drawdown %) = 回撤金額 / 歷史最高點
    dd_p = dd_a / peak
    mdd_p = dd_p.min()
    
    if not ret.empty and len(ret) > 1:
        # 這裡的 nav 用於 CAGR 與 曲線顯示：(當前權益 / 初始本金)
        nav = equity / base_cap
        
        days = (df_d.index[-1] - df_d.index[0]).days
        years = max(days / 365.25, 0.1)
        cagr = (nav.iloc[-1])**(1/years) - 1 if nav.iloc[-1] > 0 else -1
        
        # 夏普比率使用日報酬率計算
        sharpe = (ret.mean() * 252) / (ret.std() * np.sqrt(252) + 1e-12)
        sortino = (ret.mean() * 252) / (ret[ret < 0].std() * np.sqrt(252) + 1e-12)
        calmar = cagr / abs(mdd_p) if mdd_p != 0 else 0
        
        # Risk Metrics (Tail)
        q95 = ret.quantile(0.95)
        q05 = ret.quantile(0.05)
        var_95 = q05
        cvar_95 = ret[ret <= q05].mean()
        right_tail_sum = ret[ret >= q95].sum()
        left_tail_sum = ret[ret <= q05].sum()
        tail_ratio = abs(right_tail_sum / left_tail_sum) if left_tail_sum != 0 else np.nan
        skew = ret.skew()
        kurt = ret.kurtosis()
    else:
        cagr = mdd_p = sharpe = sortino = calmar = var_95 = cvar_95 = right_tail_sum = left_tail_sum = tail_ratio = skew = kurt = 0

    # Trade Info
    active_pnl = df_t["pnl_val"][df_t["pnl_val"] != 0]
    win_rate = (active_pnl > 0).mean() if not active_pnl.empty else 0
    wins = active_pnl[active_pnl > 0]
    losses = active_pnl[active_pnl < 0]
    avg_w = wins.mean() if not wins.empty else 0
    avg_l = abs(losses.mean()) if not losses.empty else 1e-9
    rr_ratio = avg_w / avg_l
    pf = wins.sum() / abs(losses.sum()) if not losses.empty else np.inf
    kelly = win_rate - (1 - win_rate) / rr_ratio if rr_ratio > 0 else 0
    
    # Obsidian specific metrics
    ev_pct = (ret.mean()) # Simplified EV % for Markdown
    avg_profit_pct = ret[ret > 0].mean() if not ret[ret > 0].empty else 0
    avg_loss_pct = ret[ret < 0].mean() if not ret[ret < 0].empty else 0

    return {
        "策略名稱": name, "總淨利 ($)": net_p, "年化報酬 (CAGR)": cagr * 100,
        "最大回撤 (MDD %)": mdd_p * 100, "最大回撤 ($)": mdd_a, "夏普比率": sharpe,
        "索提諾比率": sortino, "卡瑪比率": calmar, "獲利因子 (PF)": pf,
        "勝率 (%)": win_rate * 100, "風報比": rr_ratio, "期望值": win_rate * rr_ratio,
        "凱利準則 (%)": kelly * 100, "交易筆數": len(df_t), "資料來源": strat_data['source_trade'],
        "start_date": df_d.index[0], "end_date": df_d.index[-1],
        "VaR_95": var_95, "CVaR_95": cvar_95, "Skew": skew, "Kurtosis": kurt,
        "Right_Tail_Sum": right_tail_sum, "Left_Tail_Sum": left_tail_sum, "Tail_Ratio": tail_ratio,
        "avg_profit_pct": avg_profit_pct * 100, "avg_loss_pct": avg_loss_pct * 100, "ev_pct": ev_pct * 100,
        "max_capital": pnl.cumsum().max() # Placeholder for max invested
    }

# ===================== Sidebar =====================

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

st.sidebar.header("⚙️ 全域設定與檔案")
base_capital = st.sidebar.number_input("💰 假設初始資金 ($)", value=1000000, step=100000)
instrument_type = st.sidebar.selectbox("🧮 商品類型", ["海外個股(股)", "個股(台股)", "指數", "個股期貨"])
multiplier = {"海外個股(股)": 1, "個股(台股)": 1000, "指數": 50, "個股期貨": 2000}[instrument_type]

st.sidebar.divider()
uploaded_files = st.sidebar.file_uploader("📤 上傳策略檔案", accept_multiple_files=True, type=["csv", "xlsx", "xls"])
scan_folder = st.sidebar.button("🔄 掃描 data/strategies")
if st.sidebar.button("🗑️ 清除所有快取", type="primary"):
    st.session_state.merged_strats = {}
    st.experimental_rerun()

# --- Metadata Fields ---
st.sidebar.divider()
st.sidebar.subheader("📝 策略描述 (Obsidian 用)")
meta_name = st.sidebar.text_input("策略顯示名稱", "我的新策略")
meta_ver = st.sidebar.text_input("版本號", "v1.0")
meta_desc = st.sidebar.text_area("策略描述", "描述策略邏輯...")
meta_freq = st.sidebar.selectbox("執行頻率", ["日內", "波段", "長期"])
meta_opt = st.sidebar.text_input("優化方向", "風險控制")

st.sidebar.divider()
st.sidebar.subheader("🤖 OpenRouter 設定")
api_key = st.sidebar.text_input("🔑 API 金鑰", type="password")
ai_model = st.sidebar.selectbox("模型", ["google/gemini-2.0-flash-exp:free", "deepseek/deepseek-chat"])

if "merged_strats" not in st.session_state:
    st.session_state.merged_strats = {}

if scan_folder:
    st.session_state.merged_strats = {}
    for f in os.listdir(STRATEGY_DIR):
        if f.endswith((".csv", ".xlsx", ".xls")):
            res = process_strategy_df(os.path.join(STRATEGY_DIR, f), f, base_capital)
            if res: st.session_state.merged_strats[f] = res

if uploaded_files:
    for uf in uploaded_files:
        res = process_strategy_df(uf, uf.name, base_capital)
        if res: st.session_state.merged_strats[uf.name] = res

if not st.session_state.merged_strats:
    st.info("請上傳檔案或掃描資料夾。")
    st.stop()

# ===================== Main UI =====================
selected_names = st.multiselect("📊 選擇比較的策略", options=list(st.session_state.merged_strats.keys()), default=list(st.session_state.merged_strats.keys()))

if not selected_names:
    st.warning("請至少選中一個策略。")
    st.stop()

comparison_data = [calculate_metrics(st.session_state.merged_strats[n], n, base_capital) for n in selected_names]
comp_df = pd.DataFrame(comparison_data).set_index("策略名稱")

# ── 蒙地卡羅分布圖輔助函數 ──────────────────────────────────────────────────
def _make_mc_dist_chart(values: np.ndarray, initial_capital: float, title: str, is_drawdown: bool = False):
    """繪製橫向百分位分布帶狀圖（仿截圖樣式）"""
    p1  = float(np.percentile(values, 1))
    p5  = float(np.percentile(values, 5))
    p25 = float(np.percentile(values, 25))
    p50 = float(np.percentile(values, 50))
    p75 = float(np.percentile(values, 75))
    p95 = float(np.percentile(values, 95))
    p99 = float(np.percentile(values, 99))

    def wan(v): return f"{v / 10000:.1f}萬"

    fig = go.Figure()
    y0, y1 = 0.25, 0.75  # 色帶 y 範圍

    # 色帶：左差右好
    for x0, x1, color in [
        (p1,  p5,  "rgba(220,50,50,0.75)"),
        (p5,  p25, "rgba(250,170,130,0.55)"),
        (p25, p75, "rgba(170,225,165,0.60)"),
        (p75, p95, "rgba(70,190,90,0.60)"),
        (p95, p99, "rgba(30,140,55,0.50)"),
    ]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line_width=0, layer="below")

    # 外框
    fig.add_shape(type="rect", x0=p1, x1=p99, y0=y0, y1=y1,
                  fillcolor="rgba(0,0,0,0)", line=dict(color="rgba(0,0,0,0.15)", width=1))

    # 初始資金參考線（僅最終資產圖）
    if not is_drawdown:
        fig.add_shape(type="line", x0=initial_capital, x1=initial_capital,
                      y0=y0 - 0.08, y1=y1 + 0.08,
                      line=dict(color="rgba(50,80,210,0.65)", width=1.5, dash="dot"))

    # 關鍵分位標記
    for val, lbl, color in [
        (p5,  wan(p5),               "crimson"),
        (p50, f"{wan(p50)}（中位）", "#222222"),
        (p95, wan(p95),              "seagreen"),
    ]:
        fig.add_shape(type="line", x0=val, x1=val, y0=y0 - 0.06, y1=y1 + 0.06,
                      line=dict(color=color, width=2.5))
        fig.add_annotation(x=val, y=y1 + 0.22, text=lbl, showarrow=False,
                           font=dict(size=11, color=color), xanchor="center")

    # 邊緣標籤
    fig.add_annotation(x=p1,  y=y0 - 0.22, text=wan(p1),  showarrow=False,
                       font=dict(size=10, color="#999"), xanchor="left")
    fig.add_annotation(x=p99, y=y0 - 0.22, text=wan(p99), showarrow=False,
                       font=dict(size=10, color="#999"), xanchor="right")

    fig.update_layout(
        title=dict(text=title, font=dict(size=13), x=0),
        height=140,
        margin=dict(t=38, b=12, l=12, r=12),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[0, 1.15]),
        plot_bgcolor="rgba(255,255,255,0.04)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 多策略績效比較", "📈 淨值與回撤曲線", "📉 報酬風險分布", "🔬 單策略深度診斷", "📝 Obsidian 報告匯出", "🎲 蒙地卡羅模擬"])

# --- Tab 1: Comparison (Same as before) ---
with tab1:
    st.subheader("📋 績效指標對照表")
    st.dataframe(comp_df.style.format({
        "總淨利 ($)": "{:,.0f}", "年化報酬 (CAGR)": "{:.2f}%", "最大回撤 (MDD %)": "{:.2f}%",
        "最大回撤 ($)": "{:,.0f}", "勝率 (%)": "{:.2f}%", "風報比": "{:.2f}",
        "期望值": "{:.2f}", "凱利準則 (%)": "{:.2f}%", "交易筆數": "{:,.0f}", "資料來源": "{}"
    }), use_container_width=True)

    st.divider()
    st.subheader("🏆 策略綜合評等 (滿分 1.00)")
    
    with st.expander("💡 了解評分算法與 MDD 邏輯"):
        st.markdown("""
        ### **1. 綜合評分算法 (Scoring Logic)**
        系統根據以下權重對策略進行標準化評分：
        *   **夏普比率 (Sharpe Ratio) - 40%**: 衡量每單位風險帶來的超額報酬（獲利平滑度）。
        *   **卡瑪比率 (Calmar Ratio) - 40%**: 年化報酬與最大回撤的比值（獲利對比風險的效率）。
        *   **勝率 (Win Rate) - 20%**: 策略執行時的心理舒適度與穩定度。
        
        ### **2. 修正後 MDD 計算 (Updated MDD %)**
        採用**動態權益 (Rolling Peak Equity)** 算法：
        *   **分母**：不再固定為初始資金，而是使用 **「當時的歷史最高總價值 (Peak)」**。
        *   **優點**：即使獲利翻倍，也能真實反映資產淨值的波動風險，不會因資金長大而失真。
        """)

    def get_score(row):
        s_norm = row['夏普比率'] / (comp_df['夏普比率'].max() + 1e-9)
        m_norm = row['卡瑪比率'] / (comp_df['卡瑪比率'].max() + 1e-9)
        w_norm = row['勝率 (%)'] / (comp_df['勝率 (%)'].max() + 1e-9)
        return (s_norm * 0.4 + m_norm * 0.4 + w_norm * 0.2)
    
    scored_df = comp_df.copy()
    scored_df['綜合得分'] = scored_df.apply(get_score, axis=1)
    best_name = scored_df['綜合得分'].idxmax()
    best_row = scored_df.loc[best_name]

    c1, c2 = st.columns([1, 3])
    with c1:
        st.success(f"**最高推薦：{best_name}**")
        st.metric("綜合評分", f"{best_row['綜合得分']:.2f}", help="滿分為 1.00，代表在當前組合中綜合素質最高")
    with c2:
        rr, wr = best_row['風報比'], best_row['勝率 (%)']
        if rr > 5 and wr > 60: style = "🦄 聖杯級策略 (Holy Grail)"; tip = f"風報比 {rr:.1f} 極為罕見，具備強大的印鈔特性。"
        elif rr > 2.5: style = "🚀 趨勢爆發型"; tip = f"風報比 {rr:.1f} 優異，即便勝率稍低也能獲利。"
        elif wr > 60: style = "🛡️ 高勝率穩健型"; tip = f"依靠 {wr:.0f}% 的穩定勝率獲取穩定正期望回報。"
        else: style = "⚙️ 全能平衡型"; tip = "勝率與風報比均在水準之上。"
        st.write(f"**策略風格分析：** {style}")
        st.info(f"💡 **交易室筆記：** {tip}")

# --- Tab 2: Curves ---
with tab2:
    st.subheader("📈 淨值與回撤視覺化")
    fig_nav = go.Figure(); fig_dd = go.Figure()
    for n in selected_names:
        strat_obj = st.session_state.merged_strats[n]
        df = strat_obj['daily']
        eff_cap = strat_obj.get("detected_cap", base_capital)
        
        # 採用相同的保留累計邏輯，確保淨值與回撤繪圖正確
        pnl_daily = df["pnl_val"]
        cum_p = df["cum_pnl"] if "cum_pnl" in df.columns else pnl_daily.cumsum()
        
        equity = eff_cap + cum_p
        peak = equity.cummax()
        # 回撤百分比：(當前 / 當時最高) - 1
        dd_p_series = (equity / peak - 1.0) * 100
        nav_series = equity / eff_cap
        
        fig_nav.add_trace(go.Scatter(x=df.index, y=nav_series, name=n))
        fig_dd.add_trace(go.Scatter(x=df.index, y=dd_p_series, name=f"{n} DD%", fill='tozeroy'))
    fig_nav.update_layout(title="淨值曲線 (NAV)", hovermode="x unified"); fig_dd.update_layout(title="回撤曲線 (Drawdown %)", hovermode="x unified")
    st.plotly_chart(fig_nav, use_container_width=True); st.plotly_chart(fig_dd, use_container_width=True)

# --- Tab 3: Risk Distribution ---
with tab3:
    st.subheader("📉 報酬風險分布 (Reward-Risk Distribution)")
    dist_target = st.selectbox("🎯 選擇分析對象", selected_names, key="dist_sel")
    m = calculate_metrics(st.session_state.merged_strats[dist_target], dist_target, base_capital)
    ret = st.session_state.merged_strats[dist_target]['daily']['ret_val'].dropna() * 100
    
    import plotly.express as px
    fig_dist = px.histogram(ret, nbins=50, title=f"{dist_target} 報酬分布圖", labels={'value': '報酬率 (%)'}, color_discrete_sequence=['#7d4ccf'])
    st.plotly_chart(fig_dist, use_container_width=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("VaR (95%)", f"{m['VaR_95']*100:.2f}%")
    c1.metric("CVaR (95%)", f"{m['CVaR_95']*100:.2f}%")
    c2.metric("偏態 (Skew)", f"{m['Skew']:.2f}")
    c2.metric("峰度 (Kurtosis)", f"{m['Kurtosis']:.2f}")
    c3.metric("Tail Ratio", f"{m['Tail_Ratio']:.2f}")
    
    st.info(f"**尾部摘要：** 右尾 (最佳 5%) 總貢獻為 {m['Right_Tail_Sum']*100:.1f}%, 左尾 (最差 5%) 總損失為 {m['Left_Tail_Sum']*100:.1f}%。")

# --- Tab 4: Advanced Single Diagnostic ---
with tab4:
    ai_target = st.selectbox("🤖 選擇深度診斷策略", selected_names, key="ai_sel")
    strat_obj = st.session_state.merged_strats[ai_target]
    df_d = strat_obj['daily']
    df_t = strat_obj['trade']
    m = calculate_metrics(strat_obj, ai_target, base_capital)
    
    st.subheader("🗓️ 週期性報酬分析 (Periodic Returns)")
    # 計算年月季報酬
    def get_periodic_stats(df):
        ret = df['ret_val'].dropna()
        y = ret.groupby(ret.index.year).apply(lambda x: (1+x).prod()-1) * 100
        q = ret.groupby([ret.index.year, ret.index.quarter]).apply(lambda x: (1+x).prod()-1) * 100
        m = ret.groupby([ret.index.year, ret.index.month]).apply(lambda x: (1+x).prod()-1) * 100
        return y, q, m
    
    y_ret, q_ret, m_ret = get_periodic_stats(df_d)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**年度報酬表 (%)**")
        st.dataframe(y_ret.to_frame("Return %").style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)
    with c2:
        st.write("**季報酬分布 (%)**")
        q_df = q_ret.unstack()
        st.dataframe(q_df.style.format("{:.2f}").background_gradient(cmap="RdYlGn"), use_container_width=True)

    st.write("**月度報酬熱圖 (Monthly Heatmap %)**")
    import seaborn as sns
    import matplotlib.pyplot as plt
    m_df = m_ret.unstack()
    fig_heat, ax_heat = plt.subplots(figsize=(10, len(m_df)*0.5 + 2))
    sns.heatmap(m_df, annot=True, fmt=".1f", cmap="RdYlGn", center=0, ax=ax_heat)
    st.pyplot(fig_heat)

    st.divider()
    st.subheader("🌊 季節性規律分析 (Seasonality)")
    c3, c4 = st.columns(2)
    with c3:
        avg_m = m_ret.groupby(level=1).mean()
        fig_m = go.Figure(go.Bar(x=avg_m.index, y=avg_m, marker_color='#7d4ccf'))
        fig_m.update_layout(title="平均月度報酬 (月季節性)", xaxis_title="月份", yaxis_title="報酬平均 %")
        st.plotly_chart(fig_m, use_container_width=True)
    with c4:
        # 週季節性勝率
        df_d['weekday'] = df_d.index.dayofweek
        w_stats = df_d.groupby('weekday')['ret_val'].agg(['mean', lambda x: (x > 0).mean() * 100])
        w_stats.columns = ['Avg Ret %', 'Win Rate %']
        fig_w = go.Figure()
        fig_w.add_trace(go.Bar(x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][:len(w_stats)], y=w_stats['Avg Ret %']*100, name='平均報酬 %', marker_color='#4caf50'))
        fig_w.add_trace(go.Scatter(x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][:len(w_stats)], y=w_stats['Win Rate %'], name='勝率 %', yaxis='y2', line=dict(color='orange')))
        fig_w.update_layout(title="星期規律 (Win Rate & Return)", yaxis_title="報酬 %", yaxis2=dict(title="勝率 %", overlaying='y', side='right'))
        st.plotly_chart(fig_w, use_container_width=True)

    st.divider()
    st.subheader("🕒 持倉與行為分析 (Holding Analysis)")
    if not df_t.empty:
        # 計算持倉時長
        in_time = _find_first(df_t, ["進場時間","進場日期","entry"])
        out_time = _find_first(df_t, ["出場時間","出場日期","exit"])
        if in_time and out_time:
            df_t['duration'] = (pd.to_datetime(df_t[out_time]) - pd.to_datetime(df_t[in_time])).dt.total_seconds() / 3600 # 換算小時
            fig_dur = px.scatter(df_t, x='duration', y='pnl_val', color='pnl_val', color_continuous_scale='RdYlGn', 
                                 title="持倉時間 vs. 損益分佈", labels={'duration': '小時 (h)', 'pnl_val': '損益 ($)'})
            st.plotly_chart(fig_dur, use_container_width=True)

    st.divider()
    st.subheader("📦 個股/標的維度深度分析")
    # 嘗試尋找 Symbol 欄位
    sym_col = _find_first(df_t, ["代碼", "商品", "Symbol", "ticker", "合約", "標的"])
    if sym_col and not df_t.empty:
        # 計算每個標的的各項指標
        def calc_symbol_stats(group):
            cum_pnl = group['pnl_val'].cumsum()
            peaks = cum_pnl.cummax()
            # 避免除以 0, 若全部獲利則 MDD 為 0
            mdd_val = (cum_pnl - peaks).min()
            win_rate = (group['pnl_val'] > 0).mean()
            avg_ret = group['ret_val'].mean() * 100
            total_pnl = group['pnl_val'].sum()
            return pd.Series({
                'Total PnL': total_pnl,
                'Max Drawdown': mdd_val,
                'Win Rate': win_rate,
                'Avg Return %': avg_ret
            })
        
        sym_perf = df_t.groupby(sym_col).apply(calc_symbol_stats)
        
        row1_c1, row1_c2 = st.columns(2)
        with row1_c1:
            # 1. Top 10 Profitable Symbols
            top_profit = sym_perf.sort_values("Total PnL", ascending=False).head(10).sort_values("Total PnL")
            fig1 = go.Figure(go.Bar(x=top_profit['Total PnL'], y=top_profit.index, orientation='h', marker_color='green'))
            fig1.update_layout(title="Top 10 Profitable Symbols (Contribution)", xaxis_title="Total Return Sum", margin=dict(l=100))
            st.plotly_chart(fig1, use_container_width=True)
            
        with row1_c2:
            # 2. Top 10 Highest Risk Symbols (MDD)
            top_risk = sym_perf.sort_values("Max Drawdown", ascending=True).head(10).sort_values("Max Drawdown", ascending=False)
            fig2 = go.Figure(go.Bar(x=top_risk['Max Drawdown'], y=top_risk.index, orientation='h', marker_color='red'))
            fig2.update_layout(title="Top 10 Highest Risk Symbols (Max Drawdown $)", xaxis_title="Max Drawdown Amount", margin=dict(l=100))
            st.plotly_chart(fig2, use_container_width=True)
            
        row2_c1, row2_c2 = st.columns(2)
        with row2_c1:
            # 3. Win Rate vs Average Return
            fig3 = go.Figure(go.Scatter(x=sym_perf['Win Rate'], y=sym_perf['Avg Return %'], mode='markers', 
                                         marker=dict(size=10, opacity=0.7, color='#3176f7'),
                                         text=sym_perf.index))
            fig3.update_layout(title="Win Rate vs Average Return %", xaxis_title="Win Rate", yaxis_title="Avg Return %")
            fig3.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig3, use_container_width=True)
            
        with row2_c2:
            # 4. Distribution of Average Returns
            fig4 = px.histogram(sym_perf, x="Avg Return %", nbins=30, title="Distribution of Average Returns %",
                                color_discrete_sequence=['blue'], opacity=0.7)
            fig4.update_layout(xaxis_title="Avg Return %", yaxis_title="Frequency")
            st.plotly_chart(fig4, use_container_width=True)
            
    else:
        st.info("交易明細中未偵測到標的名稱，無法進行標的維度分析。")

    st.divider()
    st.subheader("🤖 AI 策略改良建議")
    if st.button("🚀 取得 AI 深度點評計畫"):
        if not api_key: st.warning("請設定側邊欄 API Key")
        else:
             with st.spinner("AI 偵測中..."):
                periodic_data = f"年度: {y_ret.to_dict()}, 月度均值: {avg_m.to_dict()}"
                prompt = f"分析策略: {ai_target}\n指標: {json.dumps(m, ensure_ascii=False)}\n週期數據: {periodic_data}\n請依據季節性規律給予專業意見。"
                try:
                    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {api_key}"}, 
                                     data=json.dumps({"model": ai_model, "messages": [{"role":"user","content":prompt}]}), verify=False)
                    st.markdown(r.json()['choices'][0]['message']['content'])
                except: st.error("請求超時")

# --- Tab 5: Obsidian Export ---
with tab5:
    st.subheader("📝 Obsidian Markdown 報告匯出")
    exp_target = st.selectbox("📂 選擇匯出對象", selected_names, key="exp_sel_final")
    m = calculate_metrics(st.session_state.merged_strats[exp_target], exp_target, base_capital)
    
    # 讀取當次繪圖的 MDD 曲線 (內部計算)
    # Benchmark Comparison logic
    bench_data = load_benchmarks(m['start_date'], m['end_date'])
    
    def get_bench_metrics(symbol, series):
        if series.empty: return {}
        days = (series.index[-1] - series.index[0]).days
        yrs = max(days/365.25, 0.1)
        cagr = (series.iloc[-1]/series.iloc[0])**(1/yrs) - 1
        dd = series / series.cummax() - 1; mdd = dd.min()
        sharpe = (series.pct_change().mean() * 252) / (series.pct_change().std() * np.sqrt(252) + 1e-12)
        return {"cagr": cagr, "mdd": mdd, "sharpe": sharpe, "calmar": cagr/abs(mdd) if mdd != 0 else 0}

    bench_rows = ""
    win_summary = []
    
    for sym in ["SPY", "VOO", "006208.TW"]:
        if sym in bench_data:
            bm = get_bench_metrics(sym, bench_data[sym])
            diff_cagr = (m['年化報酬 (CAGR)']/100 - bm['cagr']) * 100
            diff_calmar = (m['卡瑪比率'] - bm['calmar'])
            diff_mdd = (m['最大回撤 (MDD %)']/100 - bm['mdd']) * 100
            diff_sharpe = (m['夏普比率'] - bm['sharpe'])
            
            bench_rows += f"| {sym} | {m['年化報酬 (CAGR)']:.2f}% | {bm['cagr']*100:.2f}% | {diff_cagr:+.2f}ppt | {m['卡瑪比率']:.2f} | {bm['calmar']:.2f} | {diff_calmar:+.2f} | {m['最大回撤 (MDD %)']:.1f}% | {bm['mdd']*100:.1f}% | {diff_mdd:+.2f}ppt | {m['夏普比率']:.2f} | {bm['sharpe']:.2f} | {diff_sharpe:+.2f} |\n"
            
            # Winner Flags
            c_v = "✅" if (m['年化報酬 (CAGR)']/100 > bm['cagr']) else "❌"
            m_v = "✅" if (m['卡瑪比率'] > bm['calmar']) else "❌"
            win_summary.append(f"  * {sym}：{c_v} CAGR、{m_v} Calmar")
        else:
            win_summary.append(f"  * {sym}：⚠️ 無法取得資料")

    win_summary_str = "\n".join(win_summary)
    bench_rows_display = bench_rows if bench_rows else "| (無數據) | - | - | - | - | - | - | - | - | - | - | - | - |"

    md_content = f"""---
title: "{exp_target} Backtest - {meta_ver}"
type: backtest
module: "{meta_name}"
version: "{meta_ver}"
tags: [backtest, {meta_freq}]
run_date: {datetime.now().strftime("%Y-%m-%d")}
start_date: {m['start_date'].strftime("%Y-%m-%d")}
end_date: {m['end_date'].strftime("%Y-%m-%d")}
kelly_full: {m['凱利準則 (%)']/100:.4f}
凱利公式_Kelly: {m['凱利準則 (%)']/100:.4f}
cagr: {m['年化報酬 (CAGR)'] / 100:.4f}
年化報酬率_CAGR: {m['年化報酬 (CAGR)'] / 100:.4f}
sharpe: {m['夏普比率']:.2f}
夏普比率_Sharpe: {m['夏普比率']:.2f}
sortino: {m['索提諾比率']:.2f}
索提諾比率_Sortino: {m['索提諾比率']:.2f}
mdd: {m['最大回撤 (MDD %)'] / 100:.4f}
最大回撤_MDD: {m['最大回撤 (MDD %)'] / 100:.4f}
calmar: {m['卡瑪比率']:.2f}
卡瑪比率_Calmar: {m['卡瑪比率']:.2f}
win_rate: {m['勝率 (%)'] / 100:.4f}
勝率_WinRate: {m['勝率 (%)'] / 100:.4f}
trades: {m['交易筆數']}
交易數量_Trades: {m['交易筆數']}
net_profit: {m['總淨利 ($)']}
淨利_$: {m['總淨利 ($)']}
avg_profit_pct: {m['avg_profit_pct']:.2f}
平均獲利_%: {m['avg_profit_pct']:.2f}
avg_loss_pct: {m['avg_loss_pct']:.2f}
平均損失_%: {m['avg_loss_pct']:.2f}
ev_pct: {m['ev_pct']:.2f}
期望值EV_%: {m['ev_pct']:.2f}
cagr_pct: {m['年化報酬 (CAGR)']:.2f}
年化報酬率_CAGR%: {m['年化報酬 (CAGR)']:.2f}
mdd_pct: {m['最大回撤 (MDD %)']:.2f}
最大回撤_MDD%: {m['最大回撤 (MDD %)']:.2f}
win_rate_pct: {m['勝率 (%)']:.2f}
勝率_WinRate%: {m['勝率 (%)']:.2f}
---

# 📊 Summary
* 區間：{m['start_date'].strftime("%Y-%m-%d")} → {m['end_date'].strftime("%Y-%m-%d")}（回測於 {datetime.now().strftime("%Y-%m-%d")}）
* 成果：CAGR **{m['年化報酬 (CAGR)']:.2f}%**
* Sharpe **{m['夏普比率']:.2f}**，MDD **{m['最大回撤 (MDD %)']:.1f}%**，Calmar **{m['卡瑪比率']:.2f}**，勝率 **{m['勝率 (%)']:.0f}%**，交易數 **{m['交易筆數']}**
* 是否贏過基準（CAGR / Calmar）
{win_summary_str}

## 📊 與基準數值對照表（同期間）
| 基準 | CAGR_S | CAGR_B | ΔCAGR(ppt) | Calmar_S | Calmar_B | ΔCalmar | MDD_S | MDD_B | ΔMDD(ppt) | Sharpe_S | Sharpe_B | ΔSharpe |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{bench_rows_display}

## ⚙️ 核心品質指標
* 品質：勝率 **{m['勝率 (%)']:.1f}%**，交易數 **{m['交易筆數']}**
* 淨利 ($)：**${m['總淨利 ($)']:,.0f}**
* 最大投入金額 ($)：**${m['max_capital']:,.0f}**
* 賺賠比：**{m['風報比']:.2f}**
* 期望值 EV (%)：**{m['ev_pct']:.2f}%**
* 平均每筆報酬 (%)：**{m['ev_pct']:.2f}%**
* 平均獲利 (%)：**{m['avg_profit_pct']:.2f}%**
* 平均損失 (%)：**{m['avg_loss_pct']:.2f}%**

### 平均獲利與虧損
| 指標 | 數值 |
| --- | --- |
| 平均獲利 | ${m['總淨利 ($)']/m['交易筆數'] * m['勝率 (%)']/100:,.0f} |
| 平均虧損 | ${m['總淨利 ($)']/m['交易筆數'] * (1-m['勝率 (%)']/100):,.0f} |

## 📑 風險統計與尾部摘要
| 指標 | 參數 | 數值 | 解讀 |
| --- | --- | --- | --- |
| VaR | 95% | {m['VaR_95']*100:.2f}% | 在 95% 置信水準下的最大可能單期損失。 |
| CVaR | 95% | {m['CVaR_95']*100:.2f}% | 超過 VaR 的最壞情況下，平均損失。 |
| 右尾 Σ | 95% | {m['Right_Tail_Sum']*100:.2f}% | 最佳 5% 的極端大賺事件總貢獻。 |
| 左尾 Σ | 5% | {m['Left_Tail_Sum']*100:.2f}% | 最差 5% 的極端大虧事件總損失。 |
| Tail Ratio | | {m['Tail_Ratio']:.2f} | 正尾總貢獻對比負尾比例。 |
| 偏態 Skew | | {m['Skew']:.2f} | 數值 > 0 代表正向極端值較多。 |
| 超峰度 | | {m['Kurtosis']:.2f} | 越高代表極端事件（黑天鵝）機率越高。 |

## 📊 報酬分布圖
(請從 Web 介面擷取 Tab 3 的分布圖插入此處)

---
Generated by Krystal AI Trading System 🚀
"""
    st.markdown("### 📄 報告預覽")
    st.markdown(f'<div class="obsidian-box"><pre style="white-space: pre-wrap;">{md_content}</pre></div>', unsafe_allow_html=True)
    st.download_button("💾 下載 Obsidian 報告 (.md)", md_content, file_name=f"{exp_target}_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")


# --- Tab 6: Monte Carlo Simulation ---
with tab6:
    st.subheader("🎲 蒙地卡羅模擬 — 策略可靠度分析")
    st.caption(f"各策略歷史交易打亂重組，模擬 50,000 條不同路徑（回測期相同單數）")

    mc_strategy_names = selected_names + (["合體比較"] if len(selected_names) > 1 else [])
    mc_inner_tabs = st.tabs(mc_strategy_names)

    # 計算並快取各策略 MC 結果
    mc_results: dict = {}
    for sname in selected_names:
        cache_key = f"_mc_{sname}_{base_capital}"
        if cache_key not in st.session_state:
            strat_obj = st.session_state.merged_strats[sname]
            eff_cap = strat_obj.get("detected_cap", base_capital)
            trade_pnls = strat_obj["trade"]["pnl_val"].values
            with st.spinner(f"模擬 {sname}（50,000 條路徑）..."):
                st.session_state[cache_key] = run_monte_carlo(trade_pnls, eff_cap)
        mc_results[sname] = st.session_state[f"_mc_{sname}_{base_capital}"]

    def _render_mc_single(sname: str):
        """渲染單一策略的 MC 結果面板"""
        result = mc_results.get(sname)
        strat_obj = st.session_state.merged_strats[sname]
        eff_cap = strat_obj.get("detected_cap", base_capital)

        if result is None:
            st.warning(f"⚠️ {sname} 交易筆數不足（< 5），無法模擬。")
            return

        # ── 六格指標卡 ────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        c1.metric("最終資產中位數",   f"{result['final_median'] / 10000:.0f}萬")
        c2.metric("最差5%情境",      f"{result['final_p5'] / 10000:.0f}萬")
        c3.metric("最好5%情境",      f"{result['final_p95'] / 10000:.0f}萬")

        c4, c5, c6 = st.columns(3)
        c4.metric("中位數最大回撤",   f"{result['mdd_median'] / 10000:.1f}萬")
        c5.metric("最差5%最大回撤",  f"{result['mdd_p5'] / 10000:.1f}萬")
        ruin = result["ruin_prob"]
        c6.metric("虧損機率",        f"{ruin:.1f}%")

        # ── 分布圖 ────────────────────────────────────────────────────
        st.plotly_chart(
            _make_mc_dist_chart(
                result["final_assets"], eff_cap,
                f"最終資產分布（初始 {int(eff_cap / 10000)}萬）"
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            _make_mc_dist_chart(
                result["max_drawdowns"], eff_cap,
                "最大回撤分布（負值愈小愈好）",
                is_drawdown=True,
            ),
            use_container_width=True,
        )

        # ── 洞察文字框 ────────────────────────────────────────────────
        m = calculate_metrics(strat_obj, sname, base_capital)
        actual_mdd   = m["最大回撤 ($)"]          # 負值
        median_mdd   = result["mdd_median"]        # 負值
        worst5_mdd   = result["mdd_p5"]            # 負值（最差）
        pct_vs_actual = abs(worst5_mdd / actual_mdd - 1) * 100 if actual_mdd != 0 else 0
        order_bias    = "偏不利" if actual_mdd < median_mdd else "偏有利"
        expect_note   = "沒那麼嚴重" if actual_mdd < median_mdd else "可能更嚴重"
        pct_positive  = 100 - ruin

        insights = [
            (f"回測回撤 {actual_mdd / 10000:.1f}萬，比模擬中位數 {median_mdd / 10000:.1f}萬 "
             f"{'略大' if actual_mdd < median_mdd else '略小'} — "
             f"表示回測遇到的順序{order_bias}，實際期望回撤可能{expect_note}"),
            (f"但最差5%情境下回撤可達 {worst5_mdd / 10000:.1f}萬，"
             f"比回測數字大約 {pct_vs_actual:.0f}%，需預留此空間"),
            (f"{result['n_simulations']:,}次模擬中，最終資產 {pct_positive:.0f}% 高於初始"
             f"{int(eff_cap / 10000)}萬，策略正期望值{'穩固' if ruin < 5 else '需關注'}"),
        ]
        for text in insights:
            st.markdown(
                f'<div style="border-left:4px solid #2ecc71;padding:9px 14px;margin:5px 0;'
                f'background:rgba(46,204,113,0.06);border-radius:0 6px 6px 0;font-size:14px;">'
                f'{text}</div>',
                unsafe_allow_html=True,
            )

    def _render_mc_combined():
        """合體比較：各策略 MC 關鍵指標並排"""
        rows = []
        for sname in selected_names:
            r = mc_results.get(sname)
            if r is None:
                continue
            eff_cap = st.session_state.merged_strats[sname].get("detected_cap", base_capital)
            rows.append({
                "策略": sname,
                "最終資產中位數(萬)": round(r["final_median"] / 10000, 1),
                "最差5%情境(萬)":    round(r["final_p5"] / 10000, 1),
                "最好5%情境(萬)":    round(r["final_p95"] / 10000, 1),
                "MDD中位數(萬)":     round(r["mdd_median"] / 10000, 1),
                "MDD最差5%(萬)":     round(r["mdd_p5"] / 10000, 1),
                "虧損機率(%)":       round(r["ruin_prob"], 2),
                "初始資金(萬)":      int(eff_cap / 10000),
            })
        if not rows:
            st.info("尚無可用結果。")
            return

        cmp_df = pd.DataFrame(rows).set_index("策略")
        st.dataframe(cmp_df, use_container_width=True)

        # 最終資產中位數 vs 最差5% 比較圖
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(name="最終資產中位數(萬)", x=cmp_df.index,
                                  y=cmp_df["最終資產中位數(萬)"], marker_color="#5B47D9"))
        fig_cmp.add_trace(go.Bar(name="最差5%情境(萬)",     x=cmp_df.index,
                                  y=cmp_df["最差5%情境(萬)"],     marker_color="#e74c3c"))
        fig_cmp.add_trace(go.Bar(name="最好5%情境(萬)",     x=cmp_df.index,
                                  y=cmp_df["最好5%情境(萬)"],     marker_color="#2ecc71"))
        fig_cmp.update_layout(barmode="group", title="各策略最終資產分布比較",
                               yaxis_title="資產(萬)", height=380)
        st.plotly_chart(fig_cmp, use_container_width=True)

        fig_mdd_cmp = go.Figure()
        fig_mdd_cmp.add_trace(go.Bar(name="MDD中位數(萬)",  x=cmp_df.index,
                                      y=cmp_df["MDD中位數(萬)"],  marker_color="#f39c12"))
        fig_mdd_cmp.add_trace(go.Bar(name="MDD最差5%(萬)",  x=cmp_df.index,
                                      y=cmp_df["MDD最差5%(萬)"],  marker_color="#c0392b"))
        fig_mdd_cmp.update_layout(barmode="group", title="各策略最大回撤分布比較",
                                   yaxis_title="回撤(萬，負值)", height=320)
        st.plotly_chart(fig_mdd_cmp, use_container_width=True)

    # 渲染各 inner tab
    for i, tab_name in enumerate(mc_strategy_names):
        with mc_inner_tabs[i]:
            if tab_name == "合體比較":
                _render_mc_combined()
            else:
                _render_mc_single(tab_name)

st.sidebar.divider()
st.sidebar.info(f"📍 當前頁面：`3_📈_全能策略管理與比較.py` \n💡 已整合 Page 1 & 2 的核心功能。")
