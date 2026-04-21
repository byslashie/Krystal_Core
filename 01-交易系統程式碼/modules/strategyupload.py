import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO

st.set_page_config(layout="wide")
st.title("📈 Strategy Performance Dashboard")

# --------------------------- Sidebar Input ---------------------------
st.sidebar.subheader("🧮 商品乘數設定")
instrument_type = st.sidebar.selectbox("請選擇商品類型", ["個股", "指數", "個股期貨"])
instrument_multiplier = {"個股": 1000, "指數": 50, "個股期貨": 2000}[instrument_type]

strategy_name = st.text_input("策略名稱", value="目前回測策略")
version = st.text_input("版本號", value="v1.0")
strategy_desc = st.text_area("策略描述", value="範例策略描述")
execution_freq = st.selectbox("執行頻率", ["日內", "波段", "長期"])
optimize_focus = st.text_input("優化方向", value="停損設計、風險控制")
upload_time = datetime.now().strftime("%Y-%m-%d %H:%M")

# --------------------------- Google Sheets Setup ---------------------------
SHEET_NAME = " Krystal 總經 × 策略 × AI 自動化交易系統｜策略紀錄"
SHEET_TAB = "回測績效寫入"
CREDENTIAL_PATH = "D:/2025_Krystal_AI_Tool/2025_06_23_Krystal_AI_Trading_System/Krystal_AI_Trading_System/key/strategy-performance.json"
def append_to_google_sheet(dataframe):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_file(CREDENTIAL_PATH, scopes=scope)
        gc = gspread.authorize(credentials)
        sh = gc.open(SHEET_NAME)
        try:
            sheet = sh.worksheet(SHEET_TAB)
        except:
            sheet = sh.add_worksheet(title=SHEET_TAB, rows="100", cols="20")
            sheet.append_row(list(dataframe.columns))
        existing_rows = sheet.get_all_values()
        existing_names = [row[0] for row in existing_rows[1:]]
        if strategy_name not in existing_names:
            row = [x.item() if hasattr(x, 'item') else str(x) for x in dataframe.iloc[0]]
            sheet.append_row(row)
            st.success("✅ 成功新增策略績效至 Google Sheets!")
        else:
            st.warning("⚠️ 此策略名稱已存在於總表中，請確認是否重複上傳。")
    except Exception as e:
        st.error(f"❌ Google Sheets 寫入失敗：{e}")

# --------------------------- File Upload ---------------------------
uploaded_file = st.file_uploader("📄 請上傳策略績效 CSV 檔案", type=["csv"])

# --------------------------- Tabs ---------------------------
tabs = st.tabs(["📊 績效圖表總覽", "🧠 AI 策略建議", "🔬 策略診斷", "📋 Summary 統計"])

# --------------------------- Summary Tab ---------------------------
with tabs[3]:
    st.subheader("📋 Summary 經效分析（分區顯示）")

    def show_metric_section(title, rows, color="white"):
        st.markdown(f"<div style='background-color:{color}; padding:8px; border-radius:6px'><b>{title}</b></div>", unsafe_allow_html=True)
        df_section = pd.DataFrame(rows, columns=["指標名稱", "數值", "解釋與重要性", "計算公式"])
        st.dataframe(df_section, use_container_width=True)

    

    if uploaded_file:
        try:
            stringio = StringIO(uploaded_file.getvalue().decode("cp950"))
        except UnicodeDecodeError:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio)


        df["出場時間"] = pd.to_datetime(df["出場時間"], errors="coerce")
        df["進場時間"] = pd.to_datetime(df["進場時間"], errors="coerce")
        df["進場價格"] = pd.to_numeric(df["進場價格"], errors="coerce")
        df["出場價格"] = pd.to_numeric(df["出場價格"], errors="coerce")
        df["獲利金額"] = pd.to_numeric(df["獲利金額"], errors="coerce")
        df["交易數量"] = pd.to_numeric(df["交易數量"], errors="coerce")
        df = df.dropna().sort_values("出場時間")

        cumulative_profit = df["獲利金額"].cumsum()
        rolling_max = cumulative_profit.cummax()
        drawdown = cumulative_profit - rolling_max

        def find_mdd_intervals_no_overlap(cum_profit, top_n=3):
            drawdowns = []
            used_ranges = []
            for i in range(1, len(cum_profit)):
                peak_idx = cum_profit[:i+1].idxmax()
                subset = cum_profit[peak_idx:]
                if subset.empty:
                    continue
                try:
                    trough_idx = subset.idxmin()
                except ValueError:
                    continue
                if peak_idx >= trough_idx:
                    continue
                overlap = any(peak_idx <= r[1] and trough_idx >= r[0] for r in used_ranges)
                if overlap:
                    continue
                dd_value = cum_profit[trough_idx] - cum_profit[peak_idx]
                dd_pct = dd_value / cum_profit[peak_idx] * 100 if cum_profit[peak_idx] != 0 else 0
                drawdowns.append((dd_value, dd_pct, peak_idx, trough_idx))
                used_ranges.append((peak_idx, trough_idx))
            return sorted(drawdowns, key=lambda x: x[0])[:top_n]

        mdd_top3 = find_mdd_intervals_no_overlap(cumulative_profit)

        gross_profit = df[df["獲利金額"] > 0]["獲利金額"].sum()
        gross_loss = df[df["獲利金額"] < 0]["獲利金額"].sum()
        net_profit = df["獲利金額"].sum()
        profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else np.nan
        win_rate = (df["獲利金額"] > 0).mean()
        loss_rate = 1 - win_rate
        trade_count = len(df)
        max_profit_trade = df["獲利金額"].max()
        max_loss_trade = df["獲利金額"].min()
        avg_holding_days = (df["出場時間"] - df["進場時間"]).dt.days.mean()
        avg_profit = df[df["獲利金額"] > 0]["獲利金額"].mean()
        avg_loss = df[df["獲利金額"] < 0]["獲利金額"].mean()
        max_drawdown_value = mdd_top3[0][0] if mdd_top3 else 0
        max_drawdown_pct = mdd_top3[0][1] if mdd_top3 else 0
        max_invested_capital = df[["進場價格", "出場價格"]].max(axis=1).mul(instrument_multiplier).max()
        max_investment_return_rate = net_profit / max_invested_capital * 100

        backtest_days = (df["出場時間"].max() - df["出場時間"].min()).days + 1
        arithmetic_apy = (max_investment_return_rate / 100) / backtest_days * 365 * 100
        start_date = df["出場時間"].min()
        end_date = df["出場時間"].max()
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + end_date.day / 30
        geo_apy = ((1 + max_investment_return_rate / 100) ** (1 / months)) ** 12 - 1 if months > 0 else np.nan
        geo_apy *= 100

        annual_trade_count = trade_count / (backtest_days / 365)

        expected_value = net_profit / trade_count if trade_count else 0
        avg_return_ratio = expected_value / max_invested_capital * 100
        avg_profit_ratio = avg_profit / max_invested_capital * 100
        avg_loss_ratio = avg_loss / max_invested_capital * 100

        try:
            daily_returns = df.groupby(df["出場時間"].dt.date)["獲利金額"].sum()
            daily_returns.index = pd.to_datetime(daily_returns.index)
            std_daily = daily_returns.std()
            sharpe_ratio = (daily_returns.mean() / std_daily) * np.sqrt(252) if std_daily > 0 else np.nan
            downside_std = daily_returns[daily_returns < 0].std()
            sortino_ratio = (daily_returns.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else np.nan
        except:
            sharpe_ratio, sortino_ratio = np.nan, np.nan

        reward_risk_ratio = avg_profit / abs(avg_loss) if avg_loss != 0 else np.nan
        kelly_full = np.nan
        if reward_risk_ratio and reward_risk_ratio != 0:
            kelly_full = ((win_rate - loss_rate / reward_risk_ratio) / reward_risk_ratio)
        kelly_half = kelly_full / 2 if pd.notna(kelly_full) else np.nan
        kelly_half = kelly_full / 2 if kelly_full else np.nan

        # 分區統計區塊呈現
        show_metric_section("🟢【整體經效核心指標】★ 最重要", [
            ["淨利 ($)", f"${net_profit:,.0f}", "最直觀的策略總獲利，評估絕對績效", "總收益 - 總損失"],
            ["最大區間回撤 ($)", f"${max_drawdown_value:,.0f}", "策略最大回撤金額，衡量風險程度", "最大累積損失"],
            ["最大投入金額 ($)", f"${max_invested_capital:,.0f}", "策略期間最大持倉成本，用於評估報酬率與風控", "最大持倉價格 × 乘數"],
            ["最大投入報酬率 (%)", f"{max_investment_return_rate:.2f}%", "資金使用效率評估", "淨利 / 最大投入資金"],
            ["幾何年化報酬率 (%)", f"{geo_apy:.2f}%", "反映長期複利的成效", "年複利報酬"],
            ["算術平均報酬率 (%)", f"{arithmetic_apy:.2f}%", "簡化平均年化報酬率，短期比較用", "最大投入報酬率 / 天數 * 365"],
            ["風報比", f"{net_profit / abs(max_drawdown_value):.2f}", "風險報酬平衡指標", "淨利 / 最大回撤"],
            ["Kelly 資金配置比例 (%)", f"{kelly_full * 100:.2f}%", "追求最大長期報酬的理論最適投入比例", "(勝率 - 敗率 / 賺賠比) / 賺賠比"],
        ])

        show_metric_section("🟡【報酬組織與風控能力】★ 中高度重要", [
            ["Sharpe 比率", f"{sharpe_ratio:.2f}", "風險調整後報酬能力", "平均日報酬 / 波動率"],
            ["Sortino 比率", f"{sortino_ratio:.2f}", "僅考慮下行風險的報酬能力", "平均日報酬 / 下行波動率"],
            ["獲利因子", f"{profit_factor:.2f}", "利潤與虧損的比例關係", "總獲利 / 總虧損"],
            ["最大單次虧損 ($)", f"${max_loss_trade:,.0f}", "單筆最大風險損失", "最大虧損交易"],
            ["最大單次獲利 ($)", f"${max_profit_trade:,.0f}", "單筆最高獲利表現", "最大獲利交易"],
        ])

        show_metric_section("🔹【交易品質與勁效特徵】★ 中等重要", [
            ["勝率 (%)", f"{win_rate * 100:.2f}%", "整體勝率表現", "獲利次數 / 總交易數"],
            ["賺賠比", f"{reward_risk_ratio:.2f}", "平均獲利對平均虧損的比例", "平均獲利 / 平均虧損"],
            ["期望值 ($)", f"${expected_value:,.0f}", "平均每筆交易預期收益", "總淨利 / 交易次數"],
            ["平均每筆報酬 (%)", f"{avg_return_ratio:.2f}%", "平均交易報酬率", "期望值 / 最大投入"],
            ["Kelly 值 (50%)", f"{kelly_half:.2f}", "資金分配建議參考", "Kelly 全額值 / 2"],
        ])

        show_metric_section("🟣【獲利與損失表現】★ 中度參考", [
            ["平均獲利 ($)", f"${avg_profit:,.0f}", "每筆獲利平均表現", "正報酬平均"],
            ["平均虧損 ($)", f"${avg_loss:,.0f}", "每筆虧損平均表現", "負報酬平均"],
            ["平均獲利 (%)", f"{avg_profit_ratio:.2f}%", "相對投入的報酬", "平均獲利 / 最大投入"],
            ["平均虧損 (%)", f"{avg_loss_ratio:.2f}%", "相對投入的損失", "平均虧損 / 最大投入"],
            ["獲利總額 ($)", f"${gross_profit:,.0f}", "所有正交易加總", "獲利總和"],
        ])

        show_metric_section("🔶【交易頻率與持倉特性】★ 可優化", [
            ["總交易次數", f"{trade_count}", "整體樣本數", "資料長度"],
            ["年均交易數", f"{annual_trade_count:.1f}", "平均每年出手次數", "總交易數 / 年數"],
            ["平均持倉時間 (天)", f"{avg_holding_days:.2f}", "交易週期長短", "出場 - 進場 天數平均"],
            ["算術平均 APY (%)", f"{arithmetic_apy:.2f}%", "簡化版年報酬率", "最大投入報酬 / 回測天數 * 365"],
            ["最大投入資金 ($)", f"${max_invested_capital:,.0f}", "用於報酬/風險計算的基礎", "報酬基準"],
        ])

        # 📤 匯出至 Google Sheets
        # 📤 匯出所有統計數值至 Google Sheets（欄位攤平）
        full_summary_data = {
            "策略名稱": strategy_name,
            "版本號": version,
            "上線時間": upload_time,
            "回測期間": f"{start_date.date()} ~ {end_date.date()}",
            "商品": instrument_type,
            "描述": strategy_desc,
            "淨利 ($)": net_profit,
            "最大區間回撤 ($)": max_drawdown_value,
            "最大投入金額 ($)": max_invested_capital,
            "最大投入報酬率 (%)": max_investment_return_rate,
            "幾何年化報酬率 (%)": geo_apy,
            "算術平均報酬率 (%)": arithmetic_apy,
            "風報比": net_profit / abs(max_drawdown_value) if max_drawdown_value else np.nan,
            "Kelly 資金配置比例 (%)": kelly_full * 100 if kelly_full else np.nan,
            "Sharpe 比率": sharpe_ratio,
            "Sortino 比率": sortino_ratio,
            "獲利因子": profit_factor,
            "最大單次虧損 ($)": max_loss_trade,
            "最大單次獲利 ($)": max_profit_trade,
            "勝率 (%)": win_rate * 100,
            "賺賠比": reward_risk_ratio,
            "期望值 ($)": expected_value,
            "平均每筆報酬 (%)": avg_return_ratio,
            "Kelly 值 (50%)": kelly_half,
            "平均獲利 ($)": avg_profit,
            "平均虧損 ($)": avg_loss,
            "平均獲利 (%)": avg_profit_ratio,
            "平均虧損 (%)": avg_loss_ratio,
            "獲利總額 ($)": gross_profit,
            "總交易次數": trade_count,
            "年均交易數": annual_trade_count,
            "平均持倉時間 (天)": avg_holding_days,
        }

        full_summary_df = pd.DataFrame([full_summary_data])  # 單筆資料 → 一行

        if st.button("📤 寫入 Google Sheets 分區統計表"):
            append_to_google_sheet(full_summary_df)


# --------------------------- Interactive Chart ---------------------------
with tabs[0]:
    if uploaded_file:
        st.subheader("📊 Cumulative Return Curve with Interactive Drawdown Visualization")
        fig = go.Figure()

        # 累積報酬線
        fig.add_trace(go.Scatter(
            x=df["出場時間"],
            y=cumulative_profit,
            mode="lines",
            name="累積報酬",
            line=dict(color="blue")
        ))

        # 回撤區間曲線
        fig.add_trace(go.Scatter(
            x=df["出場時間"],
            y=drawdown,
            fill="tozeroy",
            name="回撤",
            opacity=0.3,
            line=dict(color="red")
        ))

        # 前三大 MDD 區間標註
        for i, (value, pct, start_idx, end_idx) in enumerate(mdd_top3, 1):
            start_date = df.iloc[start_idx]["出場時間"]
            end_date = df.iloc[end_idx]["出場時間"]
            mid_date = start_date + (end_date - start_date) / 2

            # 加入底色區塊
            fig.add_vrect(
                x0=start_date,
                x1=end_date,
                fillcolor=f"rgba({max(0, 255 - i*50)}, 0, {min(255, i*50)}, 0.15)",
                opacity=0.25,
                line_width=0,
                annotation_text=f"MDD #{i}",
                annotation_position="top left"
            )

            # 中間文字標註
            fig.add_annotation(
                x=mid_date,
                y=cumulative_profit.min(),
                text=f"MDD #{i}<br>${value:,.0f} ({pct:.2f}%)",
                showarrow=False,
                font=dict(size=12),
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="gray",
                borderwidth=1,
                borderpad=4
            )

        fig.update_traces(hovertemplate="時間: %{x|%Y-%m-%d}<br>金額: %{y:,.0f}")
        fig.update_layout(
            title="📉 Cumulative Return with Drawdown Zones",
            xaxis_title="出場時間",
            yaxis_title="累積報酬",
            hovermode="x unified"
        )

        st.plotly_chart(fig)

        # MDD 區間文字說明
        st.markdown("🔻 **前三大 MDD 區間資訊**")
        for i, (value, pct, start_idx, end_idx) in enumerate(mdd_top3, 1):
            start_date = df.iloc[start_idx]["出場時間"].date()
            end_date = df.iloc[end_idx]["出場時間"].date()
            st.markdown(f"💰 MDD #{i}（報酬基準）: {start_date} ~ {end_date} ｜ ${value:,.0f} ({pct:.2f}%)")

    else:
        st.warning("請先上傳 CSV 檔案以檢視統計結果。")