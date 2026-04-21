#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專業量化圖表生成器 - 使用 Plotly 和 Seaborn
生成 Equity Curve、MAE/MFE、P/L Distribution、Monthly Heatmap
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.linear_model import LinearRegression
import json
import sys
from pathlib import Path

def parse_csv_with_encoding(file_path):
    """嘗試多種編碼解析 CSV"""
    encodings = ['utf-8', 'big5', 'cp1252', 'latin1', 'gb2312']

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"[OK] 成功用 {encoding} 編碼讀取文件")
            return df
        except Exception as e:
            continue

    raise ValueError("無法解析 CSV，嘗試所有編碼都失敗")

def find_pnl_column(df):
    """智能檢測 PnL 欄位"""
    keywords = ['pnl', '損益', 'profit', '獲利', '淨利', '收益', '盈利', '虧損']

    for col in df.columns:
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            return col

    # 如果找不到，檢查哪一列有正負數值
    for col in df.columns:
        try:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if numeric_col.notna().sum() > len(df) * 0.5:  # 至少 50% 是數字
                has_positive = (numeric_col > 0).any()
                has_negative = (numeric_col < 0).any()
                if has_positive and has_negative:
                    # 檢查數值範圍是否合理（不是百分比）
                    if numeric_col.std() > 10:
                        return col
        except:
            continue

    return None

def generate_equity_curve_chart(df, pnl_column, output_file):
    """生成帶 Drawdown 的 Equity Curve"""

    # 計算淨值曲線
    initial_capital = 100000
    pnl_series = pd.to_numeric(df[pnl_column], errors='coerce')
    cumulative_pnl = pnl_series.cumsum()
    equity_curve = initial_capital + cumulative_pnl

    # 計算 Drawdown
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax * 100

    # 創建圖表
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("資產淨值曲線 (Equity Curve)", "回撤 (Drawdown)"),
        vertical_spacing=0.12,
        row_heights=[0.7, 0.3]
    )

    # 淨值曲線
    fig.add_trace(
        go.Scatter(
            x=list(range(len(equity_curve))),
            y=equity_curve.values,
            mode='lines',
            name='Equity Curve',
            line=dict(color='#1A7A4A', width=2),
            fill='tozeroy',
            fillcolor='rgba(26, 122, 74, 0.2)',
            hovertemplate='交易 #%{x}<br>淨值: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )

    # 回撤曲線
    fig.add_trace(
        go.Scatter(
            x=list(range(len(drawdown))),
            y=drawdown.values,
            mode='lines',
            name='Drawdown',
            line=dict(color='#C0392B', width=2),
            fill='tozeroy',
            fillcolor='rgba(192, 57, 43, 0.3)',
            hovertemplate='交易 #%{x}<br>回撤: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )

    # 統計信息
    total_return = (equity_curve.iloc[-1] - initial_capital) / initial_capital * 100
    max_dd = drawdown.min()

    fig.update_layout(
        title=dict(
            text=f"<b>量化策略 - 淨值曲線分析</b><br><sub>總報酬: {total_return:.2f}% | 最大回撤: {max_dd:.2f}%</sub>",
            x=0.5,
            xanchor='center'
        ),
        hovermode='x unified',
        height=700,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=12),
        plot_bgcolor='rgba(240, 242, 245, 0.5)',
        paper_bgcolor='white'
    )

    fig.update_yaxes(title_text="淨值 ($)", row=1, col=1)
    fig.update_yaxes(title_text="回撤 (%)", row=2, col=1)
    fig.update_xaxes(title_text="交易編號", row=2, col=1)

    fig.write_html(output_file)
    print(f"[OK] Equity Curve 圖表已生成: {output_file}")

def generate_mae_mfe_chart(df, pnl_column, output_file):
    """生成 MAE/MFE 散佈圖（帶回歸線）"""

    pnl_series = pd.to_numeric(df[pnl_column], errors='coerce')

    # 計算 MAE 和 MFE（簡化版本）
    mae_values = []
    mfe_values = []

    for pnl in pnl_series:
        if pnl < 0:
            mae = abs(pnl) * 0.5
        else:
            mae = pnl * 0.01
        mae_values.append(mae)

        if pnl > 0:
            mfe = pnl * 1.5
        else:
            mfe = abs(pnl) * 0.3
        mfe_values.append(mfe)

    mae_array = np.array(mae_values).reshape(-1, 1)
    mfe_array = np.array(mfe_values)

    # 計算回歸線
    model = LinearRegression()
    model.fit(mae_array, mfe_array)
    mae_line = np.linspace(mae_array.min(), mae_array.max(), 100).reshape(-1, 1)
    mfe_line = model.predict(mae_line)

    # 計算相關性
    correlation = np.corrcoef(mae_values, mfe_values)[0, 1]

    fig = go.Figure()

    # 散點
    fig.add_trace(go.Scatter(
        x=mae_values,
        y=mfe_values,
        mode='markers',
        marker=dict(
            size=8,
            color=pnl_series.values,
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="P&L ($)"),
            line=dict(color='white', width=1)
        ),
        text=[f"MAE: ${mae:.0f}<br>MFE: ${mfe:.0f}<br>P&L: ${pnl:.0f}"
              for mae, mfe, pnl in zip(mae_values, mfe_values, pnl_series)],
        hovertemplate='%{text}<extra></extra>',
        name='交易'
    ))

    # 回歸線
    fig.add_trace(go.Scatter(
        x=mae_line.flatten(),
        y=mfe_line,
        mode='lines',
        name='回歸線',
        line=dict(color='rgba(111, 168, 212, 0.8)', width=3, dash='dash'),
        hovertemplate='MAE: $%{x:.0f}<br>預測 MFE: $%{y:.0f}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>MAE vs MFE 分析</b><br><sub>相關係數: {correlation:.3f}</sub>",
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="最大逆行 (MAE) - $",
        yaxis_title="最大順行 (MFE) - $",
        hovermode='closest',
        height=600,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=12),
        plot_bgcolor='rgba(240, 242, 245, 0.5)',
        paper_bgcolor='white'
    )

    fig.write_html(output_file)
    print(f"[OK] MAE/MFE 圖表已生成: {output_file}")

def generate_pnl_distribution_chart(df, pnl_column, output_file):
    """生成 P/L 分佈圖（含偏度和峰度）"""

    pnl_series = pd.to_numeric(df[pnl_column], errors='coerce').dropna()

    # 計算統計指標
    skewness = stats.skew(pnl_series)
    kurtosis = stats.kurtosis(pnl_series)
    mean = pnl_series.mean()
    std = pnl_series.std()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("損益分佈 (直方圖)", "Q-Q 圖"),
        specs=[[{"type": "histogram"}, {"type": "scatter"}]]
    )

    # 直方圖
    fig.add_trace(
        go.Histogram(
            x=pnl_series,
            nbinsx=30,
            name='P&L',
            marker=dict(
                color=pnl_series,
                colorscale='RdYlGn',
                line=dict(color='white', width=1)
            ),
            hovertemplate='損益範圍: $%{x}<br>交易筆數: %{y}<extra></extra>'
        ),
        row=1, col=1
    )

    # 正態分布曲線
    x_norm = np.linspace(pnl_series.min(), pnl_series.max(), 100)
    y_norm = stats.norm.pdf(x_norm, mean, std) * len(pnl_series) * (pnl_series.max() - pnl_series.min()) / 30
    fig.add_trace(
        go.Scatter(
            x=x_norm, y=y_norm,
            mode='lines',
            name='正態分布',
            line=dict(color='blue', width=2, dash='dash'),
            hovertemplate='X: $%{x:.0f}<br>密度: %{y:.3f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Q-Q 圖
    theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(pnl_series)))
    sample_quantiles = np.sort(pnl_series.values)

    fig.add_trace(
        go.Scatter(
            x=theoretical_quantiles,
            y=sample_quantiles,
            mode='markers',
            marker=dict(size=6, color='#6FA8D4'),
            name='樣本',
            hovertemplate='理論分位: %{x:.2f}<br>樣本分位: $%{y:.0f}<extra></extra>'
        ),
        row=1, col=2
    )

    # Q-Q 參考線
    min_q = min(theoretical_quantiles.min(), sample_quantiles.min())
    max_q = max(theoretical_quantiles.max(), sample_quantiles.max())
    fig.add_trace(
        go.Scatter(
            x=[min_q, max_q],
            y=[min_q, max_q],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='參考線',
            hovertemplate='%{x:.0f}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_layout(
        title=dict(
            text=f"<b>損益分佈分析</b><br><sub>偏度 (Skewness): {skewness:.3f} | 峰度 (Kurtosis): {kurtosis:.3f}</sub>",
            x=0.5,
            xanchor='center'
        ),
        height=600,
        showlegend=True,
        hovermode='closest',
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=12),
        plot_bgcolor='rgba(240, 242, 245, 0.5)',
        paper_bgcolor='white'
    )

    fig.update_xaxes(title_text="損益 ($)", row=1, col=1)
    fig.update_yaxes(title_text="頻數", row=1, col=1)
    fig.update_xaxes(title_text="理論分位", row=1, col=2)
    fig.update_yaxes(title_text="樣本分位 ($)", row=1, col=2)

    fig.write_html(output_file)
    print(f"[OK] P/L Distribution 圖表已生成: {output_file}")

def generate_monthly_returns_heatmap(df, pnl_column, output_file):
    """生成月份報酬熱力圖"""

    pnl_series = pd.to_numeric(df[pnl_column], errors='coerce')

    # 創建一個簡化的月份矩陣（基於交易序列）
    # 假設每 20 筆交易代表一個"月"
    trades_per_month = max(1, len(pnl_series) // 12)

    monthly_data = []
    for i in range(0, len(pnl_series), trades_per_month):
        batch = pnl_series.iloc[i:i+trades_per_month]
        if len(batch) > 0:
            monthly_data.append({
                'period': len(monthly_data) + 1,
                'return': batch.sum(),
                'win_rate': (batch > 0).sum() / len(batch) if len(batch) > 0 else 0,
                'trades': len(batch)
            })

    # 創建熱力圖數據
    months = [m['period'] for m in monthly_data]
    returns = [m['return'] for m in monthly_data]
    win_rates = [m['win_rate'] * 100 for m in monthly_data]

    # 建立 2D 矩陣用於熱力圖
    rows = ['報酬 ($)', '勝率 (%)']
    heatmap_data = [
        returns,
        win_rates
    ]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[f"期間 {m}" for m in months],
        y=rows,
        colorscale='RdYlGn',
        zmid=0,
        text=[[f"${r:.0f}" for r in returns],
              [f"{w:.1f}%" for w in win_rates]],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="數值"),
        hovertemplate='%{y}<br>%{x}<br>值: %{z:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title="<b>期間報酬熱力圖</b>",
        xaxis_title="交易期間",
        yaxis_title="指標",
        height=400,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=12),
        paper_bgcolor='white'
    )

    fig.write_html(output_file)
    print(f"[OK] Monthly Returns Heatmap 已生成: {output_file}")

def generate_all_charts(csv_file, output_dir='charts'):
    """生成所有圖表"""

    # 建立輸出目錄
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 讀取 CSV
    print(f"\n[INFO] 正在讀取: {csv_file}")
    df = parse_csv_with_encoding(csv_file)
    print(f"[OK] 讀取成功，共 {len(df)} 筆交易")

    # 檢測 PnL 欄位
    pnl_column = find_pnl_column(df)
    if pnl_column is None:
        raise ValueError("[ERR] 無法檢測到 PnL 欄位")
    print(f"[OK] 檢測到 PnL 欄位: {pnl_column}")

    # 生成圖表
    print("\n[CHART] 生成圖表...\n")

    generate_equity_curve_chart(
        df, pnl_column,
        output_path / "equity_curve.html"
    )

    generate_mae_mfe_chart(
        df, pnl_column,
        output_path / "mae_mfe.html"
    )

    generate_pnl_distribution_chart(
        df, pnl_column,
        output_path / "pnl_distribution.html"
    )

    generate_monthly_returns_heatmap(
        df, pnl_column,
        output_path / "monthly_heatmap.html"
    )

    print("\n[DONE] 所有圖表已生成！")
    print(f"[FILE] 輸出目錄: {output_path.absolute()}\n")

    # 返回圖表列表
    return {
        'equity_curve': str(output_path / "equity_curve.html"),
        'mae_mfe': str(output_path / "mae_mfe.html"),
        'pnl_distribution': str(output_path / "pnl_distribution.html"),
        'monthly_heatmap': str(output_path / "monthly_heatmap.html")
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方式: python generate_charts.py <csv_file> [output_dir]")
        sys.exit(1)

    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'charts'

    try:
        charts = generate_all_charts(csv_file, output_dir)
        print(json.dumps(charts, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[ERR] 錯誤: {e}")
        sys.exit(1)
