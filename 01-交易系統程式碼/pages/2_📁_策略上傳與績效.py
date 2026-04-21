import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import StringIO
import numpy_financial as npf
import yfinance as yf
import sys
from pathlib import Path

# 导入UI主题
sys.path.append(str(Path(__file__).parent.parent))
from utils.ui_theme import apply_theme

# ===================== Page & Matplotlib Defaults =====================
st.set_page_config(layout="wide", page_title="Strategy Performance Dashboard", page_icon="📈", initial_sidebar_state="expanded")
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'PingFang TC', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# 应用现代主题
apply_theme(st)

# ===================== Title =====================
st.markdown("""
<h1 style="
    color: #5B47D9;
    font-size: 36px;
    font-weight: 700;
">📈 策略上傳與績效分析</h1>
""", unsafe_allow_html=True)

# ===================== Safe Globals / Flags =====================
HAS_SHEETS = bool(globals().get("HAS_SHEETS", False))
SHEET_NAME = globals().get("SHEET_NAME", "Krystal 策略紀錄")
SHEET_TAB  = globals().get("SHEET_TAB",  "回測績效寫入")
CREDENTIAL_PATH = globals().get("CREDENTIAL_PATH", "strategy-performance.json")

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

st.sidebar.subheader("🧮 商品乘數設定")
instrument_type = st.sidebar.selectbox(
    "請選擇商品類型", ["海外個股(股)", "個股(台股)", "指數", "個股期貨"]
)
instrument_multiplier = {"海外個股(股)": 1, "個股(台股)": 1000, "指數": 50, "個股期貨": 2000}[instrument_type]

strategy_name = st.text_input("策略名稱", value=globals().get("strategy_name","目前回測策略"))
version = st.text_input("版本號", value=globals().get("version","v1.0"))
strategy_desc = st.text_area("策略描述", value=globals().get("strategy_desc","範例策略描述"))
execution_freq = st.selectbox("執行頻率", ["日內", "波段", "長期"])
optimize_focus = st.text_input("優化方向", value="停損設計、風險控制")
upload_time = datetime.now().strftime("%Y-%m-%d %H:%M")

# ---- OpenRouter (optional) ----
st.sidebar.title("🤖 OpenRouter AI 策略建議")
try:
    from openai import OpenAI
    HAS_OPENROUTER = True
except Exception:
    HAS_OPENROUTER = False
api_key = st.sidebar.text_input("🔑 請輸入 OpenRouter API 金鑰", type="password")
selected_model = st.sidebar.selectbox(
    "選擇模型",
    [
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-chat-v3-0324:free",
        "meta-llama/llama-4-maverick:free",
        "qwen/qwen3-235b-a22b:free",
        "microsoft/mai-ds-r1:free",
    ],
)

# ===================== File Upload =====================
uploaded_file = st.file_uploader("📄 請上傳策略績效 CSV 檔案", type=["csv"])

# ===================== Precompute metrics once after upload =====================
_df = None
if uploaded_file is not None:
    # ---- 1) decode CSV ----
    try:
        buf = StringIO(uploaded_file.getvalue().decode("cp950"))
    except UnicodeDecodeError:
        buf = StringIO(uploaded_file.getvalue().decode("utf-8"))
    raw_df = pd.read_csv(buf)

    # ---- 2) helpers (★ 這個就是缺的那顆) ----
    def _norm_col(s):
        if s is None:
            return ""
        s = str(s).strip().lower()
        # 中英符號與空白壓平
        for a, b in {
            "（": "(", "）": ")", "　": " ", "_": "", "-": "", "/": "", "\\": ""
        }.items():
            s = s.replace(a, b)
        s = s.replace(" ", "")
        return s

    def _find_first(df: pd.DataFrame, candidates) -> str | None:
        """
        先做「正規化完全相等」比對；找不到再用「包含/被包含」的寬鬆比對。
        """
        cand_list = list(candidates) if isinstance(candidates, (list, tuple)) else [candidates]
        norm_map = {_norm_col(c): c for c in df.columns}
        # exact
        for c in cand_list:
            n = _norm_col(c)
            if n in norm_map:
                return norm_map[n]
        # fuzzy
        for ncol, orig in norm_map.items():
            for c in cand_list:
                n = _norm_col(c)
                if n and (n in ncol or ncol in n):
                    return orig
        return None

    # ---- 3) try to locate commonly used columns (寬鬆找) ----
    col_entry_time  = _find_first(raw_df, ["進場時間","進場日期","entry time","open time","entry datetime","open date","買入時間","開倉時間","entry"])
    col_exit_time   = _find_first(raw_df, ["出場時間","出場日期","close time","exit time","close datetime","賣出時間","平倉時間","exit"])
    col_entry_price = _find_first(raw_df, ["進場價格","open price","entry price","買入價","開倉價"])
    col_exit_price  = _find_first(raw_df, ["出場價格","close price","sell price","賣出價","平倉價"])
    col_qty         = _find_first(raw_df, ["交易數量","數量","口數","股數","張數","qty","quantity","size","contracts"])
    col_side_in     = _find_first(raw_df, ["進場方向","買賣別","方向","side","position","buy/sell"])
    # col_side_out = 目前用不到，可留作日後擴充

    df_pre = raw_df.copy()

    # ---- 4) 若沒有「交易數量」→ 先補 1 ----
    if col_qty is None:
        df_pre["交易數量"] = 1.0
        col_qty = "交易數量"

    # ---- 5) 能拿到價格就先推回 PnL / Return ----
    can_price = (col_entry_price is not None) and (col_exit_price is not None)
    if can_price:
        ep  = pd.to_numeric(df_pre[col_entry_price], errors="coerce")
        xp  = pd.to_numeric(df_pre[col_exit_price],  errors="coerce")
        qty = pd.to_numeric(df_pre[col_qty],        errors="coerce").fillna(0)

        # 多空判斷（預設做多）
        if col_side_in is not None:
            side_str = df_pre[col_side_in].astype(str).str.lower()
            is_short = side_str.str.contains("賣|空|short|sell")
            side = np.where(is_short, -1.0, 1.0)
        else:
            side = 1.0

        # 成本與 PnL
        mult = float(instrument_multiplier)
        cost = ep * qty * mult

        need_make_pnl = ("獲利金額" not in df_pre.columns) or pd.to_numeric(df_pre.get("獲利金額"), errors="coerce").isna().all()
        if need_make_pnl:
            df_pre["獲利金額"] = (xp - ep) * side * qty * mult

        need_make_ret = ("報酬率" not in df_pre.columns) or pd.to_numeric(df_pre.get("報酬率"), errors="coerce").isna().all()
        if need_make_ret:
            with np.errstate(divide='ignore', invalid='ignore'):
                df_pre["報酬率"] = (pd.to_numeric(df_pre["獲利金額"], errors="coerce") / cost.replace(0, np.nan))

    # ---- 6) 最終欄位對齊（沿用你的函式；若不存在則給一個 no-op 以免 NameError）----
    try:
        resolve_and_rename_columns  # 檢查是否存在
    except NameError:
        def resolve_and_rename_columns(df_in: pd.DataFrame) -> pd.DataFrame:
            """
            如果你的專案本來就有這顆，這段會被忽略；
            若沒有，就把寬鬆找到的欄位統一 rename 成標準欄名。
            """
            df_out = df_in.copy()
            rename_map = {}
            def _add(std_name, found_name):
                if found_name and found_name in df_out.columns and std_name != found_name:
                    rename_map[found_name] = std_name
            _add("進場時間",  col_entry_time)
            _add("出場時間",  col_exit_time)
            _add("進場價格",  col_entry_price)
            _add("出場價格",  col_exit_price)
            _add("交易數量",  col_qty)
            # 「獲利金額」「報酬率」若已存在就不動
            df_out = df_out.rename(columns=rename_map)
            return df_out

    try:
        _df = resolve_and_rename_columns(df_pre)
    except Exception as e:
        st.error(f"欄位對齊失敗：{e}")
        st.stop()

    # ---- 7) 型別處理與補強 ----
    for c in ["出場時間","進場時間"]:
        if c in _df.columns:
            _df[c] = pd.to_datetime(_df[c], errors="coerce")
    for c in ["進場價格","出場價格","獲利金額","交易數量","報酬率"]:
        if c in _df.columns:
            _df[c] = pd.to_numeric(_df[c], errors="coerce")

    # 若仍沒有「報酬率」→ 用 PnL / 成本再補一次
    if ("報酬率" not in _df.columns) or _df["報酬率"].isna().all():
        try:
            _cost = _df["進場價格"] * _df["交易數量"] * float(instrument_multiplier)
            with np.errstate(divide='ignore', invalid='ignore'):
                _df["報酬率"] = (_df["獲利金額"] / _cost.replace(0, np.nan))
        except Exception:
            pass

    # ---- 8) 清洗與排序 ----
    need_cols = [c for c in ["進場時間","出場時間","進場價格","交易數量","獲利金額"] if c in _df.columns]
    _df = _df.dropna(subset=need_cols).sort_values("出場時間").reset_index(drop=True)
    if _df.empty:
        st.warning("資料為空，請檢查 CSV。")

# ===================== Tabs =====================
tabs = st.tabs([
    "📊 績效圖表總覽", "🧠 AI 策略建議",
    "🔬 策略診斷",
    "📋 Summary 統計",
    "📆 期間報酬",
    "📉 報酬風險分布",
    "📝 Markdown 匯出",
])

# ---- Safe tab accessor

def _tab(idx:int, label:str=None):
    try:
        if isinstance(tabs, (list, tuple)) and len(tabs)>idx:
            return tabs[idx]
    except Exception:
        pass
    if label:
        st.warning(f"原始分頁不足以顯示『{label}』（需要第 {idx+1} 個分頁）。已改用下方容器顯示內容。")
    return st.container()

# ===================== Tab[0] — 📊 績效圖表總覽（NAV 口徑對齊 Tab3） =====================
with _tab(0, "📊 績效圖表總覽"):
    if _df is None or _df.empty:
        st.warning("請先上傳 CSV 檔案以檢視統計與比較結果。")
    else:
        st.subheader("📊 淨值曲線 + Drawdown + 基準對照（同暴露）")

        # === A) 準備「投入資金輪廓」：保留你原本的成本/現金流邏輯，用來計算 base_capital 選項 ===
        dfv = _df.sort_values("出場時間").reset_index(drop=True).copy()
        price_in = pd.to_numeric(dfv["進場價格"], errors="coerce")
        qty      = pd.to_numeric(dfv["交易數量"], errors="coerce")
        pnl      = pd.to_numeric(dfv["獲利金額"], errors="coerce")
        t_in     = pd.to_datetime(dfv["進場時間"], errors="coerce").dt.normalize()
        t_out    = pd.to_datetime(dfv["出場時間"], errors="coerce").dt.normalize()
        cost     = price_in * qty * float(instrument_multiplier)

        valid = (cost > 0) & pnl.notna() & t_in.notna() & t_out.notna()
        if not valid.any():
            st.error("沒有有效交易（成本<=0 或缺欄位），無法計算。")
            st.stop()
        dfv = pd.DataFrame({
            "t_in": t_in[valid],
            "t_out": t_out[valid],
            "cost": cost[valid].astype(float),
            "pnl": pnl[valid].astype(float),
        }).sort_values(["t_out", "t_in"]).reset_index(drop=True)

        start_dt = min(dfv["t_in"].min(), dfv["t_out"].min())
        end_dt   = max(dfv["t_in"].max(), dfv["t_out"].max())
        date_index = pd.date_range(start_dt, end_dt, freq="D")

        # 同時投入資金（流量→存量）— 只用來決定 base_capital 可視化口徑
        cashflow_map = {}
        for _, r in dfv.iterrows():
            cashflow_map[r["t_in"]]  = cashflow_map.get(r["t_in"], 0.0) + r["cost"]
            cashflow_map[r["t_out"]] = cashflow_map.get(r["t_out"], 0.0) - r["cost"]
        cf_series = pd.Series(cashflow_map, dtype=float).sort_index()
        invested_daily = cf_series.reindex(date_index, fill_value=0.0).cumsum()
        max_invested_capital_viz = float(max(invested_daily.max(), 0.0))
        st.session_state["max_invested_capital"] = max_invested_capital_viz  # 供其他分頁使用

        # === B) 本金基準（影響金額視角，但不影響 NAV 幾何口徑） ===
        st.markdown("### 💼 本金基準（影響金額視角，不影響 NAV 幾何口徑）")
        base_mode = st.radio(
            "選擇本金基準",
            ["最大同時投入", "平均同時投入（在市日平均）", "自訂本金（$）"],
            horizontal=True,
            index=0,
            key="tab0_base_mode"
        )
        base_custom = st.number_input("自訂本金（$）", min_value=1.0, value=100000.0, step=1000.0, key="tab0_base_custom")
        if base_mode == "最大同時投入":
            base_capital = max_invested_capital_viz if max_invested_capital_viz > 0 else max(abs(dfv["pnl"].sum()), 1.0)
        elif base_mode == "平均同時投入（在市日平均）":
            pos = (invested_daily > 0).astype(float)
            active_days = int(pos.sum())
            base_capital = float(invested_daily[pos == 1].mean()) if active_days > 0 else (max_invested_capital_viz or 1.0)
        else:
            base_capital = float(max(base_custom, 1.0))

        # === C) 用「出場日複利 → 日頻報酬 → NAV」統一 Tab0（與 Tab3 一樣的幾何口徑） ===
        # 1) 同日多筆合成：r_day = Π(1+r_i)-1
        ret_raw = pd.to_numeric(_df["報酬率"], errors="coerce")
        t_out_all = pd.to_datetime(_df["出場時間"], errors="coerce").dt.normalize()

        # 若報酬欄位是百分比（如 3、5 代表 3%、5%），自動轉小數
        _non_na = ret_raw.dropna()
        if len(_non_na):
            q80 = _non_na.abs().quantile(0.80)
            q20 = _non_na.abs().quantile(0.20)
            if (q80 > 1.5) and (q20 >= 0.01):
                ret_raw = ret_raw / 100.0

        daily_ret_nav = (
            pd.DataFrame({"t_out": t_out_all, "ret": ret_raw})
            .dropna()
            .groupby("t_out")["ret"]
            .apply(lambda x: (1.0 + x).prod() - 1.0)
            .sort_index()
        )
        if daily_ret_nav.empty:
            st.error("無可用的日報酬（檢查『出場時間 / 報酬率』）。")
            st.stop()

        # 2) 補成交易日頻率（B），非出場日 = 0 報酬
        nav_index = pd.date_range(daily_ret_nav.index.min(), daily_ret_nav.index.max(), freq="B")
        daily_ret_nav = daily_ret_nav.reindex(nav_index).fillna(0.0)

        # 3) 權益曲線（NAV）與百分比回撤
        nav = (1.0 + daily_ret_nav).cumprod()
        dd_pct = nav / nav.cummax() - 1.0

        # 4) 以 base_capital 轉為金額視角（圖表仍可看 $）
        equity = base_capital * nav
        cum_pnl = equity - base_capital
        dd_amt = equity - (base_capital * nav.cummax())

        # 5) 存入 session_state（供後續基準對照與他頁使用）
        strat_curve = nav.rename("你的策略")
        st.session_state["strat_curve_full"] = strat_curve.copy()
        st.session_state["strat_curve"] = strat_curve.copy()

        # 6) 以 NAV 口徑重畫：累積 P/L（$）＋回撤（$）
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equity.index, y=cum_pnl, mode="lines", name="累積報酬（$）"))
        fig.add_trace(go.Scatter(x=equity.index, y=dd_amt, fill="tozeroy", name="回撤（$）", opacity=0.3))
        fig.update_layout(title="📉 Cumulative P/L with Drawdown（$，NAV 口徑）",
                          xaxis_title="日期", yaxis_title="金額（$）", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, key="tab0_fig_pl")

        # === D) 基準下載（yfinance）— 保持你原本流程，但與 NAV 同期對齊 ===
        @st.cache_data(ttl=86400, show_spinner=False)
        def load_index_series(symbols, start_dt, end_dt):
            out = {}
            try:
                raw = yf.download(
                    tickers=symbols,
                    start=start_dt,
                    end=end_dt + pd.Timedelta(days=1),
                    auto_adjust=True,
                    progress=False,
                    group_by="column",
                    threads=True,
                )
            except Exception:
                return out
            if raw is None or len(raw) == 0:
                return out
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw[raw.columns.levels[0][0]]
                for s_ in close.columns:
                    series = pd.to_numeric(close[s_], errors="coerce").dropna()
                    series.index = pd.to_datetime(series.index)
                    out[str(s_)] = series.astype(float)
            else:
                s_ = raw["Close"] if "Close" in raw.columns else raw.iloc[:, 0]
                s_ = pd.to_numeric(s_, errors="coerce").dropna()
                s_.index = pd.to_datetime(s_.index)
                out[symbols[0]] = s_.astype(float)
            return out

        # 對齊區間改用 NAV 的 index
        bench_symbols = ["SPY", "VOO", "006208.TW"]
        bench_dict = load_index_series(bench_symbols, nav.index.min(), nav.index.max())

        date_all = pd.date_range(nav.index.min(), nav.index.max(), freq="D")
        strat_curve_full = strat_curve.reindex(date_all).ffill().bfill()

        aligned = {}
        for sym in bench_symbols:
            s_ = bench_dict.get(sym, pd.Series(dtype=float))
            if not s_.empty:
                aligned[sym] = s_.reindex(date_all).ffill().bfill().astype(float)

        # === E) Normalized NAV（共同起始日=1） ===
        if len(aligned) > 0:
            candidates = [strat_curve_full.first_valid_index()] + [s_.first_valid_index() for s_ in aligned.values()]
            candidates = [c for c in candidates if pd.notna(c)]
            common_start = max(candidates)
            common_index = pd.date_range(start=common_start, end=nav.index.max(), freq="D")

            strat_norm = (strat_curve_full.reindex(common_index).ffill().bfill())
            strat_norm = strat_norm / strat_norm.iloc[0]
            bench_norm = {}
            for sym, s_curve in aligned.items():
                series = s_curve.reindex(common_index).ffill().bfill()
                bench_norm[sym] = (series / series.iloc[0]).rename(sym)

            plot_df = pd.concat([strat_norm.rename("你的策略")] + list(bench_norm.values()), axis=1)
            fig2 = go.Figure()
            for col in plot_df.columns:
                fig2.add_trace(go.Scatter(x=plot_df.index, y=plot_df[col], mode="lines", name=col))
            fig2.update_layout(
                title="📈 Normalized NAV（共同起始日=1）",
                xaxis_title="日期",
                yaxis_title="淨值（起點=1）",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig2, use_container_width=True, key="tab0_fig_norm")

            # === F) 指標表（同一口徑：以曲線 NAV 為基礎） ===
            def _metrics_from_curve(curve: pd.Series):
                curve = curve.dropna()
                if len(curve) < 2:
                    return np.nan, np.nan, np.nan, np.nan, np.nan
                rets = curve.pct_change().dropna()
                days = (curve.index[-1] - curve.index[0]).days
                years = max(days / 365.25, 1e-9)
                cagr = (curve.iloc[-1] / curve.iloc[0]) ** (1.0 / years) - 1.0
                vol = rets.std() * np.sqrt(252) if len(rets) > 1 else np.nan
                sharpe = (rets.mean() * 252) / (rets.std() + 1e-12) if len(rets) > 1 else np.nan
                dd = curve / curve.cummax() - 1.0
                mdd = float(dd.min()) if len(dd) else np.nan
                calmar = cagr / abs(mdd) if (pd.notna(mdd) and mdd < 0) else np.nan
                return cagr, vol, sharpe, mdd, calmar

            all_curves = {"你的策略": strat_norm}
            all_curves.update(bench_norm)
            perf_rows = {}
            for name, curve in all_curves.items():
                cagr, vol, sharpe, mdd, calmar = _metrics_from_curve(curve)
                perf_rows[name] = {"CAGR": cagr, "Volatility": vol, "Sharpe": sharpe, "MDD": mdd, "Calmar": calmar}
            perf_df = pd.DataFrame(perf_rows)

            show_df = perf_df.copy()
            for col in show_df.columns:
                show_df.loc["CAGR", col]       = f"{show_df.loc['CAGR', col]*100:.2f}%" if pd.notna(perf_df.loc["CAGR", col]) else "—"
                show_df.loc["Volatility", col] = f"{show_df.loc['Volatility', col]*100:.2f}%" if pd.notna(perf_df.loc["Volatility", col]) else "—"
                show_df.loc["Sharpe", col]     = f"{show_df.loc['Sharpe', col]:.2f}" if pd.notna(perf_df.loc["Sharpe", col]) else "—"
                show_df.loc["MDD", col]        = f"{show_df.loc['MDD', col]*100:.2f}%" if pd.notna(perf_df.loc["MDD", col]) else "—"
                show_df.loc["Calmar", col]     = f"{show_df.loc['Calmar', col]:.2f}" if pd.notna(perf_df.loc["Calmar", col]) else "—"
            st.markdown("### 🧾 績效指標（同口徑：NAV）")
            st.dataframe(show_df, use_container_width=True)

            # === G) Normalized Drawdown（共同起始日） ===
            st.markdown("### 📉 Normalized Drawdown（共同起始日口徑）")
            dd_df = pd.DataFrame({name: (curve / curve.cummax() - 1.0) for name, curve in all_curves.items()})
            dd_df = dd_df.reindex(common_index).ffill().bfill()
            fig_dd = go.Figure()
            for col in dd_df.columns:
                fig_dd.add_trace(go.Scatter(x=dd_df.index, y=dd_df[col] * 100.0, mode="lines", name=col))
            fig_dd.update_layout(
                title="📉 Normalized Drawdown（MDD%）— 共同起始日對齊",
                xaxis_title="日期",
                yaxis_title="Drawdown（%）",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(ticksuffix="%"),
            )
            st.plotly_chart(fig_dd, use_container_width=True, key="tab0_fig_dd")

# ===================== Tab[1] — AI 策略建議 =====================
with tabs[1]:
    st.subheader("\U0001f9e0 AI 策略建議生成")

    st.markdown("""
    - 根據目前策略的績效指標，我們將提供改善建議與強化方向。
    - 包含：停損設計、風控機制、交易頻率、獲利結構等面向。
    """)

    # ✅ 修正：改用 session_state 確認資料是否就緒
    ready = (
        uploaded_file is not None
        and "start_date" in st.session_state
        and "end_date" in st.session_state
        and "net_profit" in st.session_state
    )

    if ready:
        # 從 session_state 取值（避免 NameError / locals 範圍問題）
        start_date = st.session_state.start_date
        end_date = st.session_state.end_date
        net_profit = st.session_state.net_profit
        max_drawdown_value = st.session_state.max_drawdown_value
        geo_apy_from_excel = st.session_state.geo_apy_from_excel
        sharpe_ratio = st.session_state.sharpe_ratio
        sortino_ratio = st.session_state.sortino_ratio
        profit_factor = st.session_state.profit_factor
        win_rate = st.session_state.win_rate
        reward_risk_ratio = st.session_state.reward_risk_ratio
        trade_count = st.session_state.trade_count
        avg_holding_days = st.session_state.avg_holding_days

        # 顯示摘要區
        summary_prompt = f"""
策略名稱：{strategy_name}
版本：{version}
商品類型：{instrument_type}
回測期間：{start_date.date()} ~ {end_date.date()}
執行頻率：{execution_freq}
策略描述：{strategy_desc}
優化方向：{optimize_focus}
淨利：{net_profit:,.0f} 元
最大回撤：{max_drawdown_value:,.0f} 元
年化報酬率（幾何）：{geo_apy_from_excel:.2f}%
風報比：{net_profit / abs(max_drawdown_value):.2f}
Sharpe：{sharpe_ratio:.2f}
Sortino：{sortino_ratio:.2f}
獲利因子：{profit_factor:.2f}
勝率：{win_rate*100:.2f}%
賺賠比：{reward_risk_ratio:.2f}
交易次數：{trade_count}
平均持倉天數：{avg_holding_days:.2f}
        """

        col1, col2 = st.columns(2)
        with col1:
            generate = st.button("🔍 使用 OpenRouter 產生 AI 策略建議", key="ai_strategy_button")
        with col2:
            regenerate = st.button("♻️ 重新產生建議", key="ai_strategy_regenerate_button")

        if generate or regenerate:
            if api_key:
                try:
                    from openai import OpenAI
                    import json
                    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

                    summary_dict = {
                        "策略名稱": strategy_name,
                        "版本": version,
                        "商品": instrument_type,
                        "回測期間": f"{start_date.date()} ~ {end_date.date()}",
                        "執行頻率": execution_freq,
                        "描述": strategy_desc,
                        "淨利": net_profit,
                        "最大回撤": max_drawdown_value,
                        "年化報酬率": geo_apy_from_excel,
                        "風報比": net_profit / abs(max_drawdown_value),
                        "Sharpe": sharpe_ratio,
                        "Sortino": sortino_ratio,
                        "獲利因子": profit_factor,
                        "勝率": win_rate,
                        "賺賠比": reward_risk_ratio,
                        "交易次數": trade_count,
                        "平均持倉天數": avg_holding_days
                    }

                    # numpy → Python 型別
                    summary_dict = {
                        k: (v.item() if isinstance(v, (np.integer, np.floating)) else v)
                        for k, v in summary_dict.items()
                    }

                    prompt = (
                        "你是資深量化交易策略分析師，請根據以下績效摘要提供具體優化建議，"
                        "並比較此策略與大盤0050與VOO與SPY哪個好：\n\n"
                        + json.dumps(summary_dict, ensure_ascii=False)
                    )

                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[
                            {"role": "system", "content": "你是量化交易顧問，請根據績效指標提供條列建議"},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ai_reply = response.choices[0].message.content
                    st.markdown("#### 📌 OpenRouter 策略建議")
                    st.write(ai_reply)
                except Exception as e:
                    st.error(f"生成建議錯誤：{e}")
            else:
                st.warning("請輸入有效的 OpenRouter API 金鑰。")
    else:
        st.warning("⚠️ 請先在『📋 Summary 統計』頁成功讀檔並完成指標計算（會自動帶入）。")

# ===================== Tab[2] — 策略診斷 =====================
with _tab(2, "🔬 策略診斷"):
    st.subheader("🔬 策略診斷 — 自動檢查常見問題")
    if uploaded_file is None or _df is None or _df.empty:
        st.info("請先上傳 CSV 並完成前面頁籤的計算。")
    else:
        # 快速計算一些指標（沿用 Tab0 結果）
        cum_profit = _df["獲利金額"].cumsum()
        dd_val = cum_profit - cum_profit.cummax()
        net_profit = float(_df["獲利金額"].sum())
        max_dd_amt = float(dd_val.min()) if len(dd_val) else 0.0
        win_rate = (_df["獲利金額"] > 0).mean()
        trade_count = int(len(_df))
        avg_holding_days = (_df["出場時間"] - _df["進場時間"]).dt.days.mean()
        s = st.session_state
        issues = []
        if trade_count < 30:
            issues.append(("樣本不足", f"交易僅 {trade_count} 筆，統計顯著性可能不足。"))
        if pd.notna(avg_holding_days) and avg_holding_days < 2:
            issues.append(("過度短線", f"平均持倉 {avg_holding_days:.1f} 天，易受噪音影響。"))
        if pd.notna(s.get("sharpe_ratio", np.nan)) and s.sharpe_ratio > 5:
            issues.append(("Sharpe 異常偏高", f"Sharpe={s.sharpe_ratio:.2f}，請檢查報酬口徑。"))
        if pd.notna(s.get("sortino_ratio", np.nan)) and s.sortino_ratio > 10:
            issues.append(("Sortino 異常偏高", f"Sortino={s.sortino_ratio:.2f}，可能樣本不足或下行波動被低估。"))
        if max_dd_amt != 0 and (net_profit/abs(max_dd_amt)) < 1:
            issues.append(("風報比偏低", "淨利/最大回撤 < 1，策略承擔風險過高。"))
        rr = s.get("reward_risk_ratio", np.nan)
        p  = s.get("win_rate", win_rate)
        kelly = (p - (1-p)/rr) if (pd.notna(rr) and rr not in (0,np.nan) and pd.notna(p)) else np.nan
        if pd.notna(kelly) and kelly > 0.5:
            issues.append(("Kelly 偏大", f"f*≈{kelly:.2f}，實務建議使用 1/2 或 1/3。"))

        diag_df = pd.DataFrame(issues, columns=["問題", "說明"])
        if diag_df.empty:
            st.success("暫未發現明顯結構性問題。可進一步做穩健性測試（時段切割、蒙地卡羅、走勢漂移）。")
        else:
            st.markdown("### 📌 自動診斷結果")
            st.dataframe(diag_df, use_container_width=True)

# ============================ Tab[3] — 📋 Summary 統計（合併完整版） ============================
# ===================== Tab[3] — 📋 Summary 統計 =====================
with _tab(3, "📋 Summary 統計"):
    st.subheader("📋 Summary 經效分析（分區顯示 + Kelly 試算）")

    if _df is None or _df.empty:
        st.info("尚未載入策略 DataFrame")
    else:
        d = _df.copy()
        d["單筆投入"]   = d["進場價格"] * d["交易數量"] * instrument_multiplier
        d["單筆報酬率"] = d["獲利金額"] / d["單筆投入"].replace(0, np.nan)

        total_trades = len(d)
        win_rate     = (d["獲利金額"] > 0).mean()
        avg_return   = d["單筆報酬率"].mean()

        # 自動偵測報酬率欄
        cand = [c for c in d.columns if ("報酬" in str(c) and "率" in str(c))]
        cand += [c for c in d.columns if str(c).lower() in ["return","returns","pct_return","roi","ret"]]
        ret_col = cand[0] if cand else "單筆報酬率"

        def _normalize_return_series(s: pd.Series) -> pd.Series:
            s = s.astype(str).str.strip().str.replace('%', '', regex=False).str.replace(',', '', regex=False)
            s = pd.to_numeric(s, errors='coerce')
            non_na = s.dropna()
            if len(non_na) == 0:
                return s
            q80 = non_na.abs().quantile(0.80)
            q20 = non_na.abs().quantile(0.20)
            if q80 > 1.5 and q20 >= 0.01:
                s = s / 100.0
            return s

        ret_series = _normalize_return_series(d[ret_col]).dropna()
        st.session_state["ret_series"] = ret_series.copy()  # 👈 Tab5/Markdown 用

        # 區間 MDD% 與 Calendar CAGR
        if len(ret_series) > 0:
            nav = (1 + ret_series).cumprod()
            mdd_pct_interval = float((nav / nav.cummax() - 1.0).min() * 100.0)
            years = max((d["出場時間"].max() - d["進場時間"].min()).days / 365.25, 1e-9)
            end_multiple = float(np.prod(1.0 + ret_series))
            geo_apy_calendar = (end_multiple ** (1.0 / years) - 1.0) * 100.0
        else:
            mdd_pct_interval = np.nan
            geo_apy_calendar = np.nan

        # 近似日報酬 → Sharpe / Sortino
        daily_pnl = d.groupby(d["出場時間"].dt.date)["獲利金額"].sum()
        daily_pnl.index = pd.to_datetime(daily_pnl.index)
        base_cap = st.session_state.get("max_invested_capital", np.nan)
        daily_ret = daily_pnl / base_cap if (pd.notna(base_cap) and base_cap > 0) else daily_pnl

        mean_d   = float(daily_ret.mean())
        std_d    = float(daily_ret.std())
        down_std = float(daily_ret[daily_ret < 0].std())
        sharpe_ratio  = (mean_d / std_d) * np.sqrt(252) if std_d  > 0 else np.nan
        sortino_ratio = (mean_d / down_std) * np.sqrt(252) if down_std > 0 else np.nan

        # 指標卡
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("總交易數", total_trades)
        c2.metric("勝率", f"{win_rate*100:.2f}%")
        c3.metric("平均報酬", f"{avg_return:.2%}")
        c4.metric("CAGR", f"{geo_apy_calendar:.2f}%" if pd.notna(geo_apy_calendar) else "—")
        c5, c6 = st.columns(2)
        c5.metric("MDD", f"{mdd_pct_interval/100:.2%}" if pd.notna(mdd_pct_interval) else "—")

        # Kelly
        has_loss = (d["單筆報酬率"] < 0).any()
        payoff = (
            d.loc[d["單筆報酬率"] > 0, "單筆報酬率"].mean() /
            abs(d.loc[d["單筆報酬率"] < 0, "單筆報酬率"].mean())
        ) if has_loss else np.nan
        kelly = win_rate - (1 - win_rate) / payoff if (pd.notna(payoff) and payoff > 0) else np.nan
        c6.metric("Kelly 值", f"{kelly:.2f}" if pd.notna(kelly) else "—")

        st.divider()
        st.markdown("### 💰 Kelly 配置資金試算")
        kelly_capital = st.number_input("可用資金（$）", min_value=0.0, value=100000.0, step=1000.0, key="tab3_kelly_cap")
        if pd.notna(kelly) and kelly > 0:
            st.info(f"✅ 建議投入（f*）：${kelly_capital*kelly:,.0f}；半額：${kelly_capital*kelly/2:,.0f}")
        else:
            st.warning("Kelly ≤ 0，暫不建議依此策略放大資金。")

        # ===== 分區顯示（加強版表格摘要） =====
        def show_metric_section(title, rows, color="white"):
            st.markdown(
                f"<div style='background-color:{color}; padding:8px; border-radius:6px'><b>{title}</b></div>",
                unsafe_allow_html=True,
            )
            _d = pd.DataFrame(rows, columns=["指標名稱", "數值", "解釋與重要性", "計算公式 / 備註"])
            st.dataframe(_d, use_container_width=True)

        # 基礎統計
        cumulative_profit = d["獲利金額"].cumsum()
        rolling_max = cumulative_profit.cummax()
        drawdown_val = cumulative_profit - rolling_max
        max_drawdown_value = float(drawdown_val.min()) if len(drawdown_val) else 0.0

        gross_profit = d.loc[d["獲利金額"] > 0, "獲利金額"].sum()
        gross_loss   = d.loc[d["獲利金額"] < 0, "獲利金額"].sum()
        net_profit   = d["獲利金額"].sum()
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else np.nan
        trade_count = int(len(d))
        max_profit_trade = float(d["獲利金額"].max())
        max_loss_trade   = float(d["獲利金額"].min())
        avg_holding_days = (d["出場時間"] - d["進場時間"]).dt.days.mean()

        # 單筆報酬率結構
        avg_profit = d.loc[d["獲利金額"] > 0, "獲利金額"].mean()
        avg_loss   = d.loc[d["獲利金額"] < 0, "獲利金額"].mean()
        d["單筆報酬率"] = d["獲利金額"] / d["單筆投入"]
        avg_profit_pct = float(d.loc[d["獲利金額"] > 0, "單筆報酬率"].mean() * 100.0) if (d["獲利金額"] > 0).any() else np.nan
        avg_loss_pct   = float(d.loc[d["獲利金額"] < 0, "單筆報酬率"].mean() * 100.0) if (d["獲利金額"] < 0).any() else np.nan

        # 同時資金佔用峰值
        cashflow = pd.Series(dtype=float)
        for _, row in d.iterrows():
            entry_time = pd.to_datetime(row["進場時間"])
            exit_time  = pd.to_datetime(row["出場時間"])
            _cost = float(row["進場價格"]) * float(row["交易數量"]) * float(instrument_multiplier)
            cashflow[entry_time] = cashflow.get(entry_time, 0.0) + _cost
            cashflow[exit_time]  = cashflow.get(exit_time, 0.0) - _cost
        cashflow = cashflow.sort_index()
        cumulative_capital = cashflow.cumsum()
        max_invested_capital = float(cumulative_capital.max()) if len(cumulative_capital) else np.nan
        st.session_state["max_invested_capital"] = max_invested_capital  # 再保險

        # 年化（Calendar / Active / 算術）
        inception_date = min(d["進場時間"].min(), d["出場時間"].min())
        end_date = d["出場時間"].max()
        years = max((end_date - inception_date).days, 1) / 365.25

        if len(ret_series) > 0 and years > 0:
            end_multiple = float(np.prod(1.0 + ret_series))
            geo_apy_calendar = (end_multiple ** (1.0 / years) - 1.0) * 100.0
            arithmetic_apy_calendar = ret_series.mean() * (len(ret_series) / years) * 100.0
        else:
            arithmetic_apy_calendar = np.nan

        active_days = (d["出場時間"] - d["進場時間"]).dt.days.clip(lower=0).sum()
        active_years = active_days / 365.25 if active_days and active_days > 0 else np.nan
        if len(ret_series) > 0 and pd.notna(active_years) and active_years > 0:
            end_multiple = float(np.prod(1.0 + ret_series))
            geo_apy_active = (end_multiple ** (1.0 / active_years) - 1.0) * 100.0
        else:
            geo_apy_active = np.nan

        # Sharpe / Sortino 已於上方算過

        # 期望值
        expected_value = float(net_profit / trade_count) if trade_count else 0.0
        reward_risk_ratio = (avg_profit / abs(avg_loss)) if (pd.notna(avg_profit) and pd.notna(avg_loss) and avg_loss != 0) else np.nan
        kelly_full = (win_rate - ((1.0 - win_rate) / reward_risk_ratio)) if pd.notna(reward_risk_ratio) and reward_risk_ratio not in (0, np.nan) else np.nan
        kelly_half = kelly_full / 2.0 if pd.notna(kelly_full) else np.nan
        ev_pct = (win_rate * avg_profit_pct + (1 - win_rate) * avg_loss_pct) if (pd.notna(avg_profit_pct) and pd.notna(avg_loss_pct)) else np.nan

        # 存入 session_state（供 Tab6/Markdown、AI）
        st.session_state.update({
            "start_date": inception_date,
            "end_date": end_date,
            "net_profit": float(net_profit),
            "max_drawdown_value": float(max_drawdown_value),
            "geo_apy_from_excel": float(geo_apy_calendar) if pd.notna(geo_apy_calendar) else np.nan,
            "sharpe_ratio": float(sharpe_ratio) if pd.notna(sharpe_ratio) else np.nan,
            "sortino_ratio": float(sortino_ratio) if pd.notna(sortino_ratio) else np.nan,
            "profit_factor": float(profit_factor) if pd.notna(profit_factor) else np.nan,
            "win_rate": float(win_rate) if pd.notna(win_rate) else np.nan,
            "reward_risk_ratio": float(reward_risk_ratio) if pd.notna(reward_risk_ratio) else np.nan,
            "trade_count": int(trade_count),
            "avg_holding_days": float(avg_holding_days) if pd.notna(avg_holding_days) else np.nan,
            "avg_profit_pct": avg_profit_pct,
            "avg_loss_pct": avg_loss_pct,
        })

        # 分區顯示（精簡）
        show_metric_section(
            "🟢【整體經效核心指標】",
            [
                ["淨利 ($)", f"${net_profit:,.0f}", "最直觀的策略總獲利", "總收益 - 總損失"],
                ["最大回撤 ($)", f"${max_drawdown_value:,.0f}", "區間最大回撤金額", "累積損益相對歷史高點之跌幅"],
                ["區間最大回撤（MDD%）", f"{(0 if pd.isna(mdd_pct_interval) else mdd_pct_interval):.2f}%", "標準 MDD%，基於報酬率欄的權益曲線", "min(NAV/peak-1) × 100"],
                ["最大投入金額 ($)", f"${(0 if pd.isna(max_invested_capital) else max_invested_capital):,.0f}", "策略期間最大持倉成本", "資金佔用峰值"],
                ["幾何年化（Calendar CAGR）", f"{(0 if pd.isna(geo_apy_calendar) else geo_apy_calendar):.2f}%", "含空手期的真·年化", "(終值/起值)^(1/年數)-1"],
                ["幾何年化（Active CAGR）", f"{(0 if pd.isna(geo_apy_active) else geo_apy_active):.2f}%", "只計在市天數", "(終值/起值)^(1/在市年數)-1"],
            ],
        )
        show_metric_section(
            "🟡【報酬與風控】",
            [
                ["Sharpe", f"{sharpe_ratio:.2f}" if pd.notna(sharpe_ratio) else "—", "風險調整報酬", "mean/σ × √252"],
                ["Sortino", f"{sortino_ratio:.2f}" if pd.notna(sortino_ratio) else "—", "下行風險 Sharpe", "mean/σ_down × √252"],
                ["獲利因子", f"{profit_factor:.2f}" if pd.notna(profit_factor) else "—", "總獲利/|總虧損|", ""],
                ["最大單次虧損 ($)", f"${max_loss_trade:,.0f}", "極端損失敏感度", ""],
                ["最大單次獲利 ($)", f"${max_profit_trade:,.0f}", "極端獲利能力", ""],
            ],
        )
        show_metric_section(
            "🔹【品質與結構】",
            [
                ["勝率", f"{win_rate*100:.2f}%", "獲利次數 / 總交易數", ""],
                ["賺賠比", f"{(avg_profit/abs(avg_loss)) if (pd.notna(avg_profit) and pd.notna(avg_loss) and avg_loss!=0) else np.nan:.2f}", "平均獲利/|平均虧損|", ""],
                ["平均每筆($)", f"${(net_profit/trade_count) if trade_count else 0:,.0f}", "期望值", ""],
                ["平均獲利(%)", f"{avg_profit_pct:.2f}%" if pd.notna(avg_profit_pct) else "—", "單筆報酬率均值(獲利)", ""],
                ["平均虧損(%)", f"{avg_loss_pct:.2f}%" if pd.notna(avg_loss_pct) else "—", "單筆報酬率均值(虧損)", ""],
                ["平均持倉天數", f"{avg_holding_days:.2f}", "出場 - 進場", ""],
            ],
        )
# ======================= Tab[4] — Return Analysis (Year / Quarter / Month) =======================
with tabs[4]:
    st.subheader("📊 Return Analysis")

    # ---- Source Data ----
    # 你的全域資料表原先命名為 _df；若使用者另外設了 df，優先使用 df，否則退回 _df。
    _base_df = None
    try:
        _base_df = df if ("df" in globals() and isinstance(df, pd.DataFrame)) else None
    except Exception:
        _base_df = None
    if _base_df is None:
        _base_df = _df if ("_df" in globals() and isinstance(_df, pd.DataFrame)) else None

    if uploaded_file and isinstance(_base_df, pd.DataFrame) and not _base_df.empty:
        # ---------- Preprocess ----------
        df4 = _base_df.copy()
        df4["出場時間"] = pd.to_datetime(df4["出場時間"], errors="coerce")
        df4["Year"] = df4["出場時間"].dt.year
        df4["Month"] = df4["出場時間"].dt.month
        df4["YearMonth"] = df4["出場時間"].dt.to_period("M").astype(str)
        df4["Quarter"] = df4["出場時間"].dt.to_period("Q").astype(str)  # e.g., '2024Q3'

        # 確保數值欄位型別
        for col in ["進場價格", "交易數量", "獲利金額"]:
            if col in df4.columns:
                df4[col] = pd.to_numeric(df4[col], errors="coerce")

        # 若缺少「報酬率」或「獲利金額」，用另一個欄位 + 成本推回
        need_ret = ("報酬率" not in df4.columns) or df4["報酬率"].isna().all()
        need_pnl = ("獲利金額" not in df4.columns) or df4["獲利金額"].isna().all()
        cost = None
        if ("進場價格" in df4.columns) and ("交易數量" in df4.columns):
            try:
                cost = df4["進場價格"] * df4["交易數量"] * float(instrument_multiplier)
            except Exception:
                cost = None
        if need_pnl and (not need_ret) and (cost is not None):
            # 用 報酬率 × 成本 回推 獲利金額
            df4["獲利金額"] = pd.to_numeric(df4["報酬率"], errors="coerce") * cost
        if need_ret and (not need_pnl) and (cost is not None):
            # 用 獲利金額 / 成本 回推 報酬率（十進位）
            with np.errstate(divide='ignore', invalid='ignore'):
                df4["報酬率"] = df4["獲利金額"] / cost.replace(0, np.nan)
        # 標準化 報酬率 為十進位（若出現百分比）
        if "報酬率" in df4.columns:
            s = pd.to_numeric(pd.Series(df4["報酬率"]).astype(str).str.replace('%','',regex=False), errors='coerce')
            # 百分比偵測：若80分位數 > 1.5 視為百分比
            non_na = s.dropna()
            if len(non_na):
                q80 = non_na.abs().quantile(0.80)
                q20 = non_na.abs().quantile(0.20)
                if (q80 > 1.5) and (q20 >= 0.01):
                    s = s / 100.0
            df4["報酬率"] = s

        # ====== 安全：去除 NA 並保留必要欄位 ======
        must_cols = ["Year", "Month", "報酬率", "獲利金額", "YearMonth", "Quarter"]
        df4 = df4.dropna(subset=[c for c in must_cols if c in df4.columns])
        if df4.empty:
            st.info("資料不足以計算。請確認有 '報酬率' 或 '獲利金額' 與 '進場價格/交易數量' 等欄位。")
            st.stop()

        # ---------- Helper：把 yf.download 回傳安全抽成 1D Close Series ----------
        def extract_close_series(px: pd.DataFrame) -> pd.Series:
            """Return a 1D float Series of Close/Adj Close regardless of MultiIndex or single-index."""
            if not isinstance(px, pd.DataFrame) or px.empty:
                return pd.Series(dtype=float)
            if isinstance(px.columns, pd.MultiIndex):
                for lvl0 in ["Adj Close", "Close"]:
                    if lvl0 in px.columns.get_level_values(0):
                        s = px[lvl0]
                        if isinstance(s, pd.DataFrame):
                            if "SPY" in s.columns:
                                s = s["SPY"]
                            else:
                                s = s.iloc[:, 0]
                        return pd.to_numeric(s, errors="coerce").dropna()
                s = px.xs(px.columns.levels[0][0], axis=1, level=0)
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[:, 0]
                return pd.to_numeric(s, errors="coerce").dropna()
            else:
                for col in ["Adj Close", "Close"]:
                    if col in px.columns:
                        return pd.to_numeric(px[col], errors="coerce").dropna()
                num = px.select_dtypes(include=[np.number])
                if num.shape[1] > 0:
                    return pd.to_numeric(num.iloc[:, 0], errors="coerce").dropna()
                return pd.Series(dtype=float)

        # ================= 1) Annual Return — Strategy vs SPY（% + $ on bar） =================
        st.markdown("### 📈 Annual Return Bar Chart (Strategy vs SPY)")

        # 策略年度：年平均報酬率(%) + 年度總獲利($)
        annual_pct = df4.groupby("Year")["報酬率"].mean() * 100.0
        annual_pnl = df4.groupby("Year")["獲利金額"].sum()
        annual_df = (
            pd.concat([annual_pct.rename("ReturnPct"), annual_pnl.rename("Profit")], axis=1)
            .reset_index()
            .dropna()
        )

        # SPY 年報酬（同期間，年末/年初-1）
        start_dt = df4["出場時間"].min().normalize()
        end_dt   = df4["出場時間"].max().normalize() + pd.Timedelta(days=1)
        spy_raw = yf.download("SPY", start=start_dt, end=end_dt, auto_adjust=True, progress=False)
        spy_close = extract_close_series(spy_raw)

        if not spy_close.empty:
            y_first = spy_close.resample("Y").first()
            y_last  = spy_close.resample("Y").last()
            spy_ret_annual = (y_last / y_first - 1.0) * 100.0
            spy_ret_annual.index = spy_ret_annual.index.year
            spy_ret_annual_df = spy_ret_annual.to_frame(name="SPYReturnPct")
        else:
            spy_ret_annual_df = pd.DataFrame(columns=["SPYReturnPct"])

        annual_df = annual_df.merge(spy_ret_annual_df, left_on="Year", right_index=True, how="left")

        col_strategy = np.where(annual_df["ReturnPct"] >= 0, "seagreen", "salmon")
        col_spy      = np.where(annual_df["SPYReturnPct"].fillna(0) >= 0, "steelblue", "#d9534f")

        fig_year_cmp = go.Figure()
        # 策略（柱上同時顯示$與%）
        fig_year_cmp.add_trace(
            go.Bar(
                x=annual_df["Year"].astype(str),
                y=annual_df["ReturnPct"],
                name="Strategy (%)",
                marker_color=col_strategy,
                text=[f"$ {p:,.0f}{r:.2f}%" for p, r in zip(annual_df["Profit"], annual_df["ReturnPct"])],
                textposition="outside",
                texttemplate="%{text}",
                hovertemplate="Year: %{x}<br>Strategy Return: %{y:.2f}%<br>Strategy Profit: $%{customdata:,.0f}<extra></extra>",
                customdata=annual_df["Profit"],
            )
        )
        # SPY
        fig_year_cmp.add_trace(
            go.Bar(
                x=annual_df["Year"].astype(str),
                y=annual_df["SPYReturnPct"],
                name="SPY (%)",
                marker_color=col_spy,
                text=[f"{v:.2f}%" if pd.notna(v) else "NA" for v in annual_df["SPYReturnPct"]],
                textposition="outside",
                hovertemplate="Year: %{x}<br>SPY Return: %{y:.2f}%<extra></extra>",
            )
        )
        fig_year_cmp.update_layout(
            title="📈 Annual Return — Strategy vs SPY (bars only)",
            xaxis_title="Year",
            yaxis_title="Return (%)",
            barmode="group",
            bargap=0.25,
            legend=dict(orientation="h"),
            hovermode="x unified",
            margin=dict(t=60),
        )
        st.plotly_chart(fig_year_cmp, use_container_width=True)

        # ➕ Annual Average（策略 vs SPY）
        avg_strategy_y = annual_df["ReturnPct"].mean()
        avg_spy_y = annual_df["SPYReturnPct"].mean()
        st.markdown(f"**Annual Average Return** — Strategy: `{avg_strategy_y:.2f}%` ｜ SPY: `{avg_spy_y:.2f}%`")

        # ================= 2) Quarterly Return — Strategy vs SPY =================
        st.markdown("### 🗓️ Quarterly Return Bar Chart (Average Return, Strategy vs SPY)")

        # 策略季度：季平均報酬率(%) + 季度總獲利($)
        q_avg_ret = df4.groupby("Quarter")["報酬率"].mean() * 100.0
        q_profit  = df4.groupby("Quarter")["獲利金額"].sum()
        q_df = (
            pd.concat([q_avg_ret.rename("ReturnPct"), q_profit.rename("Profit")], axis=1)
            .reset_index()
            .rename(columns={"Quarter": "Period"})
            .dropna()
            .sort_values("Period")
        )

        # SPY 季報酬（季末/季初-1）
        if not spy_close.empty:
            q_first = spy_close.resample("Q").first()
            q_last  = spy_close.resample("Q").last()
            spy_ret_q = (q_last / q_first - 1.0) * 100.0
            spy_ret_q.index = spy_ret_q.index.to_period("Q").astype(str)
            spy_ret_q_df = spy_ret_q.to_frame(name="SPYReturnPct")
        else:
            spy_ret_q_df = pd.DataFrame(columns=["SPYReturnPct"])

        q_df = q_df.merge(spy_ret_q_df, left_on="Period", right_index=True, how="left")

        q_colors     = np.where(q_df["ReturnPct"] >= 0, "seagreen", "salmon")
        q_colors_spy = np.where(q_df["SPYReturnPct"].fillna(0) >= 0, "steelblue", "#d9534f")

        fig_quarter = go.Figure()
        fig_quarter.add_trace(
            go.Bar(
                x=q_df["Period"],
                y=q_df["ReturnPct"],
                marker_color=q_colors,
                name="Strategy (%)",
                text=[f"$ {p:,.0f}{r:.2f}%" for p, r in zip(q_df["Profit"], q_df["ReturnPct"])],
                textposition="outside",
                texttemplate="%{text}",
                hovertemplate="Quarter: %{x}<br>Avg Return: %{y:.2f}%<br>Profit: $%{customdata:,.0f}<extra></extra>",
                customdata=q_df["Profit"],
            )
        )
        fig_quarter.add_trace(
            go.Bar(
                x=q_df["Period"],
                y=q_df["SPYReturnPct"],
                name="SPY (%)",
                marker_color=q_colors_spy,
                text=[f"{v:.2f}%" if pd.notna(v) else "NA" for v in q_df["SPYReturnPct"]],
                textposition="outside",
                hovertemplate="Quarter: %{x}<br>SPY Return: %{y:.2f}%<extra></extra>",
            )
        )
        fig_quarter.update_layout(
            title="🗓️ Quarterly Average Return — Strategy vs SPY",
            xaxis_title="Quarter",
            yaxis_title="Return (%)",
            barmode="group",
            bargap=0.25,
            legend=dict(orientation="h"),
            hovermode="x unified",
            margin=dict(t=60),
        )
        st.plotly_chart(fig_quarter, use_container_width=True)

        # ➕ Quarterly Average（策略 vs SPY）
        avg_strategy_q = q_df["ReturnPct"].mean()
        avg_spy_q = q_df["SPYReturnPct"].mean()
        st.markdown(f"**Quarterly Average Return** — Strategy: `{avg_strategy_q:.2f}%` ｜ SPY: `{avg_spy_q:.2f}%`")

        # ================= 3) Monthly Return Heatmap =================
        st.markdown("### 📅 Monthly Return Heatmap")
        monthly_matrix = df4.groupby(["Year", "Month"])["報酬率"].mean().unstack().sort_index()
        # 使用 Plotly 取代 seaborn，避免依賴與風格不一致
        st.plotly_chart(
            px.imshow(
                monthly_matrix * 100.0,
                text_auto=True,
                aspect='auto',
                labels=dict(color='Avg Return (%)'),
                x=[str(m) for m in monthly_matrix.columns],
                y=[str(y) for y in monthly_matrix.index],
                title="Monthly Return Heatmap"
            ),
            use_container_width=True,
        )

        # ================= 4) Holding Assets Table =================
        st.markdown("### 📦 Holding Assets Table")
        if "商品名稱" in df4.columns:
            group_key = "商品名稱"
        elif "商品代碼" in df4.columns:
            group_key = "商品代碼"
        else:
            group_key = None

        if group_key:
            holding_df = df4.groupby(group_key).agg(
                Trades=("報酬率", "count"),
                Qty=("交易數量", "sum"),
                Profit=("獲利金額", "sum"),
                AvgReturn=("報酬率", "mean"),
            ).reset_index()
            holding_df["AvgReturn"] = (holding_df["AvgReturn"] * 100).round(2)
            holding_df["Profit"] = holding_df["Profit"].round(0)
            holding_df = holding_df.rename(columns={group_key: "Symbol/Name"})
            st.dataframe(
                holding_df.style.format({
                    "AvgReturn": "{:.2f}%",
                    "Profit": "{:,.0f}",
                    "Qty": "{:,.0f}",
                    "Trades": "{:,.0f}",
                }),
                use_container_width=True
            )
        else:
            st.info("No symbol columns found ('商品名稱' / '商品代碼'); showing aggregated totals only.")
            agg_df = df4.agg(
                Trades=("報酬率", "count"),
                Qty=("交易數量", "sum"),
                Profit=("獲利金額", "sum"),
                AvgReturn=("報酬率", "mean"),
            ).to_frame().T
            agg_df["AvgReturn"] = (agg_df["AvgReturn"] * 100).round(2)
            agg_df["Profit"] = agg_df["Profit"].round(0)
            st.dataframe(
                agg_df.style.format({
                    "AvgReturn": "{:.2f}%",
                    "Profit": "{:,.0f}",
                    "Qty": "{:,.0f}",
                    "Trades": "{:,.0f}",
                }),
                use_container_width=True
            )

        # ================= 5) Monthly Holding Count（每月持倉個數） =================
        st.markdown("### 📊 Monthly Holding Count")
        if "商品代碼" in df4.columns:
            label_col = "商品代碼"
        elif "商品名稱" in df4.columns:
            label_col = "商品名稱"
        else:
            label_col = None

        if label_col:
            monthly_hold_cnt = df4.groupby("YearMonth")[label_col].nunique()
            ylab = "Unique Symbols"
        elif "交易數量" in df4.columns:
            monthly_hold_cnt = df4.groupby("YearMonth")["交易數量"].sum()
            ylab = "Holding Count"
        else:
            monthly_hold_cnt = df4.groupby("YearMonth")["報酬率"].size()
            ylab = "Trades"

        fig_hold = go.Figure(
            data=[
                go.Bar(
                    x=monthly_hold_cnt.index.astype(str),
                    y=monthly_hold_cnt.values,
                    marker_color="slategray",
                    name=ylab,
                    text=[f"{v:,.0f}" for v in monthly_hold_cnt.values],
                    textposition="outside",
                    texttemplate="%{text}",
                    hovertemplate="Period: %{x}<br>"+ylab+": %{y:,.0f}<extra></extra>",
                )
            ]
        )
        fig_hold.update_layout(
            title="📊 Monthly Holding Count",
            xaxis_title="Year-Month",
            yaxis_title=ylab,
            bargap=0.25,
            legend=dict(orientation="h"),
            margin=dict(t=60),
        )
        st.plotly_chart(fig_hold, use_container_width=True)
    else:
        st.info("Please upload a CSV first.")

# ======================= Tab[5] — 📉 報酬風險分布（右尾/左尾、VaR/CVaR、偏態/峰度） =======================
with tabs[5]:
    st.subheader("📉 報酬風險分布（Right/Left Tail, VaR/CVaR, Skew/Kurtosis）")

    # ====== 報酬序列 r 取得（不改任何既有變數）======
    r = st.session_state.get("ret_series", None)

    # 後備 1：若 Summary 已計算過，通常會有「單筆報酬率」
    if r is None and 'df' in locals() and isinstance(df, pd.DataFrame) and "單筆報酬率" in df.columns:
        try:
            r = pd.to_numeric(df["單筆報酬率"], errors="coerce").dropna()
        except Exception:
            r = None

    # 後備 2：找 CSV 內慣用報酬欄位（與 Summary 相同邏輯）
    if r is None and 'df' in locals() and isinstance(df, pd.DataFrame):
        try:
            _cands = [c for c in df.columns if ("報酬" in str(c) and "率" in str(c))]
            _cands += [c for c in df.columns if str(c).lower() in ["return","returns","pct_return","roi","ret"]]
            if len(_cands) > 0:
                _ret_col = _cands[0]
                try:
                    r = normalize_return_series(df[_ret_col]).dropna()
                except NameError:
                    _tmp = (
                        df[_ret_col].astype(str).str.strip()
                          .str.replace("%","",regex=False).str.replace(",","",regex=False)
                    )
                    _tmp = pd.to_numeric(_tmp, errors="coerce")
                    non_na = _tmp.dropna()
                    if len(non_na) and non_na.abs().quantile(0.80) > 1.5 and non_na.abs().quantile(0.20) >= 0.01:
                        _tmp = _tmp / 100.0
                    r = _tmp.dropna()
        except Exception:
            r = None

    # 後備 3：直接由「獲利金額 / 單筆投入」回推
    if r is None and 'df' in locals() and isinstance(df, pd.DataFrame) \
       and all(col in df.columns for col in ["獲利金額","進場價格","交易數量"]) \
       and 'instrument_multiplier' in globals():
        try:
            cost = pd.to_numeric(df["進場價格"], errors="coerce") * \
                   pd.to_numeric(df["交易數量"], errors="coerce") * float(instrument_multiplier)
            r = (pd.to_numeric(df["獲利金額"], errors="coerce") / cost).replace([np.inf, -np.inf], np.nan).dropna()
        except Exception:
            r = None

    # 最終檢查
    # 最終檢查
    if r is None:
        st.warning("找不到可用的報酬序列。請到『📋 Summary 統計』完成讀檔與欄位設定，或確保檔內含「單筆報酬率 / 報酬率 / 獲利金額+投入」。")
        st.stop()


    # ====== 介面控制（沿用同參數）======
    st.markdown("**分析設定**")
    colA, colB, colC = st.columns(3)
    with colA:
        unit_pct = st.checkbox("以百分比顯示", value=True)
    with colB:
        alpha = st.slider("置信水位 α（VaR/CVaR）", 0.80, 0.999, 0.95, 0.01)
    with colC:
        tail_q = st.slider("尾部分位（右/左尾判斷）", 0.80, 0.99, 0.95, 0.01)

    # ====== 基本統計 ======
    r = r.dropna().astype(float)
    mu, sd = float(r.mean()), float(r.std(ddof=0))
    skew = float(r.skew())
    ekurt = float(r.kurt())
    q01, q05, q50, q95, q99 = np.quantile(r, [0.01, 0.05, 0.50, 0.95, 0.99])

    # VaR / CVaR（左尾）
    var_cut = float(np.quantile(r, 1 - alpha))      # 例如 α=0.95 → 左尾 5%
    cvar = float(r[r <= var_cut].mean()) if (r <= var_cut).any() else var_cut

    # 右/左尾
    qL = float(np.quantile(r, 1 - tail_q))
    qR = float(np.quantile(r, tail_q))
    left_tail  = r[r <= qL]
    right_tail = r[r >= qR]

    sum_left  = float(left_tail.sum())
    sum_right = float(right_tail.sum())
    abs_left  = abs(sum_left) if not np.isnan(sum_left) else np.nan
    tail_ratio_sum  = (sum_right / abs_left) if (abs_left and abs_left > 0) else np.nan
    tail_ratio_mean = (right_tail.mean() / abs(left_tail.mean())) if (len(right_tail) and len(left_tail) and left_tail.mean()!=0) else np.nan
    p_left  = len(left_tail)  / len(r)
    p_right = len(right_tail) / len(r)
    p_win = float((r > 0).mean())
    tail_label = "➡️ **右尾較強**（正極端事件貢獻大）" if (pd.notna(tail_ratio_sum) and tail_ratio_sum > 1) else "⬅️ **左尾較強**（負極端事件殺傷大）"

    def _fmt(x):
        return f"{x*100:.2f}%" if unit_pct and pd.notna(x) else f"{x:.4f}"

    # ====== 指標卡 ======
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("勝率 P(r>0)", _fmt(p_win))
    m2.metric("偏態 Skew", f"{skew:.2f}")
    m3.metric("超峰度 Excess Kurtosis", f"{ekurt:.2f}")
    m4.metric(f"Tail Ratio（Σ右尾 / |Σ左尾|, q={tail_q:.2f}）", f"{tail_ratio_sum:.2f}" if pd.notna(tail_ratio_sum) else "NA")
    st.markdown(f"**判讀**：{tail_label}｜VaR/CVaR 以 α={alpha:.2f}，尾部分位界線 q={tail_q:.2f}。")

    # ====== 圖 1：直方圖 + KDE + 重要垂線（百分比模式用 r*100）======
    import matplotlib.pyplot as plt
    import seaborn as sns
    r_vis = (r * 100.0) if unit_pct else r
    mu_vis, var_vis, qL_vis, qR_vis = (mu * (100.0 if unit_pct else 1.0),
                                       var_cut * (100.0 if unit_pct else 1.0),
                                       qL * (100.0 if unit_pct else 1.0),
                                       qR * (100.0 if unit_pct else 1.0))
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(r_vis, bins=50, kde=True, stat="density", ax=ax, color="#4c78a8", alpha=0.55)
    ax.axvline(mu_vis, color="#3c763d", linestyle="--", linewidth=1.5, label=f"均值 { _fmt(mu) }")
    ax.axvline(0.0 if not unit_pct else 0.0, color="#555", linestyle=":", linewidth=1.0, label="0")
    ax.axvline(var_vis, color="#a94442", linestyle="-", linewidth=1.5, label=f"VaR@{alpha:.2f} { _fmt(var_cut) }")
    ax.axvline(qL_vis, color="#ff7f0e", linestyle="--", linewidth=1.0, label=f"左尾界 { _fmt(qL) }")
    ax.axvline(qR_vis, color="#1f77b4", linestyle="--", linewidth=1.0, label=f"右尾界 { _fmt(qR) }")
    ax.set_title("報酬分布（直方圖 + KDE）")
    ax.set_xlabel("報酬（%）" if unit_pct else "報酬")
    ax.set_ylabel("密度")
    ax.legend()
    st.pyplot(fig, use_container_width=True)
  

    # ====== 圖 2：箱型圖 ======
    import plotly.express as px
    df_box = pd.DataFrame({"return": r_vis})
    fig_box = px.box(df_box, y="return", points="outliers", title="箱型圖（含離群值）",
                     labels={"return": f"報酬{'（%）' if unit_pct else ''}"})
    st.plotly_chart(fig_box, use_container_width=True)

    # ====== 表格：VaR / CVaR 與尾部統計 ======
    st.markdown("### 📑 風險統計與尾部摘要（含解讀）")
    tail_rows = [
        ["VaR", f"{alpha:.2f}", _fmt(var_cut), "在 95% 置信水準下的最大可能單期損失（左尾分位）。"],
        ["CVaR", f"{alpha:.2f}", _fmt(cvar), "超過 VaR 的最壞情況下，平均損失。"],
        [f"右尾 Σ(≥q{tail_q:.2f})", "", _fmt(sum_right), "最佳 5% 的極端大賺事件總貢獻。"],
        [f"左尾 Σ(≤q{1-tail_q:.2f})", "", _fmt(sum_left), "最差 5% 的極端大虧事件總損失。"],
        ["Tail Ratio Σ右/|Σ左|", "", f"{tail_ratio_sum:.2f}" if pd.notna(tail_ratio_sum) else "NA", "右尾總貢獻 / 左尾總虧損。"],
        ["Tail Ratio 均值右/|均值左|", "", f"{tail_ratio_mean:.2f}" if pd.notna(tail_ratio_mean) else "NA", "平均每筆右尾大賺 / 平均每筆左尾大虧。"],
        ["右尾樣本占比", "", _fmt(p_right), f"落在右尾的樣本比例（≥q{tail_q:.2f}）。"],
        ["左尾樣本占比", "", _fmt(p_left), f"落在左尾的樣本比例（≤q{1-tail_q:.2f}）。"],
        ["偏態 Skew", "", f"{skew:.2f}", "分布對稱性指標：正值 → 右尾偏厚。"],
        ["超峰度 Excess Kurtosis", "", f"{ekurt:.2f}", "尾部肥厚程度：越大越易出現極端事件。"],
    ]
    tail_df = pd.DataFrame(tail_rows, columns=["指標", "參數", "數值", "解讀"])
    st.dataframe(tail_df, use_container_width=True)

    # ====== 雷達圖（保持你原有指標與命名）======
    st.markdown("### 🕸️ Radar — Opportunity vs Risk (0–1 Normalized)")
    REFS = {"right_sum": 5.0, "tail_ratio": 3.0, "skew": 1.5, "left_sum": 1.0, "var": 0.15, "cvar": 0.20, "kurt": 5.0}
    clip01 = lambda x: float(np.clip(x, 0.0, 1.0))
    opp_right_sum   = clip01((max(0.0, sum_right)) / REFS["right_sum"])
    opp_tail_ratio  = clip01((max(0.0, tail_ratio_sum)) / REFS["tail_ratio"]) if pd.notna(tail_ratio_sum) else 0.0
    opp_skew_pos    = clip01((max(0.0, skew)) / REFS["skew"])
    risk_left_sum   = clip01((abs(min(0.0, sum_left))) / REFS["left_sum"])
    risk_var        = clip01((abs(var_cut)) / REFS["var"])
    risk_cvar       = clip01((abs(cvar)) / REFS["cvar"])
    risk_kurt       = clip01((max(0.0, ekurt)) / REFS["kurt"])
    safe_left_sum = 1.0 - risk_left_sum
    safe_var      = 1.0 - risk_var
    safe_cvar     = 1.0 - risk_cvar
    safe_kurt     = 1.0 - risk_kurt

    opp_df = pd.DataFrame({"axis": ["Right Tail Σ", "Tail Ratio (Σ)", "Positive Skew"],
                           "score": [opp_right_sum, opp_tail_ratio, opp_skew_pos]})
    fig_opp = px.line_polar(opp_df, r="score", theta="axis", line_close=True, range_r=[0,1],
                            title="Opportunity Radar (Right-tail Strength)")
    st.plotly_chart(fig_opp, use_container_width=True)

    risk_df = pd.DataFrame({"axis": ["Left Tail Σ (safe)", "VaR (safe)", "CVaR (safe)", "Kurtosis (safe)"],
                            "score": [safe_left_sum, safe_var, safe_cvar, safe_kurt]})
    fig_risk = px.line_polar(risk_df, r="score", theta="axis", line_close=True, range_r=[0,1],
                             title="Risk Radar (Higher = Safer)")
    st.plotly_chart(fig_risk, use_container_width=True)

    st.caption("說明：雷達圖已正規化至 0–1。Opportunity 越外圈代表右尾（贏家）越強；Risk 雷達為『安全分數=1-風險強度』，越外圈越安全。")

    # ====== 自動判讀（保持你原本邏輯與文案風格）======
    st.markdown("### 🧠 自動判讀")
    comments = []
    if pd.notna(tail_ratio_sum) and tail_ratio_sum > 1.2 and skew > 0:
        comments.append("分布呈 **右尾偏厚**，極端正報酬對整體績效有明顯貢獻；可考慮保留長贏家、避免過早了結。")
    if pd.notna(tail_ratio_sum) and tail_ratio_sum < 0.8 and skew < 0:
        comments.append("分布呈 **左尾偏厚**，負極端事件殺傷較大；建議強化停損、波動度調整或避險模組。")
    if ekurt > 1.0:
        comments.append("**尾部較肥**（Excess Kurtosis > 1）：注意黑天鵝風險，建議加上 MDD/日損上限與縮倉機制。")
    if abs(skew) < 0.2 and (pd.isna(tail_ratio_sum) or abs(tail_ratio_sum-1) < 0.2):
        comments.append("分布 **接近對稱**，右/左尾影響均衡，可著重一般風控（如 ATR/百分比停損）。")
    if not comments:
        comments.append("分布無明顯極端特徵；建議持續監控 VaR/CVaR 與回撤變化，配合持倉動態調整。")
    st.write("• " + "\n• ".join(comments))

    # ====== 純文字摘要 ======
    st.markdown("### 📝 風險／機會 自動解讀")
    as_float = lambda x: (float(x) if pd.notna(x) else np.nan)
    right_sum  = as_float(sum_right)
    left_sum   = as_float(sum_left)
    tratio     = as_float(tail_ratio_sum)
    sk         = as_float(skew)
    kurt       = as_float(ekurt)
    var_v      = as_float(var_cut)
    cvar_v     = as_float(cvar)
    _fmt_pct   = lambda z: ("{:.2f}%".format(z*100) if pd.notna(z) else "NA")
    _fmt2      = lambda z: ("{:.2f}".format(z) if pd.notna(z) else "NA")

    RIGHT_STRONG   = (pd.notna(tratio) and tratio >= 2.0) or (pd.notna(sk) and sk >= 1.0) or (pd.notna(right_sum) and right_sum >= 2.0)
    LEFT_RISK_HIGH = any([
        pd.notna(left_sum) and abs(left_sum) >= 0.8,
        pd.notna(var_v) and abs(var_v) >= 0.12,
        pd.notna(cvar_v) and abs(cvar_v) >= 0.15,
        pd.notna(kurt) and kurt >= 5.0
    ])

    if RIGHT_STRONG:
        c1 = "右尾機會強：少數大贏家對總績效貢獻顯著。"
    else:
        c1 = "右尾機會普通：需提升盈虧不對稱。"

    if LEFT_RISK_HIGH:
        c2 = "左尾風險偏高：VaR/CVaR 或峰度顯示黑天鵝風險需留意。"
    else:
        c2 = "左尾風險可控：極端虧損在合理範圍。"

    if RIGHT_STRONG and LEFT_RISK_HIGH:
        archetype = "右尾驅動、左尾要控（靠贏家，但需嚴控黑天鵝）"
    elif RIGHT_STRONG and not LEFT_RISK_HIGH:
        archetype = "右尾驅動、風險穩健（可逐步放大資金）"
    elif (not RIGHT_STRONG) and LEFT_RISK_HIGH:
        archetype = "機會不足、風險偏高（先優化再上量）"
    else:
        archetype = "均衡（機會與風險皆中性）"

    st.markdown(
        f"""
**一眼結論**
- {c1}
- {c2}
- 策略型態：**{archetype}**

**關鍵指標速覽**
- Tail Ratio Σ右/左：`{_fmt2(tratio)}`
- 右尾 Σ(≥q{tail_q:.2f})：`{_fmt2(right_sum)}` ；左尾 Σ(≤q{1-tail_q:.2f})：`{_fmt2(left_sum)}`
- 偏態 Skew：`{_fmt2(sk)}`
- 超峰度：`{_fmt2(kurt)}`
- VaR@{alpha:.2f}：`{_fmt_pct(var_v)}`；CVaR@{alpha:.2f}：`{_fmt_pct(cvar_v)}`
"""
    )

    # 👉 提供 Tab[6] Markdown 匯出使用的統一鍵值
    st.session_state.update({
        "var_95":  float(np.quantile(r, 0.05)),
        "cvar_95": float(r[r <= np.quantile(r, 0.05)].mean()) if len(r) > 0 else np.nan,
        "skewness": skew,
        "kurtosis": ekurt,
    })


#============================ Tab[6] — 📝 Markdown 匯出（你要的版型） ============================
with _tab(6, "📝 Markdown 匯出"):
    st.subheader("📝 匯出 Markdown 報告（S1 版型）")

    s = st.session_state

    # ---- 基本欄位 ----
    _title     = f"{strategy_name} Backtest – {version}"
    _module    = globals().get("module_name_for_md", strategy_name.split()[0] if strategy_name else "S1")
    _version   = version
    _tag       = "baseline"
    _run_date  = datetime.now().strftime("%Y-%m-%d")
    _start_dt  = s.get("start_date", None)
    _end_dt    = s.get("end_date", None)
    _start_str = (_start_dt.date() if hasattr(_start_dt, "date") else _start_dt) or ""
    _end_str   = (_end_dt.date() if hasattr(_end_dt, "date") else _end_dt) or ""
    _benchmark = "60/40"

    # ---- 日頻報酬與核心指標 ----
    r = s.get("ret_series", pd.Series(dtype=float)).dropna().sort_index()

    # CAGR
    if pd.isna(s.get("geo_apy_from_excel", np.nan)) and len(r) > 1:
        yrs = max((r.index[-1] - r.index[0]).days / 365.25, 1e-9)
        cagr_dec = (float((1 + r).prod()) ** (1.0 / yrs) - 1.0) if yrs > 0 else np.nan
    else:
        cagr_dec = np.nan if pd.isna(s.get("geo_apy_from_excel", np.nan)) else float(s.get("geo_apy_from_excel"))/100.0

    # MDD & Calmar
    mdd_dec = np.nan
    if len(r) > 1:
        nav_tmp = (1.0 + r).cumprod()
        mdd_dec = float((nav_tmp / nav_tmp.cummax() - 1.0).min())
    calmar_v = (cagr_dec / abs(mdd_dec)) if (pd.notna(cagr_dec) and pd.notna(mdd_dec) and mdd_dec < 0) else np.nan

    sharpe_v   = s.get("sharpe_ratio",  np.nan)
    sortino_v  = s.get("sortino_ratio", np.nan)
    winrate    = s.get("win_rate", np.nan)
    trades     = s.get("trade_count", "—")
    turnover   = s.get("turnover", np.nan)

    # ---- 尾部風險 ----
    var95, cvar95 = np.nan, np.nan
    right_sum, left_sum, tail_ratio, skew_v, kurt_v = np.nan, np.nan, np.nan, np.nan, np.nan
    if len(r) > 1:
        q = 0.95
        cutL, cutR = float(np.quantile(r, 1-q)), float(np.quantile(r, q))
        var95  = float(np.quantile(r, 0.05))
        cvar95 = float(r[r <= var95].mean()) if (r <= var95).any() else var95
        left_tail  = r[r <= cutL]; right_tail = r[r >= cutR]
        left_sum   = float(left_tail.sum()) if len(left_tail)  else np.nan
        right_sum  = float(right_tail.sum()) if len(right_tail) else np.nan
        tail_ratio = (right_sum / abs(left_sum)) if (pd.notna(right_sum) and pd.notna(left_sum) and abs(left_sum)>0) else np.nan
        skew_v, kurt_v = float(r.skew()), float(r.kurt())

    # ---- 品質指標 ----
    max_invest_cap = s.get("max_invested_capital", np.nan)
    net_profit     = s.get("net_profit", np.nan)
    win_rate_dec   = float(winrate) if pd.notna(winrate) else np.nan

    avg_profit = s.get("avg_profit", np.nan)
    avg_loss   = s.get("avg_loss", np.nan)
    if (pd.isna(avg_profit) or pd.isna(avg_loss)) and "_df" in globals() and _df is not None and not _df.empty:
        dtmp = _df.copy()
        dtmp["單筆投入"]   = dtmp["進場價格"] * dtmp["交易數量"] * instrument_multiplier
        dtmp["單筆報酬率"] = dtmp["獲利金額"] / dtmp["單筆投入"].replace(0, np.nan)
        avg_profit = float(dtmp.loc[dtmp["獲利金額"] > 0, "獲利金額"].mean()) if (dtmp["獲利金額"] > 0).any() else np.nan
        avg_loss   = float(dtmp.loc[dtmp["獲利金額"] < 0, "獲利金額"].mean()) if (dtmp["獲利金額"] < 0).any() else np.nan
        avg_profit_pct = float(dtmp.loc[dtmp["獲利金額"] > 0, "單筆報酬率"].mean()*100.0) if (dtmp["獲利金額"] > 0).any() else np.nan
        avg_loss_pct   = float(dtmp.loc[dtmp["獲利金額"] < 0, "單筆報酬率"].mean()*100.0) if (dtmp["獲利金額"] < 0).any() else np.nan
        payoff = (avg_profit/abs(avg_loss)) if (pd.notna(avg_profit) and pd.notna(avg_loss) and avg_loss!=0) else np.nan
        kelly  = (win_rate_dec - (1 - win_rate_dec)/payoff) if (pd.notna(win_rate_dec) and pd.notna(payoff) and payoff>0) else np.nan
        kelly50 = (kelly/2.0) if pd.notna(kelly) else np.nan
        ev_amt = (net_profit / trades) if (pd.notna(net_profit) and isinstance(trades, int) and trades>0) else np.nan
        max_inv_roi = ((net_profit / max_invest_cap) * 100.0) if (pd.notna(net_profit) and pd.notna(max_invest_cap) and max_invest_cap>0) else np.nan
    else:
        avg_profit_pct = s.get("avg_profit_pct", np.nan)
        avg_loss_pct   = s.get("avg_loss_pct",   np.nan)
        payoff = (avg_profit/abs(avg_loss)) if (pd.notna(avg_profit) and pd.notna(avg_loss) and avg_loss!=0) else np.nan
        kelly  = (win_rate_dec - (1 - win_rate_dec)/payoff) if (pd.notna(win_rate_dec) and pd.notna(payoff) and payoff>0) else np.nan
        kelly50 = (kelly/2.0) if pd.notna(kelly) else np.nan
        ev_amt = (net_profit / trades) if (pd.notna(net_profit) and isinstance(trades, int) and trades>0) else np.nan
        max_inv_roi = ((net_profit / max_invest_cap) * 100.0) if (pd.notna(net_profit) and pd.notna(max_invest_cap) and max_invest_cap>0) else np.nan

    # ---- 基準比較（同期間） ----
    strat_curve_full = s.get("strat_curve_full", None)
    bench_syms = ["SPY", "VOO", "006208.TW"]
    bench_cmp = {}

    def _safe(fmt, v, suffix=""):
        return "—" if pd.isna(v) else (fmt.format(v) + suffix)

    if strat_curve_full is not None and hasattr(strat_curve_full, "index") and len(strat_curve_full) > 10:
        start_dt = strat_curve_full.index.min()
        end_dt   = strat_curve_full.index.max()
        try:
            raw = yf.download(bench_syms, start=start_dt, end=end_dt + pd.Timedelta(days=1),
                              auto_adjust=True, progress=False, group_by="column")
            close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) and "Close" in raw.columns.get_level_values(0) else raw.iloc[:, 0]

            for sym in bench_syms:
                try:
                    srs = pd.to_numeric(close[sym] if isinstance(close, pd.DataFrame) else close, errors="coerce").dropna()
                except Exception:
                    continue
                if srs.empty:
                    continue

                idx = pd.date_range(max(strat_curve_full.first_valid_index(), srs.index.min()), end_dt, freq="D")
                sc  = strat_curve_full.reindex(idx).ffill().bfill()
                bc  = srs.reindex(idx).ffill().bfill()
                scN = sc / sc.iloc[0]
                bcN = bc / bc.iloc[0]

                rets_b = bcN.pct_change().dropna()
                rets_s = scN.pct_change().dropna()

                days   = (idx[-1] - idx[0]).days
                yrs    = max(days/365.25, 1e-9)
                cagr_b = (bcN.iloc[-1] / bcN.iloc[0])**(1/yrs) - 1 if yrs>0 else np.nan
                cagr_s = (scN.iloc[-1] / scN.iloc[0])**(1/yrs) - 1 if yrs>0 else np.nan

                dd_b   = (bcN / bcN.cummax() - 1.0).min()
                dd_s   = (scN / scN.cummax() - 1.0).min()
                cal_b  = (cagr_b / abs(dd_b)) if (pd.notna(cagr_b) and pd.notna(dd_b) and dd_b<0) else np.nan
                cal_s  = (cagr_s / abs(dd_s)) if (pd.notna(cagr_s) and pd.notna(dd_s) and dd_s<0) else np.nan

                def _ann_sharpe(x):
                    if len(x) < 2: 
                        return np.nan
                    std = float(x.std(ddof=1))
                    mu  = float(x.mean())
                    return (mu/std*np.sqrt(252.0)) if std>0 else np.nan
                sharpe_b = _ann_sharpe(rets_b)
                sharpe_s_aligned = _ann_sharpe(rets_s)

                bench_cmp[sym] = {
                    "cagr_b": cagr_b, "cagr_s": cagr_s, "delta_cagr": (cagr_s - cagr_b) if (pd.notna(cagr_s) and pd.notna(cagr_b)) else np.nan,
                    "cal_b":  cal_b,  "cal_s":  cal_s,  "delta_cal":  (cal_s  - cal_b)  if (pd.notna(cal_s)  and pd.notna(cal_b))  else np.nan,
                    "mdd_b":  dd_b,   "mdd_s":  dd_s,   "delta_mdd":  (dd_s   - dd_b)   if (pd.notna(dd_s)   and pd.notna(dd_b))   else np.nan,
                    "sharpe_b": sharpe_b, "sharpe_s": sharpe_s_aligned,
                    "delta_sharpe": (sharpe_s_aligned - sharpe_b) if (pd.notna(sharpe_s_aligned) and pd.notna(sharpe_b)) else np.nan,
                    "beat_cagr": (cagr_s > cagr_b) if (pd.notna(cagr_s) and pd.notna(cagr_b)) else False,
                    "beat_cal":  (cal_s  > cal_b)  if (pd.notna(cal_s)  and pd.notna(cal_b))  else False,
                }
        except Exception:
            pass

    def _beat_str(sym):
        d = bench_cmp.get(sym, {})
        c1 = "✅" if d.get("beat_cagr", False) else "❌"
        c2 = "✅" if d.get("beat_cal",  False) else "❌"
        return f"{sym}：{c1} CAGR、{c2} Calmar"

    def _beat_str_details(sym):
        d = bench_cmp.get(sym, {})
        if not d:
            return f"{sym}：—"
        cagr_s = d.get("cagr_s", np.nan); cagr_b = d.get("cagr_b", np.nan); dc = d.get("delta_cagr", np.nan)
        cal_s  = d.get("cal_s",  np.nan); cal_b  = d.get("cal_b",  np.nan);  dl = d.get("delta_cal",  np.nan)
        mdd_s  = d.get("mdd_s",  np.nan); mdd_b  = d.get("mdd_b",  np.nan);  dm = d.get("delta_mdd",  np.nan)
        shp_s  = d.get("sharpe_s", np.nan); shp_b = d.get("sharpe_b", np.nan); ds = d.get("delta_sharpe", np.nan)

        part1 = f"CAGR { _safe('{:.2f}', (cagr_s*100.0), '%') } vs { _safe('{:.2f}', (cagr_b*100.0), '%') } ({ _safe('{:+.2f}', (dc*100.0), 'ppt') })"
        part2 = f"Calmar { _safe('{:.2f}', cal_s) } vs { _safe('{:.2f}', cal_b) } ({ _safe('{:+.2f}', dl) })"
        part3 = f"MDD { _safe('{:.1f}', (mdd_s*100.0), '%') } vs { _safe('{:.1f}', (mdd_b*100.0), '%') } ({ _safe('{:+.1f}', (dm*100.0), 'ppt') })"
        part4 = f"Sharpe { _safe('{:.2f}', shp_s) } vs { _safe('{:.2f}', shp_b) } ({ _safe('{:+.2f}', ds) })"
        return f"{sym}｜{part1} ｜ {part2} ｜ {part3} ｜ {part4}"

    # ---- 前置 YAML（Obsidian 版）----
    # ---- 前置 YAML（Obsidian 版；中英雙 key）----
    fm_lines = [
        "---",
        f'title: "{_title}"',
        "type: backtest",
        f"module: {_module}",
        f"version: {_version}",
        "tags: [backtest, baseline]",
        f"run_date: {_run_date}",
        f"start_date: {_start_str}",
        f"end_date: {_end_str}",

        # ===== 核心績效指標 =====
        f"kelly_full: {0 if pd.isna(kelly_full) else round(float(kelly_full), 4)}",
        f"凱利公式_Kelly: {0 if pd.isna(kelly_full) else round(float(kelly_full), 4)}",

        f"cagr: {0 if pd.isna(cagr_dec) else round(float(cagr_dec), 4)}",
        f"年化報酬率_CAGR: {0 if pd.isna(cagr_dec) else round(float(cagr_dec), 4)}",

        f"sharpe: {'' if pd.isna(sharpe_v) else format(float(sharpe_v), '.2f')}",
        f"夏普比率_Sharpe: {'' if pd.isna(sharpe_v) else format(float(sharpe_v), '.2f')}",

        f"sortino: {'' if pd.isna(sortino_v) else format(float(sortino_v), '.2f')}",
        f"索提諾比率_Sortino: {'' if pd.isna(sortino_v) else format(float(sortino_v), '.2f')}",

        f"mdd: {'' if pd.isna(mdd_dec) else format(float(mdd_dec), '.4f')}",
        f"最大回撤_MDD: {'' if pd.isna(mdd_dec) else format(float(mdd_dec), '.4f')}",

        f"calmar: {'' if pd.isna(calmar_v) else format(float(calmar_v), '.2f')}",
        f"卡瑪比率_Calmar: {'' if pd.isna(calmar_v) else format(float(calmar_v), '.2f')}",

        f"win_rate: {'' if pd.isna(winrate) else format(float(winrate), '.4f')}",
        f"勝率_WinRate: {'' if pd.isna(winrate) else format(float(winrate), '.4f')}",

        f"trades: {trades}",
        f"交易數量_Trades: {trades}",



        # ===== 你新增的四個指標（英 + 中）=====
        f"net_profit: {'' if pd.isna(net_profit) else round(float(net_profit), 2)}",
        f"淨利_$: {'' if pd.isna(net_profit) else round(float(net_profit), 2)}",

        f"avg_profit_pct: {'' if pd.isna(avg_profit_pct) else round(float(avg_profit_pct), 2)}",
        f"平均獲利_%: {'' if pd.isna(avg_profit_pct) else round(float(avg_profit_pct), 2)}",

        f"avg_loss_pct: {'' if pd.isna(avg_loss_pct) else round(float(avg_loss_pct), 2)}",
        f"平均損失_%: {'' if pd.isna(avg_loss_pct) else round(float(avg_loss_pct), 2)}",

        f"ev_pct: {'' if (pd.isna(ev_amt) or pd.isna(max_invest_cap) or max_invest_cap==0) else round((float(ev_amt)/float(max_invest_cap)*100), 2)}",
        f"期望值EV_%: {'' if (pd.isna(ev_amt) or pd.isna(max_invest_cap) or max_invest_cap==0) else round((float(ev_amt)/float(max_invest_cap)*100), 2)}",

        # ===== 可選百分比欄位（純數值，無 % 符號；英 + 中）=====
        f"cagr_pct: {'' if pd.isna(cagr_dec) else round(float(cagr_dec)*100, 2)}",
        f"年化報酬率_CAGR%: {'' if pd.isna(cagr_dec) else round(float(cagr_dec)*100, 2)}",

        f"mdd_pct: {'' if pd.isna(mdd_dec) else round(float(mdd_dec)*100, 2)}",
        f"最大回撤_MDD%: {'' if pd.isna(mdd_dec) else round(float(mdd_dec)*100, 2)}",

        f"win_rate_pct: {'' if pd.isna(winrate) else round(float(winrate)*100, 2)}",
        f"勝率_WinRate%: {'' if pd.isna(winrate) else round(float(winrate)*100, 2)}",


        "---",   # ← 結束 YAML
        "",
    ]

    # ---- Summary 與文字版比較 ----
    summary_lines = [
        "# 📊 Summary",
        f"* 區間：{_start_str} → {_end_str}（回測於 { _run_date }）",
        f"* 成果：CAGR **{0 if pd.isna(cagr_dec) else int(round(cagr_dec*100,0))}%**",
        f"* Sharpe **{'' if pd.isna(sharpe_v) else format(sharpe_v, '.1f')}**，"
        f"MDD **{'' if pd.isna(mdd_dec) else format(mdd_dec*100, '.0f')}%**，"
        f"Calmar **{'' if pd.isna(calmar_v) else format(calmar_v, '.1f')}**，"
        f"勝率 **{'' if pd.isna(winrate) else format(winrate*100, '.0f')}%**，"
        f"交易數 **{trades}**",
        "* 是否贏過基準（CAGR / Calmar）",
        "",
        f"  * {_beat_str('SPY')}",
        f"  * {_beat_str('VOO')}",
        f"  * {_beat_str('006208.TW')}",
        "",
        "## 📊 與基準數值對照表（同期間）",
    ]

    # ---- 表格渲染（同期間：Strategy vs Benchmark 以及差值） ----
    table_header = [
        "| 基準 | CAGR_S | CAGR_B | ΔCAGR(ppt) | Calmar_S | Calmar_B | ΔCalmar | MDD_S | MDD_B | ΔMDD(ppt) | Sharpe_S | Sharpe_B | ΔSharpe |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    table_rows = []
    for sym in ["SPY", "VOO", "006208.TW"]:
        d = bench_cmp.get(sym, {})
        cagr_s = d.get("cagr_s", np.nan); cagr_b = d.get("cagr_b", np.nan); dc = d.get("delta_cagr", np.nan)
        cal_s  = d.get("cal_s",  np.nan); cal_b  = d.get("cal_b",  np.nan);  dl = d.get("delta_cal",  np.nan)
        mdd_s  = d.get("mdd_s",  np.nan); mdd_b  = d.get("mdd_b",  np.nan);  dm = d.get("delta_mdd",  np.nan)
        shp_s  = d.get("sharpe_s", np.nan); shp_b = d.get("sharpe_b", np.nan); ds = d.get("delta_sharpe", np.nan)

        row = "| {sym} | {cagr_s} | {cagr_b} | {dc} | {cal_s} | {cal_b} | {dl} | {mdd_s} | {mdd_b} | {dm} | {shp_s} | {shp_b} | {ds} |".format(
            sym=sym,
            cagr_s=_safe("{:.2f}", (cagr_s*100.0), "%"),
            cagr_b=_safe("{:.2f}", (cagr_b*100.0), "%"),
            dc=_safe("{:+.2f}", (dc*100.0), "ppt"),
            cal_s=_safe("{:.2f}", cal_s, ""),
            cal_b=_safe("{:.2f}", cal_b, ""),
            dl=_safe("{:+.2f}", dl, ""),
            mdd_s=_safe("{:.1f}", (mdd_s*100.0), "%"),
            mdd_b=_safe("{:.1f}", (mdd_b*100.0), "%"),
            dm=_safe("{:+.1f}", (dm*100.0), "ppt"),
            shp_s=_safe("{:.2f}", shp_s, ""),
            shp_b=_safe("{:.2f}", shp_b, ""),
            ds=_safe("{:+.2f}", ds, ""),
        )
        table_rows.append(row)

    bench_table_md = "\n".join(table_header + (table_rows if table_rows else ["| — | — | — | — | — | — | — | — | — | — | — | — | — |"]))

    # ---- 其餘區塊 ----
    tail_lines = [
        "",
        "## ⚙️ 核心品質指標",
        "",
        f"* 品質：勝率 **{'' if pd.isna(winrate) else format(winrate*100, '.0f')}%**，交易數 **{trades}**，換手率 **{'' if pd.isna(turnover) else format(float(turnover)*100, '.0f')}%**",
         f"* 淨利 ($)：**{ '—' if pd.isna(net_profit) else f'${net_profit:,.0f}' }**",
        f"* 最大投入金額 ($)：**{ '—' if pd.isna(max_invest_cap) else f'${max_invest_cap:,.0f}' }**",
        f"* 最大投入報酬率 (%)：**{ '—' if pd.isna(max_inv_roi) else f'{max_inv_roi:.2f}%' }**",
        f"* 勝率 (%)：**{ '' if pd.isna(winrate) else f'{winrate*100:.2f}%' }**",
        f"* 賺賠比：**{ '—' if (pd.isna(avg_profit) or pd.isna(avg_loss) or avg_loss==0) else f'{(avg_profit/abs(avg_loss)):.2f}' }**",
        f"* 期望值（$）：**{ '—' if pd.isna(ev_amt) else f'${ev_amt:,.0f}' }**",
        f"* 平均每筆報酬 (%)：**{ '—' if pd.isna(avg_profit_pct) else f'{avg_profit_pct:.2f}%' }**",
        f"* Kelly 值 (50%)：**{ '—' if pd.isna(kelly50) else f'{kelly50:.4f}' }**",
        f"* 平均獲利 (%)：**{ '—' if pd.isna(avg_profit_pct) else f'{avg_profit_pct:.2f}%' }**",
        f"* 平均損失 (%)：**{ '—' if pd.isna(avg_loss_pct) else f'{avg_loss_pct:.2f}%' }**",
        f"* 期望值 EV (%)：**{ '—' if pd.isna(ev_amt) or pd.isna(max_invest_cap) else f'{(ev_amt/max_invest_cap*100):.2f}%' }**",
        "",
        "### 平均獲利與虧損",
        "",
        "| 指標 | 數值 |",
        "| --- | --- |",
        f"| 平均獲利 | { '—' if pd.isna(avg_profit) else f'{avg_profit:,.0f}' } |",
        f"| 平均虧損 | { '—' if pd.isna(avg_loss)   else f'{avg_loss:,.0f}' } |",
        "",
        "## 📑 風險統計與尾部摘要（含解讀）",
        "",
        "| 指標 | 參數 | 數值 | 解讀 |  |  |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| VaR | 95% | { '' if pd.isna(var95) else f'{var95*100:.2f}%' } | 在 95% 置信水準下的最大可能單期損失（左尾分位）。 |  |  |",
        f"| CVaR | 95% | { '' if pd.isna(cvar95) else f'{cvar95*100:.2f}%' } | 超過 VaR 的最壞情況下，平均損失。 |  |  |",
        f"| 右尾 Σ(≥q0.95) |  | { '' if pd.isna(right_sum) else f'{right_sum*100:.1f}%' } |最佳 5% 的極端大賺事件總貢獻。 |  |  |",
        f"| 左尾 Σ(≤q0.05) |  | { '' if pd.isna(left_sum)  else f'{left_sum*100:.1f}%' } | 最差 5% 的極端大虧事件總損失。|  |  |",
        f"| Tail Ratio Σ右/ | Σ左 |  |  | { '' if pd.isna(tail_ratio) else f'{tail_ratio:.2f}' } | 正尾總貢獻大於負尾 |",
        f"| 偏態 Skew |  | { '' if pd.isna(skew_v) else f'{skew_v:.2f}' } | 分布偏右，正極端貢獻大 |  |  |",
        f"| 超峰度 Excess Kurtosis |  | { '' if pd.isna(kurt_v) else f'{kurt_v:.2f}' } | 尾部肥厚程度：越大越易出現極端事件。 |  |  |",
    ]

    # ---- 組合 Markdown ----
    md_text = "\n".join(fm_lines + summary_lines + [bench_table_md] + tail_lines)

    # === Tab6：把 Tab5 存好的圖插入到 Markdown（Obsidian 圖片語法） ===
    md_text += "\n\n## 📊 報酬分布圖\n"



    # ---- 顯示與下載 ----
    st.code(md_text, language="markdown")
    st.download_button(
        "⬇️ 下載 Markdown",
        data=md_text.encode("utf-8"),
        file_name=f"{strategy_name}_{version}_report.md",
        mime="text/markdown",
        key=f"md_export::{strategy_name}::{version}::S1_template"
    )



