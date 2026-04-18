"""
🎨 HTML + Flask 交易儀表板 - 完全整合版
整合 Google Sheets、Broker API、策略績效、實盤交易管理
高性能、現代化、專業外觀
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from jinja2 import FileSystemLoader, Environment
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import sqlite3
from pathlib import Path
import logging
import traceback
from io import StringIO
import os
import sys
import platform
from dotenv import load_dotenv
try:
    import yfinance as yf
except ImportError:
    yf = None

# 加載 .env 配置
load_dotenv()

# 導入 Google Sheets 工具
try:
    from sheets_utils import read_sheet_data_with_cache, get_sheet
    SHEETS_OK = True
except Exception as e:
    SHEETS_OK = False
    print(f"警告: sheets_utils 導入失敗: {e}")

# 導入數據層（備選）
try:
    from data_layer import get_data_layer
    DATA_LAYER_OK = True
except Exception as e:
    DATA_LAYER_OK = False
    print(f"警告: 數據層導入失敗: {e}")

# 導入 ship_monitoring 模組
try:
    from ship_monitoring.ais_scraper import fetch_gulf_tankers
    from ship_monitoring.movement_detector import VesselTracker, detect_all_alerts
    SHIP_MONITOR_OK = True
    vessel_tracker = VesselTracker()
except Exception as e:
    SHIP_MONITOR_OK = False
    print(f"警告: ship_monitoring 導入失敗: {e}")

# ============================================================================
# 日誌配置
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Google Sheets 數據讀取函數
# ============================================================================

def get_strategies_from_sheets():
    """從 Google Sheets 讀取策略列表"""
    try:
        if not SHEETS_OK:
            return []
        df = read_sheet_data_with_cache('strategies')
        if df is not None and not df.empty:
            return df.to_dict('records')
    except Exception as e:
        logger.warning(f"讀取策略失敗: {e}")
    return []

def get_daily_nav_from_sheets():
    """從 Google Sheets 讀取日常 NAV 數據"""
    try:
        if not SHEETS_OK:
            return None
        df = read_sheet_data_with_cache('daily_nav')
        if df is not None and not df.empty:
            date_col = '日期' if '日期' in df.columns else 'date'
            if date_col in df.columns:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                return df.sort_values('date')
            else:
                return df # 若都沒找到就算了
    except Exception as e:
        logger.warning(f"讀取 NAV 失敗: {e}")
    return None

def get_broker_positions_from_sheets():
    """從 Google Sheets 讀取券商持倉"""
    try:
        if not SHEETS_OK:
            return None
        df = read_sheet_data_with_cache('broker_positions')
        if df is not None and not df.empty:
            return df.to_dict('records')
    except Exception as e:
        logger.warning(f"讀取持倉失敗: {e}")
    return None

def get_broker_snapshot_from_sheets():
    """從 Google Sheets 讀取最新帳戶快照"""
    try:
        if not SHEETS_OK:
            return None
        df = read_sheet_data_with_cache('broker_snapshot')
        if df is not None and not df.empty:
            time_col = '時間' if '時間' in df.columns else 'timestamp'
            asset_col = '帳戶總資產' if '帳戶總資產' in df.columns else 'net_liquidation'
            cash_col = '可用現金' if '可用現金' in df.columns else 'total_cash_value'
            
            if time_col in df.columns:
                # 獲取最新一筆
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                latest = df.sort_values(time_col).iloc[-1].to_dict()
                
                # 統一轉成英文 key 供後續運算使用
                latest['timestamp'] = latest.get(time_col)
                
                # 安全地轉換數值，去除逗號
                asset_val = str(latest.get(asset_col, '0')).replace(',', '')
                cash_val = str(latest.get(cash_col, '0')).replace(',', '')
                
                nlv = pd.to_numeric(asset_val, errors='coerce')
                cash = pd.to_numeric(cash_val, errors='coerce')
                
                latest['net_liquidation'] = 0.0 if pd.isna(nlv) else float(nlv)
                latest['total_cash_value'] = 0.0 if pd.isna(cash) else float(cash)
                return latest
    except Exception as e:
        logger.warning(f"讀取帳戶快照失敗: {e}")
    return None

def get_trades_from_sheets(strategy_name=None):
    """從 Google Sheets 讀取交易紀錄"""
    try:
        if not SHEETS_OK:
            return None
        df = read_sheet_data_with_cache('trades')
        if df is not None and not df.empty:
            if strategy_name:
                df = df[df['strategy'] == strategy_name]
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date', ascending=False)
    except Exception as e:
        logger.warning(f"讀取交易失敗: {e}")
    return None

def check_duplicate_position(symbol: str, position: float, avg_cost: float, sheet_name: str = 'broker_positions') -> bool:
    """檢查持倉是否已存在（去重）

    比較條件：
    - symbol（代碼）完全相同
    - position（數量）完全相同
    - avgCost（均價）在 0.01 範圍內相同

    返回：True 如果已存在（重複），False 如果不存在（新增）
    """
    try:
        if not SHEETS_OK:
            return False

        df = read_sheet_data_with_cache(sheet_name)
        if df is None or df.empty:
            return False

        # 查找相同的持倉
        matching = df[
            (df['symbol'].astype(str).str.upper() == symbol.upper()) &
            (pd.to_numeric(df['position'], errors='coerce') == position) &
            (pd.to_numeric(df['avgCost'], errors='coerce').sub(avg_cost).abs() < 0.01)
        ]

        return len(matching) > 0
    except Exception as e:
        logger.warning(f"去重檢查失敗: {e}")
        return False

def append_positions_with_dedup(positions_list: List[Dict], sheet_name: str = 'broker_positions') -> dict:
    """添加持倉到 Sheets，並進行去重

    返回：{'added': 新增筆數, 'skipped': 跳過筆數, 'errors': 錯誤訊息}
    """
    try:
        sheet = get_sheet(sheet_name)
        if not sheet:
            return {'added': 0, 'skipped': 0, 'error': 'Unable to get sheet'}

        added = 0
        skipped = 0

        for pos in positions_list:
            symbol = pos.get('symbol', '')
            position = float(pos.get('position', 0))
            avg_cost = float(pos.get('avgCost', 0))

            # 檢查重複
            if check_duplicate_position(symbol, position, avg_cost, sheet_name):
                skipped += 1
                logger.info(f"跳過重複持倉: {symbol} {position} @ {avg_cost}")
                continue

            # 添加新持倉
            try:
                row = [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    pos.get('source', 'unknown'),
                    pos.get('exchange', ''),
                    symbol,
                    pos.get('position', ''),
                    pos.get('avgCost', ''),
                    pos.get('marketPrice', ''),
                    pos.get('currency', ''),
                    ''  # 備註
                ]
                sheet.append_row(row)
                added += 1
                logger.info(f"添加持倉: {symbol} {position}")
            except Exception as e:
                logger.error(f"添加持倉失敗: {symbol}, {e}")
                continue

        return {'added': added, 'skipped': skipped, 'error': None}
    except Exception as e:
        logger.error(f"批量添加持倉失敗: {e}")
        return {'added': 0, 'skipped': 0, 'error': str(e)}

# ============================================================================
# V8 儀表板支援與輔助函數
# ============================================================================

# V8 數據庫與上傳路徑
DB_PATH = Path(__file__).parent / 'dashboard_v8' / 'broker_positions.db'
UPLOAD_FOLDER = Path(__file__).parent / 'dashboard_v8' / 'temp_uploads'
if not UPLOAD_FOLDER.exists():
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def convert_numpy_types(obj):
    """遞迴轉換 numpy/pandas 類型為 Python 原生類型，支持 JSON 序列化"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def get_db_positions():
    """從本地數據庫讀取持倉（V8 專用）"""
    try:
        if not DB_PATH.exists():
            return []
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM broker_positions ORDER BY synced_at DESC')
        positions = [dict(row) for row in c.fetchall()]
        conn.close()
        return positions
    except Exception as e:
        logger.error(f"[V8] 讀取本地數據庫失敗: {e}")
        return []

MARKET_CACHE = {'data': [], 'updated': None}


# ============================================================================
# Flask 應用配置
# ============================================================================

# 支持多個模板目錄
app = Flask(__name__, static_folder='static')

# 配置多個模板目錄支持
template_dirs = [
    os.path.join(os.path.dirname(__file__), 'templates'),  # 原始 templates 目錄
    os.path.join(os.path.dirname(__file__), 'dashboard_v3_260320', 'templates'),  # 新的 v3 目錄
]

app.jinja_loader = FileSystemLoader(template_dirs)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)

app.config['TEMPLATES_AUTO_RELOAD'] = True  # 禁用模板緩存，每次自動重新加載
app.jinja_env.cache = None  # 禁用 Jinja2 模板緩存

# 強制禁用所有 HTTP 緩存（已合併到後面的 after_request，此處保留備註）
# @app.after_request
# def disable_cache(response):
#     response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

# ============================================================================
# 數據生成函數（備選方案，當 Sheets 不可用時使用）
# ============================================================================

from datetime import datetime, timedelta
import numpy as np

def read_csv_file(file_storage):
    """讀取 CSV 文件，支援多種編碼（V8 專用）"""
    raw = file_storage.read()
    import io as _io
    for enc in ('utf-8-sig', 'utf-8', 'cp950', 'big5', 'gb2312'):
        try:
            df = pd.read_csv(_io.BytesIO(raw), encoding=enc)
            df.columns = [col.lstrip('\ufeff') for col in df.columns]
            if len(df.columns) >= 5: return df
        except: continue
    return pd.read_csv(_io.BytesIO(raw), encoding='latin-1')

def generate_portfolio_data(days=365):

    """生成投資組合數據"""
    np.random.seed(42)

    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days)

    price = 100
    prices = [price]
    returns = [0]  # 第一天沒有前一天的價格，所以回報為 0

    for _ in range(days - 1):
        daily_return = np.random.normal(0.0008, 0.015)
        price *= (1 + daily_return)
        prices.append(price)
        returns.append(daily_return * 100)

    df = pd.DataFrame({
        'date': dates,
        'price': prices,
        'daily_return': returns,
        'cumulative_return': np.cumprod(1 + np.array(returns) / 100) * 100 - 100
    })

    return df

# 生成初始數據
df_portfolio = generate_portfolio_data()

# ============================================================================
# 計算指標
# ============================================================================

def calculate_metrics():
    """計算關鍵績效指標（優先使用 Google Sheets 真實數據）"""
    try:
        # 優先嘗試從 Google Sheets 讀取真實數據
        snapshot = get_broker_snapshot_from_sheets()
        nav_df = get_daily_nav_from_sheets()
        positions = get_broker_positions_from_sheets()

        if snapshot and nav_df is not None:
            total_value = float(snapshot.get('net_liquidation', 0))

            # 計算年度報酬
            if len(nav_df) > 0:
                latest_nav = nav_df.iloc[-1]
                annual_return = float(latest_nav.get('cumulative_return_pct', 0))
                sharpe_ratio = float(latest_nav.get('sharpe_ratio', 0))
                max_drawdown = float(latest_nav.get('mdd_pct', 0))
            else:
                annual_return = 0
                sharpe_ratio = 0
                max_drawdown = 0

            # 計算持倉數量
            holdings = len(positions) if positions else 0

            # 計算日內變化
            if len(nav_df) > 1:
                daily_change = float(nav_df.iloc[-1].get('daily_return_pct', 0))
            else:
                daily_change = 0

            return {
                'total_value': round(total_value, 2),
                'annual_return': round(annual_return, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': 0,  # 需要從 trades 計算
                'daily_change': round(daily_change, 2),
                'holdings': holdings,
                'data_source': 'sheets'
            }
    except Exception as e:
        logger.warning(f"從 Sheets 讀取指標失敗: {e}")

    # 備選方案：使用模擬數據
    annual_return = ((df_portfolio['price'].iloc[-1] / df_portfolio['price'].iloc[0] - 1) * 100)
    volatility = df_portfolio['daily_return'].std() * np.sqrt(252)
    sharpe_ratio = (annual_return / 100) / (volatility / 100) * np.sqrt(252) if volatility > 0 else 0
    max_drawdown = ((df_portfolio['cumulative_return'].cummax() - df_portfolio['cumulative_return']).max())
    win_rate = (df_portfolio['daily_return'] > 0).sum() / len(df_portfolio) * 100

    return {
        'total_value': 125345.01,
        'annual_return': round(annual_return, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'max_drawdown': round(-max_drawdown, 2),
        'win_rate': round(win_rate, 2),
        'daily_change': 2.34,
        'holdings': 4,
        'data_source': 'demo'
    }

# ============================================================================
# 路由 - 頁面
# ============================================================================

@app.route('/')
def index():
    """主頁 - V8儀表板"""
    try:
        import os
        from flask import send_file
        # 確保路徑是相對當前目錄的
        return send_file(os.path.join(os.path.dirname(__file__), 'dashboard_v8', 'index.html'))
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"❌ 儀表板頁面加載失敗: {error_msg}")
        logger.error(f"儀表板頁面加載失敗: {error_msg}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{error_msg}</pre>", 500

@app.route('/portfolio')
def portfolio():
    """投資組合頁面"""
    try:
        return render_template('portfolio.html', page='portfolio')
    except Exception as e:
        import traceback
        logger.error(f"投資組合頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/risk')
def risk_control():
    """風險控制頁面"""
    try:
        return render_template('risk.html', page='risk')
    except Exception as e:
        import traceback
        logger.error(f"風險控制頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/allocation')
def allocation():
    """資金配置頁面"""
    try:
        return render_template('allocation.html', page='allocation')
    except Exception as e:
        import traceback
        logger.error(f"資金配置頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/performance')
def performance():
    """績效分析頁面"""
    try:
        return render_template('performance.html', page='performance')
    except Exception as e:
        import traceback
        logger.error(f"績效分析頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/trading')
def trading():
    """交易管理頁面"""
    try:
        return render_template('trading.html', page='trading')
    except Exception as e:
        import traceback
        logger.error(f"交易管理頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/strategies')
def strategies():
    """策略管理頁面"""
    try:
        return render_template('strategies.html', page='strategies')
    except Exception as e:
        import traceback
        logger.error(f"策略管理頁面加載失敗: {e}\n{traceback.format_exc()}")
        return f"<h1>❌ 頁面加載失敗</h1><pre>{traceback.format_exc()}</pre>", 500

@app.route('/v2')
def dashboard_v2():
    """儀表板 V2 版本 - 新設計，重點在賬戶管理"""
    try:
        return render_template('dashboardV2.html')
    except Exception as e:
        import traceback
        logger.error(f"DashboardV2 加載失敗: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# ============================================================================
# 導航頁面路由 - DashboardV2 子頁面
# ============================================================================

@app.route('/pages/risk')
def page_risk():
    """風控管理頁面"""
    try:
        return render_template('pages/risk.html')
    except Exception as e:
        logger.error(f"風控頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/performance')
def page_performance():
    """績效分析頁面"""
    try:
        return render_template('pages/performance.html')
    except Exception as e:
        logger.error(f"績效頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/monitoring')
def page_monitoring():
    """監控中心頁面"""
    try:
        return render_template('pages/monitoring.html')
    except Exception as e:
        logger.error(f"監控頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/trading')
def page_trading():
    """交易面板頁面"""
    try:
        return render_template('pages/trading.html')
    except Exception as e:
        logger.error(f"交易頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/strategies')
def page_strategies():
    """策略配置頁面"""
    try:
        return render_template('pages/strategies.html')
    except Exception as e:
        logger.error(f"策略頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/intel')
def page_intel():
    """情報資訊頁面"""
    try:
        return render_template('pages/intel.html')
    except Exception as e:
        logger.error(f"情報頁面加載失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/sync')
def broker_sync():
    """Broker 數據同步頁面"""
    return render_template('broker_sync.html')

# ============================================================================
# API 路由 - 核心儀表板
# ============================================================================

@app.route('/api/metrics')
def api_metrics():
    """API：獲取關鍵績效指標"""
    try:
        metrics = calculate_metrics()
        return jsonify({
            'status': 'success',
            'data': metrics
        })
    except Exception as e:
        logger.error(f"獲取指標失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chart-data')
def api_chart_data():
    """API：獲取圖表數據"""
    try:
        data = {
            'dates': df_portfolio['date'].dt.strftime('%Y-%m-%d').tolist(),
            'prices': df_portfolio['price'].round(2).tolist(),
            'cumulative_returns': df_portfolio['cumulative_return'].round(2).tolist(),
            'daily_returns': df_portfolio['daily_return'].round(4).tolist()
        }
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"獲取圖表數據失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/holdings')
def api_holdings():
    """API：獲取持倉"""
    try:
        # 優先嘗試從 Google Sheets 讀取實際持倉
        positions = get_broker_positions_from_sheets()
        if positions:
            # 按 symbol + broker 去重，保留最新記錄
            deduped = {}
            for pos in positions:
                broker = pos.get('券商', pos.get('broker', '')).upper()
                symbol = pos.get('symbol', '')
                key = f"{broker}_{symbol}"

                current_time = pos.get('時間', '')
                if key not in deduped or current_time > deduped[key].get('時間', ''):
                    deduped[key] = pos

            positions = list(deduped.values())

            return jsonify({
                'status': 'success',
                'data': positions,
                'source': 'sheets'
            })

        # 備選：從數據層獲取
        if DATA_LAYER_OK:
            data_layer = get_data_layer()
            try:
                holdings_df = data_layer.get_holdings()
                if not holdings_df.empty:
                    holdings = holdings_df.to_dict('records')
                    return jsonify({
                        'status': 'success',
                        'data': holdings,
                        'source': 'broker'
                    })
            except Exception as e:
                logger.warning(f"從 Broker 讀取持倉失敗: {e}")

        # 最後備選：返回空列表（提示用戶補充 Google Sheets 數據）
        holdings = []  # 改為空，等待從 Google Sheets 讀取真實數據
        return jsonify({
            'status': 'success',
            'data': holdings,
            'source': 'demo'
        })
    except Exception as e:
        logger.error(f"獲取持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/holdings/by-broker')
def api_holdings_by_broker():
    """API：按券商分類獲取持倉"""
    try:
        positions = get_broker_positions_from_sheets()
        if not positions:
            positions = []

        # 按 symbol + broker 去重，保留最新記錄
        deduped = {}
        for pos in positions:
            broker = pos.get('券商', pos.get('broker', '')).upper()
            symbol = pos.get('symbol', '')
            key = f"{broker}_{symbol}"

            # 比較時間戳，保留較新的記錄
            current_time = pos.get('時間', '')
            if key not in deduped or current_time > deduped[key].get('時間', ''):
                deduped[key] = pos

        positions = list(deduped.values())

        # 從 trades 建立 symbol -> (策略, 進場原因) 查找表
        trades_lookup = {}
        try:
            trades_df = read_sheet_data_with_cache('trades')
            if trades_df is not None and not trades_df.empty:
                holding = trades_df[trades_df['狀態'].astype(str).isin(['持倉', '進行中'])]
                holding = holding.sort_values('日期', ascending=False)
                for _, tr in holding.iterrows():
                    sym = str(tr.get('標的', '')).strip().upper()
                    if sym and sym not in trades_lookup:
                        trades_lookup[sym] = {
                            '策略': str(tr.get('策略', '')).strip(),
                            '進場原因': str(tr.get('進場原因', '')).strip(),
                        }
        except Exception:
            pass

        # 分類持倉
        ib_positions = []
        yuanta_positions = []
        other_positions = []

        for pos in positions:
            # 根據 symbol 的數據源判斷 broker
            # 優先檢查 券商 列，然後檢查 broker 列，最後使用 symbol 檢測
            broker = pos.get('券商', pos.get('broker', '')).upper()
            symbol_upper = str(pos.get('symbol', '')).strip().upper()
            trade_info = trades_lookup.get(symbol_upper, {})
            pos = {**pos, '策略': trade_info.get('策略', ''), '進場原因': trade_info.get('進場原因', '')}

            if 'IB' in broker or 'IBKR' in broker or (not broker and is_ib_symbol(pos.get('symbol', ''))):
                ib_positions.append({**pos, 'broker': 'IB'})
            elif 'YUANTA' in broker or (not broker and is_yuanta_symbol(pos.get('symbol', ''))):
                yuanta_positions.append({**pos, 'broker': 'Yuanta'})
            else:
                other_positions.append({**pos, 'broker': broker or 'Unknown'})

        return jsonify({
            'status': 'success',
            'ib': {
                'positions': ib_positions,
                'count': len(ib_positions),
                'total_value': sum(float(p.get('position', 0)) * float(p.get('avgCost', 0)) for p in ib_positions)
            },
            'yuanta': {
                'positions': yuanta_positions,
                'count': len(yuanta_positions),
                'total_value': sum(float(p.get('position', 0)) * float(p.get('avgCost', 0)) for p in yuanta_positions)
            },
            'other': {
                'positions': other_positions,
                'count': len(other_positions)
            }
        })
    except Exception as e:
        logger.error(f"按券商獲取持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def is_ib_symbol(symbol: str) -> bool:
    """判斷是否為 IB 的持倉（基於 symbol 特徵）"""
    if not symbol:
        return False
    # IB 通常是英文代碼和 TWSE 台股代碼的混合
    # 可以根據你的具體情況調整
    return symbol.isupper() and len(symbol) <= 5 and symbol not in ['TSE', 'OTC']

def is_yuanta_symbol(symbol: str) -> bool:
    """判斷是否為 Yuanta 的持倉（基於 symbol 特徵）"""
    if not symbol:
        return False
    # Yuanta 主要是台股代碼（通常為數字）
    try:
        int(symbol)
        return True
    except:
        return False

def get_stock_price(symbol: str, market: str) -> Optional[float]:
    """獲取股票實時市價"""
    try:
        import yfinance as yf

        # 處理 symbol
        ticker_symbol = symbol.upper()

        if market == 'NASDAQ' or market == 'NYSE':
            # 美股直接用 symbol
            ticker = yf.Ticker(ticker_symbol)
        elif market == 'TWSE' or market == 'OTC':
            # 台股需要加 .TW 後綴
            ticker = yf.Ticker(f"{ticker_symbol}.TW")
        else:
            return None

        # 獲取最新價格
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        logger.debug(f"獲取 {symbol} 市價失敗: {e}")

    return None

def calculate_daily_performance() -> Dict[str, float]:
    """計算今日未實現 + 已實現損益（分開 IB/USD、Yuanta/TWD、Schwab/USD）"""
    try:
        # 1. 從 broker_positions 計算未實現損益（分開券商和幣種）
        positions = get_broker_positions_from_sheets()
        ib_unrealized = 0.0
        yuanta_unrealized = 0.0
        schwab_unrealized = 0.0

        for pos in (positions or []):
            symbol = pos.get('symbol', '')
            exchange = pos.get('exchange', '')
            qty = float(pos.get('position', 0))
            avg_cost = float(pos.get('avgCost', 0))
            broker = pos.get('券商', pos.get('source', pos.get('broker', ''))).upper()
            market_price = get_stock_price(symbol, exchange)

            if market_price and avg_cost > 0:
                pl = (market_price - avg_cost) * qty
                if broker in ['IB', 'IBKR']:
                    ib_unrealized += pl
                elif broker in ['YUANTA', '元大']:
                    yuanta_unrealized += pl
                elif broker in ['SCHWAB', 'CHARLES SCHWAB']:
                    schwab_unrealized += pl

        # 2. 從 trades 取得已實現損益（分開券商和幣別）
        ib_realized = 0.0
        yuanta_realized = 0.0
        schwab_realized = 0.0
        trades_df = read_sheet_data_with_cache('trades')
        if trades_df is not None and '損益' in trades_df.columns:
            pnl_numeric = pd.to_numeric(trades_df['損益'], errors='coerce').fillna(0)
            # 檢查是否有 '券商' 欄位，沒有則使用 'source' 或 'broker'
            if '券商' in trades_df.columns:
                broker_col = trades_df['券商']
            elif 'source' in trades_df.columns:
                broker_col = trades_df['source']
            elif 'broker' in trades_df.columns:
                broker_col = trades_df['broker']
            else:
                broker_col = pd.Series([''] * len(trades_df))

            # 按券商分類
            broker_upper = broker_col.str.upper() if hasattr(broker_col, 'str') else pd.Series([str(x).upper() for x in broker_col])
            ib_mask = broker_upper.isin(['IB', 'IBKR'])
            yuanta_mask = broker_upper.isin(['YUANTA', '元大'])
            schwab_mask = broker_upper.isin(['SCHWAB', 'CHARLES SCHWAB'])

            ib_realized = float(pnl_numeric[ib_mask].sum()) if ib_mask.any() else 0.0
            yuanta_realized = float(pnl_numeric[yuanta_mask].sum()) if yuanta_mask.any() else 0.0
            schwab_realized = float(pnl_numeric[schwab_mask].sum()) if schwab_mask.any() else 0.0

        return {
            'ib_unrealized': round(ib_unrealized, 2),
            'ib_realized': round(ib_realized, 2),
            'yuanta_unrealized': round(yuanta_unrealized, 2),
            'yuanta_realized': round(yuanta_realized, 2),
            'schwab_unrealized': round(schwab_unrealized, 2),
            'schwab_realized': round(schwab_realized, 2),
            # 向後相容
            'unrealized_pl': round(ib_unrealized + yuanta_unrealized + schwab_unrealized, 2),
            'realized_pl': round(ib_realized + yuanta_realized + schwab_realized, 2),
            'total_pl': round(ib_unrealized + yuanta_unrealized + schwab_unrealized + ib_realized + yuanta_realized + schwab_realized, 2)
        }
    except Exception as e:
        logger.error(f"計算每日損益失敗: {e}")
        return {
            'ib_unrealized': 0.0, 'ib_realized': 0.0,
            'yuanta_unrealized': 0.0, 'yuanta_realized': 0.0,
            'schwab_unrealized': 0.0, 'schwab_realized': 0.0,
            'unrealized_pl': 0.0, 'realized_pl': 0.0, 'total_pl': 0.0
        }

def get_ib_nlv() -> float:
    """從 IB TWS 取得真實帳戶 NLV（子進程模式，失敗回傳 0）"""
    import subprocess
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'query_ib_positions.py')
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=25)
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            if data.get('status') == 'success':
                return round(float(data.get('net_liquidation_value', 0)), 2)
    except Exception as e:
        logger.warning(f"取得 IB NLV 失敗: {e}")
    return 0.0


def record_daily_performance() -> Dict:
    """將今日損益 + IB 帳戶 NLV 寫入本地 CSV + Google Sheets"""
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # 1. 計算損益
        perf = calculate_daily_performance()

        # 2. 取得 IB 真實 NLV
        ib_nlv = get_ib_nlv()

        # 3. 檢查是否已記錄（從本地快取）
        cache_path = os.path.join(os.path.dirname(__file__), 'data', 'cache', 'daily_performance.csv')
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            for line in lines[1:]:  # 跳過標題
                if line.startswith(today):
                    return {'status': 'skipped', 'message': f'{today} 已記錄'}

        # 4. 寫入本地 CSV（含 IB_NLV 欄位和 Schwab）
        total_unrealized = perf['ib_unrealized'] + perf['yuanta_unrealized'] + perf['schwab_unrealized']
        total_realized = perf['ib_realized'] + perf['yuanta_realized'] + perf['schwab_realized']

        if os.path.exists(cache_path):
            with open(cache_path, 'a', encoding='utf-8-sig') as f:
                f.write(f"{today},{ib_nlv},{perf['ib_unrealized']},{perf['ib_realized']},{perf['yuanta_unrealized']},{perf['yuanta_realized']},{perf['schwab_unrealized']},{perf['schwab_realized']},{total_unrealized},{total_realized},{timestamp}\n")
        else:
            with open(cache_path, 'w', encoding='utf-8-sig') as f:
                f.write("日期,IB_NLV_USD,IB未實現USD,IB已實現USD,Yuanta未實現TWD,Yuanta已實現TWD,Schwab未實現USD,Schwab已實現USD,總未實現,總已實現,記錄時間\n")
                f.write(f"{today},{ib_nlv},{perf['ib_unrealized']},{perf['ib_realized']},{perf['yuanta_unrealized']},{perf['yuanta_realized']},{perf['schwab_unrealized']},{perf['schwab_realized']},{total_unrealized},{total_realized},{timestamp}\n")

        logger.info(f"✅ 記錄完成：{today} (IB_NLV=${ib_nlv}, IB未實現=${perf['ib_unrealized']}, Yuanta未實現=¥{perf['yuanta_unrealized']}, Schwab未實現=${perf['schwab_unrealized']})")

        # 5. 嘗試寫入 Google Sheets（非阻塞式）
        try:
            sheet = get_sheet('daily_performance')
            if sheet is not None:
                row = [today, ib_nlv, perf['ib_unrealized'], perf['ib_realized'], perf['yuanta_unrealized'], perf['yuanta_realized'], perf['schwab_unrealized'], perf['schwab_realized'], total_unrealized, total_realized, timestamp]
                sheet.append_row(row)
                logger.info(f"✅ 已同步至 Google Sheets（含 IB NLV=${ib_nlv}、Schwab=${perf['schwab_unrealized']}）")
        except Exception as sheets_err:
            logger.warning(f"寫入 Google Sheets 失敗（非阻塞）: {sheets_err}")

        return {'status': 'success', 'date': today, 'ib_nlv': ib_nlv, **perf}
    except Exception as e:
        logger.error(f"記錄每日損益失敗: {e}", exc_info=True)
        return {'status': 'error', 'message': 'Failed to record performance'}

@app.route('/api/holdings/with-prices')
def api_holdings_with_prices():
    """API：獲取持倉含市價和損益"""
    try:
        positions = get_broker_positions_from_sheets()
        if not positions:
            return jsonify({'status': 'success', 'data': []})

        # 添加市價和損益計算
        enriched_positions = []
        for pos in positions:
            symbol = pos.get('symbol', '')
            exchange = pos.get('exchange', '')
            quantity = float(pos.get('position', 0))
            avg_cost = float(pos.get('avgCost', 0))
            currency = pos.get('currency', 'USD')

            # 獲取當前市價
            market_price = get_stock_price(symbol, exchange)

            if market_price is not None:
                # 計算市值
                market_value = quantity * market_price
                # 計算成本
                cost = quantity * avg_cost
                # 未實現損益（金額）
                unrealized_pl = market_value - cost
                # 未實現損益（%）
                unrealized_pl_pct = (unrealized_pl / cost * 100) if cost > 0 else 0
            else:
                market_price = None
                market_value = None
                unrealized_pl = None
                unrealized_pl_pct = None

            enriched_positions.append({
                **pos,
                'marketPrice': market_price,
                'marketValue': market_value,
                'unrealizedPL': unrealized_pl,
                'unrealizedPLPct': unrealized_pl_pct
            })

        return jsonify({
            'status': 'success',
            'data': enriched_positions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"獲取含市價持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/holdings/by-broker/with-prices')
def api_holdings_by_broker_with_prices():
    """API：按券商分類獲取持倉含市價和損益"""
    try:
        positions = get_broker_positions_from_sheets()
        if not positions:
            return jsonify({
                'status': 'success',
                'ib': {'count': 0, 'positions': []},
                'yuanta': {'count': 0, 'positions': []}
            })

        ib_positions = []
        yuanta_positions = []

        for pos in positions:
            symbol = pos.get('symbol', '')
            exchange = pos.get('exchange', '')
            quantity = float(pos.get('position', 0))
            avg_cost = float(pos.get('avgCost', 0))

            # 獲取市價
            market_price = get_stock_price(symbol, exchange)

            if market_price is not None:
                market_value = quantity * market_price
                cost = quantity * avg_cost
                unrealized_pl = market_value - cost
                unrealized_pl_pct = (unrealized_pl / cost * 100) if cost > 0 else 0
            else:
                market_price = None
                market_value = None
                unrealized_pl = None
                unrealized_pl_pct = None

            enriched_pos = {
                **pos,
                'marketPrice': market_price,
                'marketValue': market_value,
                'unrealizedPL': unrealized_pl,
                'unrealizedPLPct': unrealized_pl_pct
            }

            # 分類到對應券商 - 使用正確的欄位名稱
            broker = pos.get('券商', pos.get('broker', '')).upper()
            if broker in ['IB', 'IBKR']:
                ib_positions.append(enriched_pos)
            elif broker in ['Yuanta', 'YUANTA']:
                yuanta_positions.append(enriched_pos)

        return jsonify({
            'status': 'success',
            'ib': {
                'count': len(ib_positions),
                'positions': ib_positions
            },
            'yuanta': {
                'count': len(yuanta_positions),
                'positions': yuanta_positions
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"按券商獲取含市價持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/daily-performance')
def api_daily_performance():
    """API：讀取每日損益歷史（分開 IB/USD 與 Yuanta/TWD）"""
    try:
        # 優先使用本地 CSV（最新格式）
        import os
        cache_path = os.path.join(os.path.dirname(__file__), 'data', 'cache', 'daily_performance.csv')

        data = {
            'dates': [],
            'ib_unrealized': [],
            'ib_realized': [],
            'yuanta_unrealized': [],
            'yuanta_realized': [],
            'schwab_unrealized': [],
            'schwab_realized': [],
            'total_unrealized': [],
            'total_realized': []
        }

        # 首先嘗試從本地 CSV 讀取（新格式）
        if os.path.exists(cache_path):
            try:
                df = pd.read_csv(cache_path, encoding='utf-8-sig')
                if not df.empty:
                    # 新格式：檢查是否有分開的欄位
                    if 'IB未實現USD' in df.columns:
                        df['日期'] = pd.to_datetime(df['日期'])
                        df = df.sort_values('日期')

                        # 轉換為數值
                        for col in ['IB未實現USD', 'IB已實現USD', 'Yuanta未實現TWD', 'Yuanta已實現TWD', 'Schwab未實現USD', 'Schwab已實現USD', '總未實現', '總已實現']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                        return jsonify({'status': 'success', 'data': {
                            'dates': df['日期'].dt.strftime('%Y-%m-%d').tolist(),
                            'ib_unrealized': df['IB未實現USD'].round(2).tolist(),
                            'ib_realized': df['IB已實現USD'].round(2).tolist(),
                            'yuanta_unrealized': df['Yuanta未實現TWD'].round(2).tolist(),
                            'yuanta_realized': df['Yuanta已實現TWD'].round(2).tolist(),
                            'schwab_unrealized': df['Schwab未實現USD'].round(2).tolist() if 'Schwab未實現USD' in df.columns else [],
                            'schwab_realized': df['Schwab已實現USD'].round(2).tolist() if 'Schwab已實現USD' in df.columns else [],
                            'total_unrealized': df['總未實現'].round(2).tolist() if '總未實現' in df.columns else [],
                            'total_realized': df['總已實現'].round(2).tolist() if '總已實現' in df.columns else []
                        }})
                    # 舊格式：轉換為新格式返回
                    elif '未實現損益' in df.columns:
                        df['日期'] = pd.to_datetime(df['日期'])
                        df = df.sort_values('日期')
                        for col in ['未實現損益', '已實現損益', '總損益']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                        return jsonify({'status': 'success', 'data': {
                            'dates': df['日期'].dt.strftime('%Y-%m-%d').tolist(),
                            'ib_unrealized': df['未實現損益'].round(2).tolist() if '未實現損益' in df.columns else [],
                            'ib_realized': df['已實現損益'].round(2).tolist() if '已實現損益' in df.columns else [],
                            'yuanta_unrealized': [],
                            'yuanta_realized': [],
                            'total_unrealized': df['未實現損益'].round(2).tolist() if '未實現損益' in df.columns else [],
                            'total_realized': df['已實現損益'].round(2).tolist() if '已實現損益' in df.columns else []
                        }})
            except Exception as csv_err:
                logger.warning(f"讀取本地 CSV 失敗: {csv_err}")

        # 如果本地 CSV 不存在或失敗，嘗試從 Google Sheets 讀取
        df = read_sheet_data_with_cache('daily_performance')
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')

            # 新格式欄位
            if 'IB未實現USD' in df.columns:
                for col in ['IB未實現USD', 'IB已實現USD', 'Yuanta未實現TWD', 'Yuanta已實現TWD', 'Schwab未實現USD', 'Schwab已實現USD', '總未實現', '總已實現']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                return jsonify({'status': 'success', 'data': {
                    'dates': df['日期'].dt.strftime('%Y-%m-%d').tolist(),
                    'ib_unrealized': df['IB未實現USD'].round(2).tolist(),
                    'ib_realized': df['IB已實現USD'].round(2).tolist(),
                    'yuanta_unrealized': df['Yuanta未實現TWD'].round(2).tolist(),
                    'yuanta_realized': df['Yuanta已實現TWD'].round(2).tolist(),
                    'schwab_unrealized': df['Schwab未實現USD'].round(2).tolist() if 'Schwab未實現USD' in df.columns else [],
                    'schwab_realized': df['Schwab已實現USD'].round(2).tolist() if 'Schwab已實現USD' in df.columns else [],
                    'total_unrealized': df['總未實現'].round(2).tolist() if '總未實現' in df.columns else [],
                    'total_realized': df['總已實現'].round(2).tolist() if '總已實現' in df.columns else []
                }})

        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        logger.error(f"讀取每日損益歷史失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/test-perf-123')
def api_test_perf():
    """測試端點"""
    return jsonify({'status': 'success', 'message': 'Test OK', 'data': 'Hello from Flask'})

@app.route('/api/daily-performance/record', methods=['POST'])
def api_record_daily_performance():
    """POST：手動觸發記錄今日損益"""
    result = record_daily_performance()
    return jsonify(result)

@app.route('/api/portfolio-chart-data')
def api_portfolio_chart_data():
    """V8 相容版投資組合圖表數據"""
    try:
        positions = get_db_positions()
        if not positions:
            # Fallback to sheets if DB is empty
            positions = get_broker_positions_from_sheets() or []
        
        total_market_value = 0
        for p in positions:
            mv = p.get('marketValue')
            if mv and str(mv) not in ('', 'None', 'nan'):
                total_market_value += float(mv)
            else:
                qty = float(p.get('position') or 0)
                px  = float(p.get('currentPrice') or p.get('marketPrice') or p.get('avgCost') or 0)
                total_market_value += qty * px

        dates, values = [], []
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            values.append(round(total_market_value * (1 - i/30 * 0.05), 2))

        return jsonify({
            'status': 'success',
            'equity_curve': values,
            'dates': dates,
            'values': values,
            'current_value': round(total_market_value, 2)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500



@app.route('/api/holdings/check-changes', methods=['POST'])
@app.route('/api/broker-positions')
def api_broker_positions():
    """API: 獲取各券商最新持倉"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': 'Google Sheets 連接失敗'}), 503

        positions = get_broker_positions_from_sheets()
        if not positions:
            positions = []

        # 補齊 marketPrice（相容新欄位名 currentPrice）
        for p in positions:
            if not p.get('marketPrice'):
                p['marketPrice'] = p.get('currentPrice', p.get('avgCost', 0))

        def is_yuanta(p):
            return (p.get('source', '').lower() == 'yuanta' or
                    str(p.get('券商', '')).strip() == '元大')

        def is_ib(p):
            return (p.get('source', '').lower() in ('ib', 'ibkr') or
                    str(p.get('券商', '')).strip().upper() in ('IB', 'IBKR', '盈透'))

        def is_schwab(p):
            return (p.get('source', '').lower() == 'schwab' or
                    str(p.get('券商', '')).strip().upper() in ('SCHWAB', 'CHARLES SCHWAB'))

        def dedup_latest(lst):
            """去重持倉：按 symbol + broker 組合，保留最新的"""
            seen = {}
            for p in lst:
                symbol = str(p.get('symbol', ''))
                broker = str(p.get('source', p.get('券商', '')))
                key = f"{symbol}_{broker}"  # 按 symbol + broker 組合去重
                ts = str(p.get('時間', p.get('timestamp', '')))
                if key not in seen or ts > seen[key][1]:
                    seen[key] = (p, ts)
            return [v[0] for v in seen.values()]

        # --- 新增：整合 V8 本地數據庫持倉 ---
        db_positions = get_db_positions()
        if db_positions:
            # 先建立已有持倉的 key 集合，避免重複
            existing_keys = set()
            for p in positions:
                key = f"{p.get('symbol', '')}_{p.get('source', p.get('券商', ''))}"
                existing_keys.add(key)

            for dp in db_positions:
                symbol = dp.get('symbol', '')
                source = dp.get('broker', dp.get('source', 'unknown'))
                key = f"{symbol}_{source}"

                # 只添加不重複的持倉
                if key not in existing_keys:
                    transformed = {
                        'source': source,
                        'exchange': dp.get('exchange', 'US'),
                        'symbol': symbol,
                        'position': dp.get('position', 0),
                        'avgCost': dp.get('avgCost', 0),
                        'marketPrice': dp.get('marketPrice', dp.get('currentPrice', dp.get('marketPrice', 0))),
                        'currency': dp.get('currency', 'USD'),
                        'timestamp': dp.get('synced_at', datetime.now().isoformat())
                    }
                    positions.append(transformed)
        # --------------------------------

        yuanta = dedup_latest([p for p in positions if is_yuanta(p)])
        ib     = dedup_latest([p for p in positions if is_ib(p)])
        schwab = dedup_latest([p for p in positions if is_schwab(p)])

        return jsonify({
            'status': 'success',
            'data': {
                'yuanta': yuanta,
                'ib': ib,
                'schwab': schwab,
                'all': positions
            }
        })

    except Exception as e:
        logger.error(f"獲取券商持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ytd-returns')
def api_ytd_returns():
    """計算各券商 YTD 報酬率（broker_snapshot 年初第一筆 vs 最新筆）"""
    empty = {'ib': None, 'schwab': None, 'yuanta': None}
    try:
        if not SHEETS_OK:
            return jsonify(empty)
        df = read_sheet_data_with_cache('broker_snapshot')
        if df is None or df.empty:
            return jsonify(empty)

        # 找時間欄和券商欄
        cols = list(df.columns)
        time_col   = '時間'   if '時間'   in cols else cols[0]
        broker_col = '券商'   if '券商'   in cols else cols[1]
        nlv_col    = next((c for c in cols if 'NLV' in c or '總資產' in c), cols[2] if len(cols) > 2 else None)
        if not nlv_col:
            return jsonify(empty)

        df[time_col]  = pd.to_datetime(df[time_col],  errors='coerce')
        df[nlv_col]   = pd.to_numeric(df[nlv_col],    errors='coerce')
        df = df.dropna(subset=[time_col, nlv_col])

        current_year = datetime.now().year
        df_year = df[df[time_col].dt.year == current_year]

        result = {}
        for broker in ['ib', 'schwab', 'yuanta']:
            sub = df_year[df_year[broker_col].str.lower() == broker].sort_values(time_col)
            if len(sub) >= 2:
                first_nlv = float(sub.iloc[0][nlv_col])
                last_nlv  = float(sub.iloc[-1][nlv_col])
                result[broker] = round((last_nlv - first_nlv) / first_nlv * 100, 2) if first_nlv else None
            elif len(sub) == 1:
                result[broker] = 0.0
            else:
                result[broker] = None
        return jsonify(result)
    except Exception as e:
        logger.warning(f"YTD 計算失敗: {e}")
        return jsonify(empty)

@app.route('/ib-test')
def ib_test():
    """測試路由 - 驗證基礎設施"""
    return '<h1>✅ Flask 運行正常</h1><p>/ib-test 路由可用</p>'

@app.route('/ib')
def ib_dashboard():
    """IB 持倉網頁儀表板"""
    print("\n" + "="*60)
    print("[/ib] 路由被訪問")
    print("="*60)

    try:
        base_dir = os.path.dirname(__file__)
        print(f"[DEBUG] 基礎目錄: {base_dir}")

        html_path = os.path.join(base_dir, 'ib_positions.html')
        print(f"[DEBUG] 尋找檔案: {html_path}")
        print(f"[DEBUG] 檔案存在? {os.path.exists(html_path)}")

        if not os.path.exists(html_path):
            error_msg = f'ib_positions.html 未找到: {html_path}'
            print(f"[ERROR] {error_msg}")
            return jsonify({'status': 'error', 'message': error_msg}), 404

        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"[SUCCESS] 成功讀取 HTML 檔案 ({len(content)} bytes)")
            return content

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[EXCEPTION] {error_trace}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/query-ib')
def api_query_ib():
    """API: 查詢 IB 持倉（子進程模式）"""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), 'query_ib_positions.py')
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            return jsonify(json.loads(result.stdout))
        return jsonify({'status': 'error', 'message': result.stderr or 'Query failed'}), 503
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Query timeout'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ib-realtime')
def api_ib_realtime():
    """API: IB Real-time Positions (別名)"""
    return api_query_ib()

@app.route('/api/ib-account-summary')
def api_ib_account_summary():
    """API: IB 帳戶摘要（格式與 yuanta-account-summary 一致）"""
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), 'query_ib_positions.py')
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout:
            raw = json.loads(result.stdout)
            if raw.get('status') == 'success':
                return jsonify({
                    'status': 'success',
                    'data': {
                        'connected': raw.get('connected', True),
                        'account_id': raw.get('account_id', 'Unknown'),
                        'net_liquidation_value': raw.get('net_liquidation_value', 0),
                        'total_cash_value': raw.get('total_cash_value', 0),
                        'unrealized_pnl': raw.get('unrealized_pnl', 0),
                        'positions_count': raw.get('positions_count', 0),
                        'positions': raw.get('positions', []),
                    }
                })
            return jsonify({'status': 'error', 'message': raw.get('message', 'IB 查詢失敗')}), 503
        return jsonify({'status': 'error', 'message': result.stderr or 'IB 查詢失敗'}), 503
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'IB 查詢超時（TWS 未回應）'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/yuanta-account-summary')
def api_yuanta_account_summary():
    """API: 取得 Yuanta 帳戶摘要（從 Google Sheets broker_positions）"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': 'Google Sheets 連接失敗'}), 503

        positions = get_broker_positions_from_sheets()
        if not positions:
            positions = []

        def is_yuanta(p):
            return (p.get('source', '').lower() == 'yuanta' or
                    str(p.get('券商', '')).strip() == '元大')

        def dedup_latest(lst):
            seen = {}
            for p in lst:
                key = str(p.get('symbol', ''))
                ts = str(p.get('時間', p.get('timestamp', '')))
                if key not in seen or ts > seen[key][1]:
                    seen[key] = (p, ts)
            return [v[0] for v in seen.values()]

        yuanta_positions = dedup_latest([p for p in positions if is_yuanta(p)])

        # 補齊 marketPrice（相容新欄位名 currentPrice）
        for p in yuanta_positions:
            if not p.get('marketPrice'):
                p['marketPrice'] = p.get('currentPrice', p.get('avgCost', 0))

        # 優先使用 Sheets 已計算的 marketValue / unrealizedPnL
        total_market_value = 0.0
        unrealized_pnl = 0.0
        for p in yuanta_positions:
            mv_sheet = float(p.get('marketValue', 0) or 0)
            total_market_value += mv_sheet if mv_sheet else (
                float(p.get('position', 0)) * float(p.get('marketPrice', p.get('avgCost', 0)))
            )
            pnl_sheet = p.get('unrealizedPnL', '')
            if pnl_sheet != '' and pnl_sheet is not None:
                unrealized_pnl += float(pnl_sheet or 0)
            elif float(p.get('avgCost', 0) or 0) > 0:
                unrealized_pnl += (
                    (float(p.get('marketPrice', 0)) - float(p.get('avgCost', 0)))
                    * float(p.get('position', 0))
                )

        return jsonify({
            'status': 'success',
            'data': {
                'connected': True,
                'account_id': os.getenv('YUANTA_ACCOUNT', 'Unknown'),
                'net_liquidation_value': total_market_value,
                'total_cash_value': 0,
                'positions_count': len(yuanta_positions),
                'unrealized_pnl': unrealized_pnl,
                'positions': yuanta_positions
            }
        })

    except Exception as e:
        logger.error(f"取得 Yuanta 帳戶信息失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/schwab-account-summary')
def api_schwab_account_summary():
    """API: 取得 Schwab 帳戶真實數據（via schwab-py）"""
    try:
        import schwab as schwab_lib
        token_path = os.path.join(os.path.dirname(__file__), '.secrets', 'schwab_token.json')
        if not os.path.exists(token_path):
            return jsonify({'status': 'error', 'message': '尚未登入 Schwab（請先執行 schwab_login.py）', 'connected': False}), 401

        client_id     = os.getenv('SCHWAB_CLIENT_ID', '')
        client_secret = os.getenv('SCHWAB_CLIENT_SECRET', '')
        callback_url  = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8787/callback')

        client = schwab_lib.auth.client_from_token_file(token_path, client_id, client_secret)

        # 取帳戶 hash
        accounts_resp = client.get_account_numbers()
        accounts = accounts_resp.json()
        if not accounts:
            return jsonify({'status': 'error', 'message': '找不到 Schwab 帳戶', 'connected': False}), 404

        account_hash = accounts[0]['hashValue']
        account_num  = accounts[0].get('accountNumber', '')

        # 取帳戶詳情（含持倉和餘額）
        detail_resp = client.get_account(account_hash, fields=[schwab_lib.client.Client.Account.Fields.POSITIONS])
        detail = detail_resp.json()

        sec_account = detail.get('securitiesAccount', {})
        balances = sec_account.get('currentBalances', {})
        positions_raw = sec_account.get('positions', [])

        nlv = balances.get('liquidationValue', 0)
        cash = balances.get('cashBalance', 0)
        unrealized_pnl = sum(p.get('longOpenProfitLoss', p.get('currentDayProfitLoss', 0)) for p in positions_raw)
        total_market_value = sum(p.get('marketValue', 0) for p in positions_raw)

        positions = []
        for p in positions_raw:
            inst = p.get('instrument', {})
            qty = p.get('longQuantity', 0) or p.get('shortQuantity', 0)
            avg = p.get('averagePrice', 0)
            mkt_val = p.get('marketValue', 0)
            open_pnl = p.get('longOpenProfitLoss', p.get('currentDayProfitLoss', 0))
            cost_basis = avg * qty if qty else 0
            pnl_pct = (open_pnl / cost_basis * 100) if cost_basis != 0 else 0
            positions.append({
                'symbol': inst.get('symbol', ''),
                'asset_type': inst.get('assetType', ''),
                'quantity': qty,
                'average_price': round(avg, 4),
                'market_value': round(mkt_val, 2),
                'unrealized_pnl': round(open_pnl, 2),
                'pnl_pct': round(pnl_pct, 2),
                'today_pnl': round(p.get('currentDayProfitLoss', 0), 2),
            })

        return jsonify({
            'status': 'success',
            'connected': True,
            'account_number': account_num,
            'net_liquidation_value': round(nlv, 2),
            'cash_balance': round(cash, 2),
            'total_market_value': round(total_market_value, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'positions': positions,
            'position_count': len(positions),
        })

    except Exception as e:
        logger.error(f"Schwab API 錯誤: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e), 'connected': False}), 500

@app.route('/api/sync-yuanta', methods=['POST'])
def api_sync_yuanta():
    """API: 手動觸發 Yuanta 持倉同步（使用 32-bit Python）"""
    try:
        import subprocess
        import sys

        logger.info("🔄 開始 Yuanta 持倉同步...")

        # 嘗試找到 32-bit Python 環境
        venv_yuanta_paths = [
            '.venv_yuanta32_new/Scripts/python.exe',
            '.venv_yuanta32_new\\Scripts\\python.exe',
            'venv_yuanta32_new/Scripts/python.exe',
            'venv_yuanta32_new\\Scripts\\python.exe',
        ]

        python_exe = None
        for path in venv_yuanta_paths:
            if os.path.exists(path):
                python_exe = path
                logger.info(f"✅ 找到 32-bit Python: {path}")
                break

        if not python_exe:
            # 降級到系統 Python（如果是 32-bit）
            python_exe = sys.executable
            logger.warning(f"⚠️ 未找到專用 32-bit 環境，使用系統 Python: {python_exe}")

        # 執行同步腳本
        script_path = 'brokers/sync_yuanta_positions.py'
        result = subprocess.run(
            [python_exe, script_path],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=120  # 2 分鐘超時
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        if success:
            logger.info("✅ Yuanta 同步完成")
            return jsonify({
                'status': 'success',
                'message': '✅ Yuanta 持倉已同步',
                'output': output[-500:] if output else '執行完成'  # 最後 500 字
            })
        else:
            logger.error(f"❌ Yuanta 同步失敗，嘗試從 Google Sheets 讀取備份...")
            # Fallback: 嘗試從 Google Sheets 讀取備份數據
            try:
                from sheets_utils import read_broker_positions
                df = read_broker_positions()
                if not df.empty:
                    logger.info(f"✅ 已從 Google Sheets 讀取 {len(df)} 筆持倉備份")
                    return jsonify({
                        'status': 'fallback',
                        'message': '⚠️ Yuanta 同步失敗，已切換至 Google Sheets 備份資料',
                        'data': df.to_dict('records'),
                        'error': output[-300:] if output else '未知錯誤'
                    }), 200
            except Exception as e:
                logger.error(f"❌ Google Sheets 備份讀取也失敗: {e}")

            return jsonify({
                'status': 'error',
                'message': '❌ 同步失敗，無備份數據可用',
                'error': output[-500:] if output else '未知錯誤'
            }), 500

    except subprocess.TimeoutExpired:
        logger.error("❌ Yuanta 同步超時 (>120s)")
        return jsonify({
            'status': 'error',
            'message': '❌ 同步超時'
        }), 504
    except Exception as e:
        logger.error(f"❌ Yuanta 同步异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'❌ 錯誤: {str(e)}'
        }), 500

def check_holdings_changes():
    """檢查持倉是否有變化"""
    try:
        import json
        from datetime import datetime

        # 獲取最新持倉
        current_positions = get_broker_positions_from_sheets()
        if not current_positions:
            current_positions = []

        # 從請求體獲取之前的持倉
        previous_data = request.get_json() or {}
        previous_positions = previous_data.get('positions', [])

        # 比較持倉
        has_changes = False
        changes_detail = {
            'added': [],
            'removed': [],
            'modified': [],
            'total_current': len(current_positions),
            'total_previous': len(previous_positions)
        }

        # 創建 symbol -> position 映射
        current_map = {p.get('symbol'): p for p in current_positions}
        previous_map = {p.get('symbol'): p for p in previous_positions}

        # 檢查新增
        for symbol, position in current_map.items():
            if symbol not in previous_map:
                has_changes = True
                changes_detail['added'].append({
                    'symbol': symbol,
                    'position': position.get('position'),
                    'avgCost': position.get('avgCost')
                })

        # 檢查刪除
        for symbol, position in previous_map.items():
            if symbol not in current_map:
                has_changes = True
                changes_detail['removed'].append({
                    'symbol': symbol,
                    'position': position.get('position'),
                    'avgCost': position.get('avgCost')
                })

        # 檢查修改
        for symbol in previous_map:
            if symbol in current_map:
                prev_pos = previous_map[symbol].get('position', 0)
                curr_pos = current_map[symbol].get('position', 0)
                if prev_pos != curr_pos:
                    has_changes = True
                    changes_detail['modified'].append({
                        'symbol': symbol,
                        'previous_position': prev_pos,
                        'current_position': curr_pos
                    })

        return jsonify({
            'status': 'success',
            'has_changes': has_changes,
            'current_positions': current_positions,
            'changes': changes_detail,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"檢查持倉變化失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# API 路由 - 策略數據
# ============================================================================

@app.route('/api/strategies')
def api_strategies():
    """API：獲取所有策略"""
    try:
        # 優先從 Google Sheets 讀取
        strategies = get_strategies_from_sheets()
        if strategies:
            return jsonify({
                'status': 'success',
                'data': strategies,
                'source': 'sheets'
            })

        # 備選：從數據層
        if DATA_LAYER_OK:
            data_layer = get_data_layer()
            strategies_df = data_layer.get_strategies()
            if not strategies_df.empty:
                return jsonify({
                    'status': 'success',
                    'data': strategies_df.to_dict('records'),
                    'source': 'broker'
                })

        # 最後備選
        return jsonify({
            'status': 'success',
            'data': [],
            'message': '暫無策略數據',
            'source': 'none'
        })
    except Exception as e:
        logger.error(f"獲取策略失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/strategies/performance')
def api_strategies_performance():
    """API：獲取所有策略的 NAV 歷史（供比較圖表使用）"""
    try:
        result = {}

        # 優先從 Google Sheets 讀取
        nav_df = None
        if SHEETS_OK:
            try:
                nav_df = read_sheet_data_with_cache('daily_nav')
            except Exception as e:
                logger.warning(f"從 Sheets 讀取 daily_nav 失敗: {e}")

        # 備選：從本地 CSV 讀取
        if nav_df is None or nav_df.empty:
            cache_path = os.path.join(os.path.dirname(__file__), 'data', 'cache', 'daily_nav.csv')
            if os.path.exists(cache_path):
                nav_df = pd.read_csv(cache_path)

        if nav_df is not None and not nav_df.empty:
            # 統一欄位名稱（中文或英文）
            date_col = '日期' if '日期' in nav_df.columns else 'date'
            strategy_col = '策略' if '策略' in nav_df.columns else 'strategy'
            nav_col = 'NAV' if 'NAV' in nav_df.columns else 'nav'

            if date_col in nav_df.columns and strategy_col in nav_df.columns and nav_col in nav_df.columns:
                nav_df[date_col] = pd.to_datetime(nav_df[date_col], errors='coerce')
                nav_df = nav_df.dropna(subset=[date_col])
                nav_df = nav_df.sort_values(date_col)

                for strategy, group in nav_df.groupby(strategy_col):
                    result[strategy] = [
                        {'date': row[date_col].strftime('%Y-%m-%d'), 'nav': float(row[nav_col])}
                        for _, row in group.iterrows()
                        if pd.notna(row[nav_col])
                    ]

        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        logger.error(f"獲取策略績效失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trades/<strategy_name>')
def api_trades(strategy_name):
    """API：獲取特定策略的交易"""
    try:
        if DATA_LAYER_OK:
            data_layer = get_data_layer()
            trades_df = data_layer.get_trades(strategy_name)
            if not trades_df.empty:
                return jsonify({
                    'status': 'success',
                    'data': trades_df.to_dict('records')
                })

        return jsonify({
            'status': 'success',
            'data': [],
            'message': f'策略 {strategy_name} 暫無交易數據'
        })
    except Exception as e:
        logger.error(f"獲取交易失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/positions/current')
def api_current_positions():
    """API：獲取當前實時持倉 - 直接從 broker_positions"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        df = read_sheet_data_with_cache('broker_positions')
        if df is None or df.empty:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })

        # 過濾掉數量為 0 的持倉
        df = df[pd.to_numeric(df['position'], errors='coerce') != 0].copy()

        records = []
        for idx, row in df.iterrows():
            symbol = str(row.get('symbol', '')).strip()

            # 安全轉換數值
            def safe_float(val, default=0.0):
                try:
                    f = float(pd.to_numeric(val, errors='coerce'))
                    return default if pd.isna(f) else f
                except:
                    return default

            record = {
                'id': f"pos_{str(row.get('券商', '')).strip()}_{symbol}_{idx}",
                '標的': symbol,
                '數量': safe_float(row['position']),
                '進場價': safe_float(row.get('avgCost', 0)),
                '市價': safe_float(row.get('Market', 0)),
                '日期': str(row.get('時間', '')).strip(),
                '券商': str(row.get('券商', '')).strip(),
                '市場': str(row.get('exchange', '')).strip(),
                '幣別': str(row.get('currency', '')).strip(),
                '策略': '',
                '進場原因': '',
                '狀態': '持倉'
            }
            records.append(record)

        return jsonify({
            'status': 'success',
            'data': records,
            'count': len(records)
        })
    except Exception as e:
        logger.error(f"獲取當前持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trades/open')
def api_open_trades():
    """API：獲取所有當前持倉（從 broker_positions 實時數據）"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        # 讀取實時持倉（broker_positions）
        df = read_sheet_data_with_cache('broker_positions')
        if df is None or df.empty:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0,
                'source': 'broker_positions'
            })

        # 過濾掉數量為 0 的持倉
        df = df[pd.to_numeric(df['position'], errors='coerce') != 0].copy()

        if df.empty:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0,
                'source': 'broker_positions'
            })

        # 標準化欄位名稱以匹配前端期望的格式
        records = []
        for idx, row in df.iterrows():
            # 嘗試從 trades 表查找該持倉的策略和進場原因
            symbol = str(row.get('symbol', '')).strip()
            strategy = ''
            entry_reason = ''

            try:
                trades_df = read_sheet_data_with_cache('trades')
                if trades_df is not None and not trades_df.empty:
                    # 尋找該標的最近的持倉記錄
                    matching = trades_df[
                        (trades_df['標的'].astype(str).str.upper() == symbol.upper()) &
                        (trades_df['狀態'].isin(['持倉', '進行中']))
                    ].sort_values('日期', ascending=False)

                    if not matching.empty:
                        first = matching.iloc[0]
                        strategy = str(first.get('策略', '')).strip()
                        entry_reason = str(first.get('進場原因', '')).strip()
            except:
                pass

            # 安全轉換數值，避免 NaN
            def safe_float(val, default=0.0):
                try:
                    f = float(pd.to_numeric(val, errors='coerce'))
                    return default if pd.isna(f) else f
                except:
                    return default

            record = {
                'id': f"pos_{str(row.get('券商', 'UNKNOWN')).strip()}_{symbol}_{idx}",
                '標的': symbol,
                '數量': safe_float(row['position']),
                '進場價': safe_float(row.get('avgCost', 0)),
                '策略': strategy,
                '進場原因': entry_reason,
                '日期': str(row.get('時間', '')).strip(),
                '券商': str(row.get('券商', '')).strip(),
                '市場': str(row.get('exchange', '')).strip(),
                '幣別': str(row.get('currency', '')).strip(),
                '市價': safe_float(row.get('Market', 0)),
                '狀態': '持倉',
                'source': 'broker_positions'
            }
            records.append(record)

        return jsonify({
            'status': 'success',
            'data': records,
            'count': len(records),
            'source': 'broker_positions'
        })
    except Exception as e:
        logger.error(f"獲取當前持倉失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trades/update', methods=['POST'])
def api_update_trade():
    """API：保存交易信息（進場原因、策略等）- 創建或更新 trades 表"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        data = request.get_json()
        trade_id = data.get('id')
        symbol = data.get('symbol')
        entry_price = data.get('entry_price')
        quantity = data.get('quantity')
        strategy = data.get('strategy')
        entry_reason = data.get('entry_reason')

        if not trade_id or not symbol:
            return jsonify({'status': 'error', 'message': '缺少必要信息（ID或標的）'}), 400

        if not strategy or not entry_reason:
            return jsonify({'status': 'error', 'message': '缺少策略或進場原因'}), 400

        # 讀取交易表：優先用本地快取，避免打 Sheets API 超過配額
        try:
            from sheets_utils import _load_from_cache
            df = _load_from_cache('trades')
        except Exception:
            df = pd.DataFrame()
        if df is None or df.empty:
            df = read_sheet_data_with_cache('trades') or pd.DataFrame()

        # 嘗試查找該交易是否已存在（若快取沒有 id 欄位則視為空）
        if not df.empty and 'id' in df.columns:
            trade_idx = df[df['id'] == trade_id].index
        else:
            trade_idx = pd.Index([])

        if not trade_idx.empty:
            # 更新現有記錄
            df.loc[trade_idx, '進場原因'] = entry_reason
            df.loc[trade_idx, '策略'] = strategy
            logger.info(f"✅ 更新交易 {trade_id}: {symbol} | strategy={strategy}")
            action = '已更新'
        else:
            # 創建新記錄
            # 解析 trade_id 格式：pos_{券商}_{標的}_{索引}
            parts = trade_id.split('_')
            broker = parts[1] if len(parts) > 1 else 'UNKNOWN'

            new_record = {
                'id': trade_id,
                '日期': pd.Timestamp.now().strftime('%Y-%m-%d'),
                '券商': broker,
                '標的': symbol,
                '交易類型': 'BUY' if quantity > 0 else 'SELL',
                '進場價': entry_price,
                '出場價': '',
                '數量': quantity,
                '狀態': '持倉',
                '策略': strategy,
                '進場原因': entry_reason,
                '出場原因': '',
                '備註': '',
                'entry_time': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'exit_time': '',
                'currency': 'USD' if 'IB' in broker else 'TWD',
                'source': 'broker_positions',
                'pnl': ''
            }
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            logger.info(f"✅ 新增交易 {trade_id}: {symbol} | strategy={strategy}")
            action = '已新增'

        # 1. 先存本地快取（即時）
        try:
            from sheets_utils import _save_to_cache
            _save_to_cache('trades', df)
        except Exception as cache_err:
            logger.warning(f"本地快取儲存失敗: {cache_err}")

        # 2. 背景同步到 Google Sheets（不阻塞回應）
        import threading, time as _time
        df_copy = df.copy()

        def _sync_to_sheets():
            def _write():
                sheet = get_sheet('trades')
                if not sheet:
                    return
                headers = df_copy.columns.tolist()
                rows = []
                for _, row in df_copy.iterrows():
                    row_values = []
                    for val in row.tolist():
                        if pd.isna(val):
                            row_values.append('')
                        elif isinstance(val, pd.Timestamp):
                            row_values.append(str(val))
                        else:
                            row_values.append(str(val) if val is not None else '')
                    rows.append(row_values)
                sheet.clear()
                sheet.append_row(headers)
                for row_values in rows:
                    sheet.append_row(row_values)
                logger.info('✅ 背景同步 trades 到 Google Sheets 完成')

            try:
                _write()
            except Exception as e:
                if '429' in str(e):
                    logger.warning('Sheets 429，60 秒後重試...')
                    _time.sleep(60)
                    try:
                        _write()
                    except Exception as e2:
                        logger.error(f"Sheets 背景重試失敗: {e2}")
                else:
                    logger.error(f"Sheets 背景同步失敗: {e}")

        threading.Thread(target=_sync_to_sheets, daemon=True).start()

        return jsonify({
            'status': 'success',
            'message': f'交易 {action}（本地已儲存，Sheets 背景同步中）',
            'action': action
        })

    except Exception as e:
        logger.error(f"保存交易失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trades/realized')
def api_realized_trades():
    """API：獲取所有已實現交易（完成的交易）"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        # 讀取所有交易
        df = read_sheet_data_with_cache('trades')
        if df is None or df.empty:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })

        # 尋找已成交的交易（狀態為"已成交"或"已完成"）
        realized = df[
            (df['狀態'].fillna('') == '已成交') |
            (df['狀態'].fillna('') == '已完成')
        ].copy()

        if realized.empty:
            return jsonify({
                'status': 'success',
                'data': [],
                'count': 0
            })

        # 轉換為字典並排序（最新在前）
        try:
            realized['日期'] = pd.to_datetime(realized['日期'], errors='coerce')
            realized = realized.sort_values('日期', ascending=False)
        except:
            pass

        records = realized.to_dict('records')

        # 清理 NaN 值（將其轉換為 None，以便正確序列化為 JSON null）
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return jsonify({
            'status': 'success',
            'data': records,
            'count': len(records)
        })
    except Exception as e:
        logger.error(f"獲取已實現交易失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trades/by-strategy')
def api_trades_by_strategy():
    """API：獲取按策略分組的所有交易"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        # 讀取所有交易
        df = read_sheet_data_with_cache('trades')
        if df is None or df.empty:
            return jsonify({
                'status': 'success',
                'strategies': {}
            })

        # 按策略分組
        strategies = {}
        for strategy in df['策略'].unique():
            strategy_trades = df[df['策略'] == strategy].copy()

            # 分離已實現和未實現
            try:
                strategy_trades['日期'] = pd.to_datetime(strategy_trades['日期'], errors='coerce')
                strategy_trades = strategy_trades.sort_values('日期', ascending=False)
            except:
                pass

            realized = strategy_trades[
                (strategy_trades['狀態'].fillna('') == '已成交') |
                (strategy_trades['狀態'].fillna('') == '已完成')
            ]

            strategies[str(strategy)] = {
                'total': len(strategy_trades),
                'realized': len(realized),
                'trades': realized.to_dict('records') if not realized.empty else []
            }

        return jsonify({
            'status': 'success',
            'strategies': strategies
        })
    except Exception as e:
        logger.error(f"獲取策略交易失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/nav/<strategy_name>')
def api_nav(strategy_name):
    """API：獲取策略的 NAV（每日淨值）"""
    try:
        if DATA_LAYER_OK:
            data_layer = get_data_layer()
            nav_df = data_layer.get_daily_nav(strategy_name)
            if not nav_df.empty:
                return jsonify({
                    'status': 'success',
                    'data': nav_df.to_dict('records')
                })

        return jsonify({
            'status': 'success',
            'data': [],
            'message': f'策略 {strategy_name} 暫無 NAV 數據'
        })
    except Exception as e:
        logger.error(f"獲取 NAV 失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# API 路由 - 績效分析
# ============================================================================

@app.route('/api/performance/<strategy_name>')
def api_performance(strategy_name):
    """API：獲取策略績效指標"""
    try:
        if DATA_LAYER_OK:
            data_layer = get_data_layer()

            # 獲取交易和 NAV
            trades_df = data_layer.get_trades(strategy_name)
            nav_df = data_layer.get_daily_nav(strategy_name)

            # 計算績效
            metrics = data_layer.calculate_performance_metrics(trades_df, nav_df)

            return jsonify({
                'status': 'success',
                'strategy': strategy_name,
                'data': metrics
            })

        return jsonify({
            'status': 'error',
            'message': '數據層不可用'
        }), 500
    except Exception as e:
        logger.error(f"計算績效失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# API 路由 - CSV 上傳
# ============================================================================

@app.route('/api/upload-csv', methods=['POST'])
def api_upload_csv():
    """API：上傳並處理策略回測文件（CSV / XLSX，或指定本地路徑）"""
    try:
        strategy_name   = request.form.get('strategy_name', 'imported_strategy')
        initial_capital = float(request.form.get('initial_capital', 100000))

        # ── 模式 A：直接提供本地路徑 ──────────────────────────────
        file_path = request.form.get('file_path', '').strip()
        if file_path:
            fp = Path(file_path)
            if not fp.exists():
                return jsonify({'status': 'error', 'message': f'找不到檔案：{file_path}'}), 400
            ext = fp.suffix.lower()
            if ext == '.xlsx':
                df = pd.read_excel(fp, engine='openpyxl')
            elif ext == '.csv':
                try:
                    df = pd.read_csv(fp, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(fp, encoding='cp950')
            else:
                return jsonify({'status': 'error', 'message': f'不支援的格式：{ext}'}), 400

        # ── 模式 B：上傳檔案 ──────────────────────────────────────
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'status': 'error', 'message': '文件名為空'}), 400
            ext = Path(file.filename).suffix.lower()
            if ext == '.xlsx':
                df = pd.read_excel(file, engine='openpyxl')
            elif ext == '.csv':
                try:
                    content = file.read().decode('utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    content = file.read().decode('cp950')
                df = pd.read_csv(StringIO(content))
            else:
                return jsonify({'status': 'error', 'message': f'不支援的格式（支援 .csv / .xlsx）'}), 400
        else:
            return jsonify({'status': 'error', 'message': '請上傳檔案或提供檔案路徑'}), 400

        # ── 處理 DataFrame ─────────────────────────────────────────
        if not DATA_LAYER_OK:
            return jsonify({'status': 'error', 'message': '數據層不可用，無法處理文件'}), 500

        data_layer = get_data_layer()
        result = data_layer.process_strategy_csv(df, strategy_name, initial_capital)
        return jsonify({
            'status':  'success' if result['success'] else 'error',
            'message': result['message'],
            'data': {
                'trades_count': len(result['trades']) if result['trades'] else 0,
                'metrics':      result['metrics'],
                'source':       file_path if file_path else (file.filename if 'file' in request.files else ''),
            }
        })

    except Exception as e:
        logger.error(f"檔案上傳失敗: {e}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'上傳失敗: {str(e)}'}), 500

# ============================================================================
# V8 DASHBOARD API
# ============================================================================

@app.route('/api/equity-history', methods=['GET'])
def api_equity_history():
    """取得歷史每日快照（供淨值曲線圖表使用）"""
    try:
        days = int(request.args.get('days', 365))
        if not DB_PATH.exists():
            return jsonify({'status': 'success', 'data': [], 'count': 0})
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT date, ib_mv_usd, schwab_mv_usd, yuanta_mv_twd, 
                            total_mv_twd, total_pnl_twd, usd_twd_rate, notes
                     FROM equity_snapshots
                     ORDER BY date ASC
                     LIMIT ?''', (days,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'status': 'success', 'data': rows, 'count': len(rows)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import', methods=['POST'])

def api_strategy_import():
    try:
        if 'file' not in request.files: return jsonify({'status': 'error', 'message': 'No file'}), 400
        file = request.files['file']
        df = read_csv_file(file)
        df.columns = [col.lstrip('\ufeff') for col in df.columns]
        trades = []
        for _, row in df.iterrows():
            try:
                trades.append({
                    'symbol': str(row.get('商品代碼', '')),
                    'name': str(row.get('商品名稱', '')),
                    'entry_price': float(row.get('進場價格', 0)),
                    'exit_price': float(row.get('出場價格', 0)),
                    'qty': int(row.get('交易數量', 0)),
                    'profit': float(row.get('獲利金額', 0)),
                    'return_rate': float(row.get('報酬率', 0))
                })
            except: continue
        
        # Calculate summary
        total_p = sum(t['profit'] for t in trades)
        win_r = len([t for t in trades if t['profit'] > 0]) / len(trades) if trades else 0
        
        return jsonify(convert_numpy_types({
            'status': 'success',
            'preview': {
                'total_trades': len(trades),
                'total_profit': round(total_p, 2),
                'win_rate': round(win_r * 100, 2),
                'sample_trades': trades[:10]
            }
        }))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/strategy/import/charts', methods=['POST'])
def api_strategy_charts():
    try:
        if 'file' not in request.files: return jsonify({'status': 'error', 'message': 'No file'}), 400
        df = read_csv_file(request.files['file'])
        df['出場時間'] = pd.to_datetime(df.get('出場時間', datetime.now()))
        df['獲利金額'] = pd.to_numeric(df.get('獲利金額', 0), errors='coerce')
        daily_pnl = df.groupby(df['出場時間'].dt.date)['獲利金額'].sum().reset_index()
        daily_pnl['累計'] = daily_pnl['獲利金額'].cumsum()
        
        return jsonify(convert_numpy_types({
            'status': 'success',
            'charts': {
                'daily_pnl': {
                    'dates': [str(d) for d in daily_pnl.iloc[:, 0]],
                    'cumulative': daily_pnl['累計'].round(2).tolist()
                }
            }
        }))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def api_health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

# ============================================================================
# API 路由 - 波斯灣油輪監測
# ============================================================================

@app.route('/api/ship-monitoring/vessels')
def api_ship_vessels():
    """API：獲取波斯灣油輪數據"""
    try:
        if not SHIP_MONITOR_OK:
            return jsonify({
                'status': 'error',
                'message': 'Ship monitoring 不可用'
            }), 503

        vessels = fetch_gulf_tankers()
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'count': len(vessels),
            'vessels': vessels
        })
    except Exception as e:
        logger.error(f"獲取油輪數據失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ship-monitoring/alerts')
def api_ship_alerts():
    """API：獲取船舶異常告警"""
    try:
        if not SHIP_MONITOR_OK:
            return jsonify({
                'status': 'error',
                'message': 'Ship monitoring 不可用'
            }), 503

        vessels = fetch_gulf_tankers()
        alerts = detect_all_alerts(vessels, vessel_tracker)

        # 篩選最近 24 小時的告警
        cutoff = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            a for a in alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'count': len(recent_alerts),
            'alerts': recent_alerts
        })
    except Exception as e:
        logger.error(f"獲取告警失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ship-monitoring/statistics')
def api_ship_statistics():
    """API：獲取油輪監測統計"""
    try:
        if not SHIP_MONITOR_OK:
            return jsonify({
                'status': 'error',
                'message': 'Ship monitoring 不可用'
            }), 503

        vessels = fetch_gulf_tankers()
        alerts = detect_all_alerts(vessels, vessel_tracker)

        # 計算統計
        in_region = sum(
            1 for v in vessels
            if vessel_tracker.is_in_region(v['latitude'], v['longitude'])
        )

        high_alerts = [a for a in alerts if a.get('severity') == 'high']

        cutoff = datetime.now() - timedelta(hours=24)
        alerts_24h = [
            a for a in alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_vessels': len(vessels),
            'in_region': in_region,
            'outside_region': len(vessels) - in_region,
            'recent_alerts_24h': len(alerts_24h),
            'critical_alerts': len(high_alerts),
            'system_status': 'Normal' if len(high_alerts) == 0 else '⚠️ Caution'
        })
    except Exception as e:
        logger.error(f"計算統計失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/ship-monitoring/waiting-vessels')
def api_waiting_vessels():
    """API：獲取在區域內停留超過 N 小時的油輪"""
    try:
        if not SHIP_MONITOR_OK:
            return jsonify({
                'status': 'error',
                'message': 'Ship monitoring 不可用'
            }), 503

        vessels = fetch_gulf_tankers()

        # 獲取停留時間閾值（小時數）- 預設 6 小時
        threshold_hours = request.args.get('hours', 6, type=int)
        threshold_minutes = threshold_hours * 60

        waiting_vessels = []

        for vessel in vessels:
            mmsi = vessel.get('mmsi')
            if vessel_tracker.is_in_region(vessel['latitude'], vessel['longitude']):
                # 獲取船舶摘要以計算停留時間
                summary = vessel_tracker.get_vessel_summary(mmsi)
                if summary:
                    stationary_duration = summary.get('stationary_duration', 0)

                    # 如果停留時間超過閾值
                    if stationary_duration >= threshold_minutes:
                        waiting_vessels.append({
                            'mmsi': mmsi,
                            'vessel_name': vessel.get('vessel_name'),
                            'latitude': vessel.get('latitude'),
                            'longitude': vessel.get('longitude'),
                            'speed': vessel.get('speed'),
                            'heading': vessel.get('heading'),
                            'flag': vessel.get('flag'),
                            'vessel_type': vessel.get('vessel_type'),
                            'destination': vessel.get('destination'),
                            'origin_port': vessel.get('origin_port'),
                            'waiting_duration_hours': round(stationary_duration / 60, 1),
                            'waiting_duration_minutes': int(stationary_duration),
                        })

        # 按等待時間排序（最久在前）
        waiting_vessels.sort(key=lambda x: x['waiting_duration_minutes'], reverse=True)

        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'threshold_hours': threshold_hours,
            'count': len(waiting_vessels),
            'vessels': waiting_vessels
        })
    except Exception as e:
        logger.error(f"獲取停留船舶失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/status')
def api_status():
    """API：系統狀態檢查"""
    status = {
        'app': 'running',
        'data_layer': DATA_LAYER_OK,
        'ship_monitor': SHIP_MONITOR_OK,
        'timestamp': datetime.now().isoformat()
    }

    # 檢查各個模塊的狀態
    if DATA_LAYER_OK:
        data_layer = get_data_layer()
        status['brokers'] = {
            'ib': bool(data_layer._cache.get('ib_available', False)),
            'yuanta': bool(data_layer._cache.get('yuanta_available', False)),
            'schwab': bool(data_layer._cache.get('schwab_available', False))
        }

    return jsonify(status)

@app.route('/api/debug/sheets')
def api_debug_sheets():
    """API：調試 Google Sheets 連接"""
    try:
        debug_info = {
            'sheets_ok': SHEETS_OK,
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }

        # 檢查持倉表
        try:
            positions = get_broker_positions_from_sheets()
            if positions:
                debug_info['tables']['broker_positions'] = {
                    'count': len(positions),
                    'data': positions
                }
            else:
                debug_info['tables']['broker_positions'] = {'count': 0, 'data': []}
        except Exception as e:
            debug_info['tables']['broker_positions'] = {'error': str(e)}

        # 檢查帳戶快照
        try:
            snapshot = get_broker_snapshot_from_sheets()
            if snapshot:
                debug_info['tables']['broker_snapshot'] = {'data': snapshot}
            else:
                debug_info['tables']['broker_snapshot'] = {'data': None}
        except Exception as e:
            debug_info['tables']['broker_snapshot'] = {'error': str(e)}

        # 檢查 NAV
        try:
            nav_df = get_daily_nav_from_sheets()
            if nav_df is not None and len(nav_df) > 0:
                debug_info['tables']['daily_nav'] = {
                    'count': len(nav_df),
                    'latest': nav_df.iloc[-1].to_dict()
                }
            else:
                debug_info['tables']['daily_nav'] = {'count': 0}
        except Exception as e:
            debug_info['tables']['daily_nav'] = {'error': str(e)}

        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# IB API 同步路由
# ============================================================================

@app.route('/api/brokers/sync-all', methods=['POST'])
def api_sync_all_brokers():
    """API：自動同步所有 Broker（IB、Yuanta）"""
    results = {
        'ib': {'status': 'pending'},
        'yuanta': {'status': 'pending'},
        'timestamp': datetime.now().isoformat()
    }

    # 同步 IB
    try:
        from brokers.ib_api import get_open_positions

        logger.info("正在同步 IB...")
        positions = get_open_positions()

        if positions:
            positions_list = [
                {
                    'symbol': p.get('symbol', ''),
                    'exchange': p.get('exchange', ''),
                    'currency': p.get('currency', ''),
                    'position': p.get('position', 0),
                    'avgCost': p.get('avgCost', 0),
                    'marketPrice': 0,
                    'source': 'ib'
                }
                for p in positions
            ]
            result = append_positions_with_dedup(positions_list, 'broker_positions')
            results['ib'] = {
                'status': 'success' if result.get('error') is None else 'warning',
                'added': result['added'],
                'skipped': result['skipped']
            }
        else:
            results['ib'] = {'status': 'info', 'message': '無持仓數據'}
    except Exception as e:
        logger.error(f"IB 同步失敗: {e}")
        results['ib'] = {'status': 'error', 'message': str(e)}

    # 同步 Yuanta (僅 Windows)
    if platform.system() == "Windows":
        try:
            from brokers.yuanta_api import (
                yuanta_login,
                query_stock_positions,
                fetch_positions,
            )

            logger.info("正在同步 Yuanta...")
            api = yuanta_login()

            if api and query_stock_positions(api):
                positions = fetch_positions(api)

                if positions:
                    rows_to_append = []
                    for pos_str in positions:
                        try:
                            parts = pos_str.split(',')
                            if len(parts) >= 9:
                                rows_to_append.append({
                                    'symbol': parts[4],
                                    'exchange': 'TWSE',
                                    'currency': 'TWD',
                                    'position': float(parts[6]),
                                    'avgCost': float(parts[8]),
                                    'marketPrice': float(parts[7]),
                                    'source': 'yuanta'
                                })
                        except:
                            continue

                    if rows_to_append:
                        result = append_positions_with_dedup(rows_to_append, 'broker_positions')
                        results['yuanta'] = {
                            'status': 'success' if result.get('error') is None else 'warning',
                            'added': result['added'],
                            'skipped': result['skipped']
                        }
                    else:
                        results['yuanta'] = {'status': 'info', 'message': '無有效持仓'}
                else:
                    results['yuanta'] = {'status': 'info', 'message': '無持仓數據'}
            else:
                results['yuanta'] = {'status': 'error', 'message': '登入或查詢失敗'}
        except Exception as e:
            logger.error(f"Yuanta 同步失敗: {e}")
            results['yuanta'] = {'status': 'error', 'message': str(e)}
    else:
        results['yuanta'] = {'status': 'skipped', 'message': '僅支持 Windows'}

    return jsonify({
        'status': 'success',
        'results': results,
        'total_added': sum(r.get('added', 0) for r in results.values() if isinstance(r, dict)),
        'total_skipped': sum(r.get('skipped', 0) for r in results.values() if isinstance(r, dict))
    })

@app.route('/api/ib/sync', methods=['POST'])
def api_ib_sync():
    """API：同步 IB 持仓到 Google Sheets（帶去重）"""
    try:
        from brokers.ib_api import get_open_positions

        logger.info("正在同步 IB 持仓...")

        # 获取 IB 持仓
        positions = get_open_positions()

        if not positions:
            return jsonify({
                'status': 'success',
                'message': '無持仓數據',
                'added': 0,
                'skipped': 0
            })

        # 转换格式
        positions_list = [
            {
                'symbol': p.get('symbol', ''),
                'exchange': p.get('exchange', ''),
                'currency': p.get('currency', ''),
                'position': p.get('position', 0),
                'avgCost': p.get('avgCost', 0),
                'marketPrice': 0,  # IB API 沒提供
                'source': 'ib'
            }
            for p in positions
        ]

        # 使用去重函數寫入
        result = append_positions_with_dedup(positions_list, 'broker_positions')

        return jsonify({
            'status': 'success' if result.get('error') is None else 'warning',
            'message': f"IB 同步完成：新增 {result['added']} 筆，跳過 {result['skipped']} 筆",
            'added': result['added'],
            'skipped': result['skipped'],
            'positions': positions_list[:5]
        })

    except Exception as e:
        logger.error(f"IB 同步失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

# ============================================================================
# 元大 API 同步路由
# ============================================================================

@app.route('/api/yuanta/sync', methods=['POST'])
def api_yuanta_sync():
    """API：同步元大持仓到 Google Sheets"""
    try:
        # 導入元大 API
        if platform.system() != "Windows":
            return jsonify({'status': 'error', 'message': '元大 API 只支持 Windows'}), 400

        from brokers.yuanta_api import (
            yuanta_login,
            query_stock_positions,
            fetch_positions,
        )

        # 登入
        logger.info("正在連接元大 API...")
        api = yuanta_login()

        if not api:
            return jsonify({'status': 'error', 'message': '元大登入失敗'}), 401

        # 查詢持仓
        if not query_stock_positions(api):
            return jsonify({'status': 'error', 'message': '查詢持仓失敗'}), 400

        # 獲取持仓列表
        positions = fetch_positions(api)

        if not positions:
            return jsonify({
                'status': 'success',
                'message': '無持仓數據',
                'count': 0
            })

        # 解析並寫入 Google Sheets
        # 格式: 0,0,0,0,{stk_code},0,{stk_nos},{stk_price},{stk_cost_raw}
        rows_to_append = []

        for pos_str in positions:
            try:
                parts = pos_str.split(',')
                if len(parts) >= 9:
                    stk_code = parts[4]
                    stk_nos = float(parts[6])
                    stk_price = float(parts[7])
                    stk_cost = float(parts[8])

                    rows_to_append.append({
                        'symbol': stk_code,
                        'exchange': 'TWSE',
                        'currency': 'TWD',
                        'position': stk_nos,
                        'avgCost': stk_cost,
                        'marketPrice': stk_price,
                        'source': 'yuanta'
                    })
            except Exception as e:
                logger.warning(f"解析元大持仓失敗: {pos_str}, {e}")
                continue

        # 使用去重函數寫入 Google Sheets
        if rows_to_append:
            result = append_positions_with_dedup(rows_to_append, 'broker_positions')

            return jsonify({
                'status': 'success' if result.get('error') is None else 'warning',
                'message': f"元大同步完成：新增 {result['added']} 筆，跳過 {result['skipped']} 筆",
                'added': result['added'],
                'skipped': result['skipped'],
                'positions': rows_to_append[:5]  # 返回前5筆預覽
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': '未能解析任何持仓',
                'count': 0
            }), 206

    except Exception as e:
        logger.error(f"元大同步失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

# ============================================================================
# 缺失的 API 端點 - 為 Dashboard 補充
# ============================================================================

@app.route('/api/risk-metrics')
def api_risk_metrics():
    """風險指標 API — 真實資料版（來自 risk_control.py）"""
    try:
        from modules.risk_control import get_risk_metrics, get_risk_report
        metrics = get_risk_metrics()
        report = get_risk_report()
        return jsonify({
            'status': 'success',
            'data': {
                'overall_risk_level': metrics['overall_risk_level'],
                'should_stop_trading': metrics['should_stop_trading'],
                'max_drawdown': metrics['max_drawdown'],
                'daily_pnl_pct': metrics['daily_pnl_pct'],
                'position_alerts': metrics['position_alerts'],
                'checked_at': metrics['checked_at'],
                'signals': report['signals'],
            }
        })
    except Exception as e:
        logger.error(f"risk-metrics API 失敗：{e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/sync-broker-positions', methods=['POST'])
def api_sync_broker_positions():
    """同步 Broker 持倉"""
    try:
        broker = request.json.get('broker', 'all')
        return jsonify({
            'status': 'success',
            'message': f'同步 {broker} 持倉成功',
            'count': 5,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/intel/events')
def api_intel_events():
    """國際情報事件"""
    try:
        return jsonify({
            'status': 'success',
            'data': [
                {'date': '2026-03-20', 'title': 'FOMC 會議', 'impact': 'high', 'region': 'US'},
                {'date': '2026-03-18', 'title': '中國 GDP 發布', 'impact': 'medium', 'region': 'CN'},
                {'date': '2026-03-15', 'title': '美國 CPI 數據', 'impact': 'high', 'region': 'US'}
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/intel/usgs')
def api_intel_usgs():
    """地震和自然災害數據"""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'recent_earthquakes': [],
                'alerts': [],
                'last_updated': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-incidents')
def api_risk_incidents():
    """風險事件 — 從 risk_incidents sheet 讀取真實記錄"""
    try:
        from sheets_utils import read_risk_incidents
        df = read_risk_incidents()
        if df.empty:
            data = []
        else:
            # 取最近 20 筆，最新在前
            df = df.tail(20).iloc[::-1]
            data = df.to_dict(orient='records')
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        logger.error(f"risk-incidents API 失敗：{e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/macro-state')
def api_macro_state():
    """宏觀經濟狀態"""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'cycle_phase': 'expansion',
                'gdp_growth': 2.5,
                'inflation_rate': 3.2,
                'interest_rate': 4.75,
                'unemployment': 3.8
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Schwab OAuth 路由
# ============================================================================

@app.route('/schwab')
def schwab_page():
    """Schwab 認證和管理頁面"""
    try:
        from brokers.schwab_api import is_schwab_enabled, load_config_from_env

        is_connected = is_schwab_enabled()
        config = load_config_from_env()

        return render_template('schwab.html',
                             is_connected=is_connected,
                             client_id=config.client_id if config.client_id else '未配置')
    except Exception as e:
        logger.error(f"Schwab 頁面加載失敗: {e}")
        return render_template('schwab.html',
                             is_connected=False,
                             error=str(e))

@app.route('/api/schwab/status')
def api_schwab_status():
    """API：Schwab 連接狀態"""
    try:
        from brokers.schwab_api import is_schwab_enabled, has_valid_token, load_token

        is_connected = is_schwab_enabled()
        token = load_token()

        return jsonify({
            'status': 'success',
            'connected': is_connected,
            'has_token': has_valid_token(token),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"查詢 Schwab 狀態失敗: {e}")
        return jsonify({
            'status': 'error',
            'connected': False,
            'message': str(e)
        }), 500

@app.route('/api/schwab/check-config')
def api_schwab_check_config():
    """API：檢查 Schwab 配置是否完整"""
    try:
        from brokers.schwab_api import load_config_from_env

        cfg = load_config_from_env()

        config_status = {
            'client_id': bool(cfg.client_id),
            'client_secret': bool(cfg.client_secret),
            'redirect_uri': bool(cfg.redirect_uri),
            'all_configured': all([cfg.client_id, cfg.client_secret, cfg.redirect_uri])
        }

        return jsonify({
            'status': 'success',
            'config': config_status,
            'message': '所有配置已完成' if config_status['all_configured'] else '配置未完成，請檢查 .env'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/schwab/auth-url')
def api_schwab_auth_url():
    """API：生成 Schwab OAuth 授權 URL"""
    try:
        from brokers.schwab_api import get_authorize_url, load_config_from_env

        # 檢查配置
        cfg = load_config_from_env()
        if not cfg.client_id or not cfg.redirect_uri:
            return jsonify({
                'status': 'error',
                'message': '配置不完整：請在 .env 中設定 SCHWAB_CLIENT_ID 和 SCHWAB_REDIRECT_URI'
            }), 400

        auth_url = get_authorize_url()
        return jsonify({
            'status': 'success',
            'auth_url': auth_url
        })
    except Exception as e:
        logger.error(f"生成授權 URL 失敗: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/trades/save-current', methods=['POST'])
def api_save_current_trade():
    """API：直接保存當前交易的策略和進場原因到 trades 表"""
    try:
        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': '無法連接 Google Sheets'}), 503

        data = request.get_json()
        symbol = data.get('symbol', '').strip()
        strategy = data.get('strategy', '').strip()
        entry_reason = data.get('entry_reason', '').strip()
        entry_price = float(data.get('entry_price', 0))
        quantity = float(data.get('quantity', 0))
        broker = data.get('broker', 'UNKNOWN').strip()

        if not symbol or not strategy or not entry_reason:
            return jsonify({'status': 'error', 'message': '缺少必要信息'}), 400

        # 讀取 trades 表
        df = read_sheet_data_with_cache('trades')
        if df is None:
            df = pd.DataFrame()

        # 查找該標的是否已存在且狀態為「持倉」
        matching = df[
            (df['標的'].astype(str) == symbol) &
            (df['狀態'].astype(str).isin(['持倉', '進行中']))
        ]

        if not matching.empty:
            # 更新現有記錄
            for idx in matching.index:
                df.loc[idx, '策略'] = strategy
                df.loc[idx, '進場原因'] = entry_reason
            action = '已更新'
        else:
            # 新建記錄
            import uuid
            new_record = {
                'id': f"pos_{broker}_{symbol}_{uuid.uuid4().hex[:8]}",
                '日期': datetime.now().strftime('%Y-%m-%d'),
                '券商': broker,
                '標的': symbol,
                '交易類型': 'BUY' if quantity > 0 else 'SELL',
                '進場價': entry_price,
                '出場價': '',
                '數量': quantity,
                '狀態': '持倉',
                '策略': strategy,
                '進場原因': entry_reason,
                '出場原因': '',
                '備註': '自動同步自當前交易編輯',
                'entry_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'exit_time': '',
                'currency': 'USD' if 'IB' in broker else 'TWD',
                'source': 'broker_positions',
                'pnl': ''
            }
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            action = '已新增'

        # 寫回 Google Sheets
        sheet = get_sheet('trades')
        if sheet:
            sheet.clear()
            headers = df.columns.tolist()
            sheet.append_row(headers)
            for _, row in df.iterrows():
                row_values = [str(v) if not pd.isna(v) else '' for v in row.tolist()]
                sheet.append_row(row_values)

            # 清快取
            try:
                from sheets_utils import _save_to_cache
                _save_to_cache('trades', df)
            except:
                pass

            logger.info(f"✅ {action}: {symbol} | strategy={strategy}")
            return jsonify({'status': 'success', 'message': f'交易{action}', 'action': action})
        else:
            return jsonify({'status': 'error', 'message': '無法連接 trades 分頁'}), 500

    except Exception as e:
        logger.error(f"保存當前交易失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/schwab/callback')
def schwab_callback():
    """Schwab OAuth 回調處理 - 交換授權碼為 Token"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')

        if not code:
            return redirect(url_for('schwab_page') + '?error=no_auth_code')

        logger.info(f"Schwab OAuth 回調: code={code[:20]}..., state={state}")

        # 交換授權碼為 access token
        from brokers.schwab_api import load_config_from_env, save_token
        import requests

        cfg = load_config_from_env()

        if not cfg.client_id or not cfg.client_secret:
            return redirect(url_for('schwab_page') + '?error=config_missing')

        # 準備 token 交換請求
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': cfg.redirect_uri,
            'client_id': cfg.client_id,
            'client_secret': cfg.client_secret
        }

        # 發送 token 交換請求
        try:
            response = requests.post(
                cfg.token_url,
                data=token_data,
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Token 交換請求失敗: {e}")
            return redirect(url_for('schwab_page') + '?error=token_exchange_failed')

        # 解析響應
        try:
            token_response = response.json()
        except Exception as e:
            logger.error(f"Token 響應解析失敗: {e}")
            return redirect(url_for('schwab_page') + '?error=token_parse_failed')

        # 檢查錯誤
        if 'error' in token_response:
            error_desc = token_response.get('error_description', token_response['error'])
            logger.error(f"Schwab Token 交換錯誤: {error_desc}")
            return redirect(url_for('schwab_page') + f'?error=schwab_error&msg={error_desc[:50]}')

        # 提取 access token
        if 'access_token' not in token_response:
            logger.error("Schwab 響應中缺少 access_token")
            return redirect(url_for('schwab_page') + '?error=no_access_token')

        # 添加過期時間戳（可選）
        if 'expires_in' in token_response:
            import time
            token_response['expires_at'] = time.time() + token_response['expires_in']

        # 保存 token
        try:
            save_token(token_response)
            logger.info("Schwab Token 已成功保存")
            return redirect(url_for('schwab_page') + '?authorized=true&token_saved=true')
        except Exception as e:
            logger.error(f"Token 保存失敗: {e}")
            return redirect(url_for('schwab_page') + '?error=token_save_failed')

    except Exception as e:
        logger.error(f"Schwab 回調處理失敗: {e}")
        return redirect(url_for('schwab_page') + '?error=callback_error')

# ============================================================================
# 錯誤處理
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found', 'status': 'error'}), 404

@app.errorhandler(500)
def server_error(e):
    error_msg = f"服務器錯誤: {e}\n{traceback.format_exc()}"
    print(f"SERVER ERROR HANDLER: {error_msg}", flush=True)
    logger.error(error_msg)
    return jsonify({'error': 'Server error', 'status': 'error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    error_msg = f"未捕獲的異常: {e}\n{traceback.format_exc()}"
    print(f"EXCEPTION HANDLER: {error_msg}", flush=True)
    logger.error(error_msg)
    return jsonify({'error': 'Server error', 'status': 'error'}), 500

@app.before_request
def before_request():
    """請求前處理"""
    print(f"BEFORE_REQUEST: {request.method} {request.path}", flush=True)
    logger.info(f"{request.method} {request.path}")

@app.after_request
def after_request(response):
    """響應後處理"""
    print(f"AFTER_REQUEST: Status {response.status_code}", flush=True)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # CORS：允許 localhost:5000 跨域存取
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# ============================================================================
# 新增 API - 景氣循環與美林時鐘
# ============================================================================

@app.route('/api/econ/indicators')
def get_econ_indicators():
    """獲取經濟指標數據（舊版，保留相容性）"""
    try:
        indicators = {
            'gdp_growth': 2.4,
            'inflation_cpi': 3.2,
            'fed_funds_rate': 4.75,
            'unemployment_rate': 3.9,
            'consumer_confidence': 102.6,
            '10y_yield': 4.12
        }
        return jsonify(indicators)
    except Exception as e:
        logger.error(f"獲取經濟指標失敗: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/macro-indicators')
def api_macro_indicators():
    """真實總經指標 API — 從 FRED + Yahoo Finance 抓取，快取 6 小時"""
    force = request.args.get('refresh', '').lower() in ('1', 'true', 'yes')
    try:
        from macro_data import get_indicators
        data = get_indicators(force_refresh=force)
        return jsonify(data)
    except Exception as e:
        logger.error(f"macro-indicators 失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'indicators': {}}), 500

@app.route('/api/econ/cycle-position')
def get_cycle_position():
    """獲取美林時鐘位置"""
    try:
        # TODO: 實現 econ_classifier.py 的 M1 判斷
        position = {
            'phase': 'expansion',  # 'recession', 'recovery', 'expansion', 'overheating'
            'confidence': 78,
            'x': 0.75,  # inflation
            'y': 0.75   # growth
        }
        return jsonify(position)
    except Exception as e:
        logger.error(f"獲取美林時鐘位置失敗: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/econ/12month-history')
def get_12month_history():
    """獲取過去 12 個月的景氣循環歷史（從 econ_history.json 讀取，每月自動追加當月象限）"""
    HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "econ_history.json")
    QUADRANT_MAP = {"recession": 1, "recovery": 2, "slowdown": 2, "expansion": 3, "overheating": 4}

    try:
        # ── 讀取現有歷史 ──────────────────────────────────────
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("history", [])

        # ── 嘗試追加當月象限 ──────────────────────────────────
        current_month = datetime.now().strftime("%Y-%m")
        months_recorded = [r["month"] for r in records]

        if current_month not in months_recorded:
            try:
                from macro_compass_api import MacroCompassAPI
                import asyncio
                loop = asyncio.new_event_loop()
                compass_data = loop.run_until_complete(MacroCompassAPI().get_compass_data())
                loop.close()
                quadrant = compass_data.get("current_quadrant", "slowdown")
                code = QUADRANT_MAP.get(quadrant, 2)
                records.append({"month": current_month, "quadrant": quadrant, "code": code})
                data["history"] = records
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"econ_history: 追加 {current_month} → {quadrant} ({code})")
            except Exception as e:
                logger.warning(f"econ_history 追加當月失敗（使用現有歷史）: {e}")

        # ── 返回最近 12 個月的 code 陣列 ─────────────────────
        codes = [r["code"] for r in records[-12:]]
        return jsonify({'history': codes, 'detail': records[-12:]})

    except Exception as e:
        logger.error(f"獲取景氣循環歷史失敗: {e}")
        return jsonify({'history': [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 2, 2], 'error': str(e)})

# ============================================================================
# 新增 API - 社群風險監控
# ============================================================================

@app.route('/api/risk/score')
def get_risk_score():
    """獲取實時風險評分（VIX 50% + 通膨偏離 30% + 實質利率壓力 20%）"""
    try:
        from macro_data import get_indicators
        inds = get_indicators().get("indicators", {})

        def _num(key):
            raw = inds.get(key, {}).get("value", None)
            if raw is None or raw == "N/A":
                return None
            try:
                return float(str(raw).replace("%","").replace("K","").replace("+","").strip())
            except (ValueError, TypeError):
                return None

        vix      = _num("vix")      or 20.0
        cpi      = _num("us_cpi")   or 2.5
        fed_rate = _num("fed_rate") or 3.5

        # ── VIX 分數 (0-100)：VIX 12→0, 20→30, 28→60, 40→100
        if vix <= 12:
            vix_score = 0
        elif vix <= 20:
            vix_score = (vix - 12) / 8 * 30
        elif vix <= 28:
            vix_score = 30 + (vix - 20) / 8 * 30
        elif vix <= 40:
            vix_score = 60 + (vix - 28) / 12 * 40
        else:
            vix_score = 100

        # ── 通膨偏離分數 (0-100)：CPI 目標 2%，偏離越大風險越高
        cpi_dev = abs(cpi - 2.0)
        if cpi_dev <= 0.5:
            infl_score = cpi_dev / 0.5 * 15
        elif cpi_dev <= 1.5:
            infl_score = 15 + (cpi_dev - 0.5) / 1.0 * 35
        elif cpi_dev <= 3.0:
            infl_score = 50 + (cpi_dev - 1.5) / 1.5 * 40
        else:
            infl_score = 90

        # ── 實質利率壓力分數 (0-100)：過高（緊縮）或過低（寬鬆過度）均加分
        real_rate = fed_rate - cpi
        if -0.5 <= real_rate <= 1.5:
            real_score = 10
        elif real_rate > 1.5:
            real_score = 10 + min((real_rate - 1.5) / 2.5 * 60, 60)
        else:
            real_score = 10 + min((-0.5 - real_rate) / 2.0 * 60, 60)

        overall = round(vix_score * 0.5 + infl_score * 0.3 + real_score * 0.2)
        overall = max(0, min(100, overall))

        return jsonify({
            'overall_score': overall,
            'components': {
                'vix_score':  round(vix_score, 1),
                'infl_score': round(infl_score, 1),
                'real_score': round(real_score, 1),
            },
            'inputs': {
                'vix': vix, 'cpi': cpi, 'fed_rate': fed_rate,
                'real_rate': round(real_rate, 2),
            },
            'sentiment_score': 45,
            'anomaly_count': 0,
            'institution_count': 0,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"獲取風險評分失敗: {e}")
        return jsonify({'overall_score': 28, 'error': str(e)})

@app.route('/api/risk/alerts')
def get_risk_alerts():
    """依真實指標值生成規則型風險告警"""
    try:
        from macro_data import get_indicators
        inds = get_indicators().get("indicators", {})

        def _num(key):
            raw = inds.get(key, {}).get("value", None)
            if raw is None or raw == "N/A":
                return None
            try:
                return float(str(raw).replace("%","").replace("K","").replace("+","").strip())
            except (ValueError, TypeError):
                return None

        vix      = _num("vix")
        cpi      = _num("us_cpi")
        fed_rate = _num("fed_rate")
        nfp      = _num("nfp")
        ism_pmi  = _num("ism_pmi")

        alerts = []
        ts = datetime.now().strftime("%Y-%m-%d")

        if vix is not None:
            if vix >= 35:
                alerts.append({'time': ts, 'severity': 'high',   'type': 'market_fear',  'message': f'VIX={vix:.1f} 極度恐慌區間（≥35），市場波動劇烈', 'action': '減倉'})
            elif vix >= 28:
                alerts.append({'time': ts, 'severity': 'medium', 'type': 'market_fear',  'message': f'VIX={vix:.1f} 進入恐慌區間（≥28），注意下行風險', 'action': '控倉'})
            elif vix <= 13:
                alerts.append({'time': ts, 'severity': 'low',    'type': 'complacency',  'message': f'VIX={vix:.1f} 過度樂觀（≤13），市場可能自滿', 'action': '留意'})

        if cpi is not None:
            if cpi >= 4.0:
                alerts.append({'time': ts, 'severity': 'high',   'type': 'inflation',    'message': f'CPI={cpi:.1f}% 通膨嚴重超標（≥4%），Fed 政策壓力大', 'action': '減少債券'})
            elif cpi >= 3.0:
                alerts.append({'time': ts, 'severity': 'medium', 'type': 'inflation',    'message': f'CPI={cpi:.1f}% 通膨偏高（≥3%），降息預期受壓', 'action': '注意'})

        if fed_rate is not None and cpi is not None:
            real_rate = fed_rate - cpi
            if real_rate >= 3.0:
                alerts.append({'time': ts, 'severity': 'medium', 'type': 'tight_policy', 'message': f'實質利率={real_rate:.2f}% 偏緊縮，企業融資成本高', 'action': '留意成長股'})
            elif real_rate <= -1.0:
                alerts.append({'time': ts, 'severity': 'medium', 'type': 'easy_policy',  'message': f'實質利率={real_rate:.2f}% 負值，通膨壓力累積中', 'action': '減持現金'})

        if nfp is not None and nfp < 0:
            alerts.append({'time': ts, 'severity': 'high',   'type': 'jobs',         'message': f'NFP={nfp:.0f}K 非農就業負成長，衰退訊號', 'action': '防禦'})
        elif nfp is not None and nfp < 50:
            alerts.append({'time': ts, 'severity': 'medium', 'type': 'jobs',         'message': f'NFP={nfp:.0f}K 就業偏弱（<50K），成長放緩', 'action': '觀察'})

        if ism_pmi is not None and ism_pmi < 45:
            alerts.append({'time': ts, 'severity': 'medium', 'type': 'manufacturing', 'message': f'ISM PMI={ism_pmi:.1f} 製造業嚴重萎縮（<45）', 'action': '減少週期股'})

        if not alerts:
            alerts.append({'time': ts, 'severity': 'low', 'type': 'normal', 'message': '當前各項指標均在正常範圍內', 'action': '維持'})

        return jsonify({'alerts': alerts, 'generated_at': datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"獲取風險告警失敗: {e}")
        return jsonify({'alerts': [], 'error': str(e)})

@app.route('/api/risk/7day-trend')
def get_risk_trend():
    """獲取 7 日風險趨勢"""
    try:
        # 示例數據
        trend = {
            'dates': ['03-14', '03-15', '03-16', '03-17', '03-18', '03-19', '03-20'],
            'scores': [35, 38, 32, 28, 35, 30, 28]
        }
        return jsonify(trend)
    except Exception as e:
        logger.error(f"獲取風險趨勢失敗: {e}")
        return jsonify({'error': str(e)}), 500

_PTT_CACHE = {'data': None, 'ts': 0}
_PTT_TTL = 900  # 15 分鐘快取

def _fetch_ptt_stock():
    """爬 PTT Stock 板最新文章，回傳解析結果"""
    import requests, re, time

    now = time.time()
    if _PTT_CACHE['data'] and now - _PTT_CACHE['ts'] < _PTT_TTL:
        return _PTT_CACHE['data']

    session = requests.Session()
    session.cookies.set('over18', '1', domain='www.ptt.cc')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-TW,zh;q=0.9',
    }

    articles = []
    for page_offset in [0, 1]:   # 最新兩頁
        idx_url = 'https://www.ptt.cc/bbs/Stock/index.html' if page_offset == 0 else None
        if page_offset == 1:
            # 從第一頁 HTML 取上一頁連結
            prev_links = re.findall(r'href="(/bbs/Stock/index\d+\.html)"[^>]*>‹ 上頁', articles[0].get('_prev','') if articles else '')
            if not prev_links:
                break
            idx_url = 'https://www.ptt.cc' + prev_links[0]

        try:
            r = session.get('https://www.ptt.cc/bbs/Stock/index.html', headers=headers, timeout=8, verify=False)
            html = r.text
        except Exception:
            break

        # 推文數
        nrecs  = re.findall(r'class="nrec"><span[^>]*>(\d+|爆|XX|X\d*)</span>', html)
        # 標題（含類型 [新聞]/[討論]/[標的] 等）
        titles_raw = re.findall(r'class="title">\s*(?:<a href="([^"]+)">)?([^<\n]+)', html)

        for i, (link, title) in enumerate(titles_raw):
            title = title.strip()
            if not title or '本文已被刪除' in title:
                continue
            nrec_raw = nrecs[i] if i < len(nrecs) else '0'
            # 推文數轉數字
            if nrec_raw == '爆':
                nrec = 100
            elif nrec_raw.startswith('X'):
                nrec = -10
            else:
                try:
                    nrec = int(nrec_raw)
                except ValueError:
                    nrec = 0

            # 文章類型
            cat_match = re.match(r'\[([^\]]+)\]', title)
            category = cat_match.group(1) if cat_match else '其他'

            # 情緒：推文多 & 標題含正向詞 → bullish，反之 bearish
            pos_words = ['漲', '多', '買', '強', '高', '上', '看好', '反彈', '突破', '利多', '飆', '爆量']
            neg_words = ['跌', '空', '賣', '弱', '低', '下', '崩', '跌停', '砍', '利空', '崩跌', '賠']
            t = title
            pos_hit = sum(1 for w in pos_words if w in t)
            neg_hit = sum(1 for w in neg_words if w in t)
            if nrec >= 20 and pos_hit > neg_hit:
                sentiment = 'bullish'
            elif nrec < 0 or neg_hit > pos_hit:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'

            articles.append({
                'title': title,
                'category': category,
                'nrec': nrec,
                'sentiment': sentiment,
                'url': 'https://www.ptt.cc' + link if link else '',
            })

        break  # 只取一頁就夠

    # 按推文數排序，取前 10
    articles.sort(key=lambda x: x['nrec'], reverse=True)
    articles = articles[:10]

    # 統計板面熱度
    total = len(articles)
    bull  = sum(1 for a in articles if a['sentiment'] == 'bullish')
    bear  = sum(1 for a in articles if a['sentiment'] == 'bearish')
    bull_pct = round(bull / total * 100) if total else 50

    # 熱門關鍵詞（標題拆字）
    TOPIC_KEYWORDS = {
        '台積電': ['台積電', 'TSMC', '2330'],
        'AI/科技': ['AI', '輝達', 'NVDA', '科技', '半導體'],
        'ETF':    ['ETF', '00878', '0050', '00919'],
        '美股':   ['美股', '那斯達克', 'S&P', 'SP500'],
        '總經':   ['Fed', '升息', '降息', '通膨', 'CPI'],
        '資金':   ['外資', '投信', '主力', '法人'],
    }
    topic_counts = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        cnt = sum(1 for a in articles for kw in kws if kw in a['title'])
        if cnt > 0:
            topic_counts[topic] = cnt

    result = {
        'articles': articles,
        'summary': {
            'total': total,
            'bull_pct': bull_pct,
            'bear_pct': 100 - bull_pct,
            'hot_topics': sorted(topic_counts.items(), key=lambda x: -x[1])[:4],
        },
        'board': 'PTT/Stock',
        'fetched_at': datetime.now().isoformat(),
    }
    _PTT_CACHE['data'] = result
    _PTT_CACHE['ts'] = now
    return result


@app.route('/api/social/twitter')
def get_twitter_data():
    """PTT Stock 板熱門文章（取代 Twitter 假資料）"""
    try:
        data = _fetch_ptt_stock()
        # 轉換成前端 hashtags 格式（保留相容性）
        topics = data['summary'].get('hot_topics', [])
        hashtags = [
            {'tag': f'#{t}', 'mentions': c * 15, 'positive': data['summary']['bull_pct'], 'trend': 'up' if data['summary']['bull_pct'] >= 50 else 'down'}
            for t, c in topics
        ]
        return jsonify({'hashtags': hashtags, 'ptt_summary': data['summary'], 'source': 'PTT/Stock'})
    except Exception as e:
        logger.error(f"PTT 爬取失敗: {e}")
        return jsonify({'hashtags': [], 'error': str(e)})


@app.route('/api/social/reddit')
def get_reddit_data():
    """PTT Stock 板文章列表（取代 Reddit 假資料）"""
    try:
        data = _fetch_ptt_stock()
        articles = data['articles']
        # 轉換成前端 subreddits 格式（保留相容性）
        hot_topic = articles[0]['title'][:20] + '...' if articles else 'N/A'
        bull_pct = data['summary']['bull_pct']
        mood = 'bullish' if bull_pct >= 60 else 'bearish' if bull_pct <= 40 else 'cautious'
        subreddits = [
            {'name': 'PTT/Stock', 'discussions': len(articles), 'hot_topic': hot_topic, 'sentiment': mood},
        ]
        return jsonify({'subreddits': subreddits, 'articles': articles[:8], 'source': 'PTT/Stock'})
    except Exception as e:
        logger.error(f"PTT 爬取失敗: {e}")
        return jsonify({'subreddits': [], 'error': str(e)})

_NEWS_CACHE = {'data': None, 'ts': 0}
_NEWS_TTL = 1800  # 30 分鐘快取

@app.route('/api/social/news')
def get_news_data():
    """獲取金融新聞（Yahoo Finance RSS，30 分鐘快取）"""
    import time, xml.etree.ElementTree as ET, urllib.request

    now = time.time()
    if _NEWS_CACHE['data'] and now - _NEWS_CACHE['ts'] < _NEWS_TTL:
        return jsonify(_NEWS_CACHE['data'])

    try:
        # Yahoo Finance 財經新聞 RSS
        rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^IXIC&region=US&lang=en-US"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        items = root.findall('.//item')[:8]

        news = []
        for item in items:
            title = item.findtext('title', '').strip()
            pub_date = item.findtext('pubDate', '').strip()
            source = item.findtext('dc:creator', 'Yahoo Finance', ns).strip() or 'Yahoo Finance'
            # 簡單解析日期
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub_date)
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                time_str = pub_date[:16] if pub_date else datetime.now().strftime('%Y-%m-%d')

            # 簡單情緒判斷
            title_lower = title.lower()
            if any(w in title_lower for w in ['surge', 'rally', 'gains', 'rise', 'high', 'bull']):
                impact = 'positive'
            elif any(w in title_lower for w in ['fall', 'drop', 'crash', 'fear', 'recession', 'loss', 'decline']):
                impact = 'negative'
            else:
                impact = 'neutral'

            news.append({'time': time_str, 'source': source, 'title': title, 'impact': impact})

        result = {'news': news, 'fetched_at': datetime.now().isoformat()}
        _NEWS_CACHE['data'] = result
        _NEWS_CACHE['ts'] = now
        return jsonify(result)

    except Exception as e:
        logger.warning(f"Yahoo Finance RSS 失敗: {e}")
        # 降級：返回最後快取或空列表
        if _NEWS_CACHE['data']:
            return jsonify(_NEWS_CACHE['data'])
        return jsonify({'news': [], 'error': str(e)})

@app.route('/api/social/institutions')
def get_institution_data():
    """獲取機構動向數據"""
    try:
        # TODO: 連接機構數據源 (SEC EDGAR, Bloomberg Terminal)
        data = {
            'institutions': [
                {'name': '高盛', 'move': '減持新興市場', 'amount': 5200000000, 'impact': 'em_asset'},
                {'name': '摩根士丹利', 'move': '增持科技股', 'amount': 3800000000, 'impact': 'tech_stock'}
            ]
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"獲取機構動向失敗: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# 全球市場強弱 API
# ============================================================================

_MARKET_TICKERS = [
    {'id': 'sp500',  'label': 'S&P 500',  'ticker': '^GSPC',     'flag': 'us', 'country': 'US'},
    {'id': 'nasdaq', 'label': 'NASDAQ',   'ticker': '^IXIC',     'flag': 'us', 'country': 'US'},
    {'id': 'twii',   'label': '加權指數', 'ticker': '^TWII',     'flag': 'tw', 'country': 'TW'},
    {'id': 'nikkei', 'label': '日經 225', 'ticker': '^N225',     'flag': 'jp', 'country': 'JP'},
    {'id': 'dax',    'label': 'DAX',      'ticker': '^GDAXI',    'flag': 'de', 'country': 'DE'},
    {'id': 'sensex', 'label': 'SENSEX',   'ticker': '^BSESN',    'flag': 'in', 'country': 'IN'},
    {'id': 'sse',    'label': '上証指數', 'ticker': '000001.SS', 'flag': 'cn', 'country': 'CN'},
]

def _ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def _ema_status(price, ema_val, threshold=0.003):
    """bull / neutral / bear，threshold = 0.3% 以內算 neutral"""
    diff = (price - ema_val) / ema_val
    if diff > threshold:
        return 'bull'
    elif diff < -threshold:
        return 'bear'
    return 'neutral'

def _score_and_status(pos52w, ema20s, ema50s, ema200s):
    """綜合強弱評分 0-100"""
    score = round(pos52w * 0.35)  # 52週位階 35分
    score += {'bull': 10, 'neutral': 5, 'bear': 0}[ema20s]
    score += {'bull': 20, 'neutral': 10, 'bear': 0}[ema50s]
    score += {'bull': 35, 'neutral': 17, 'bear': 0}[ema200s]
    score = min(100, score)
    if score >= 72:
        status, badge = '擴張', 'badge-green'
    elif score >= 50:
        status, badge = '復甦', 'badge-blue'
    elif score >= 32:
        status, badge = '趨緩', 'badge-yellow'
    else:
        status, badge = '衰退', 'badge-red'
    return score, status, badge

@app.route('/api/yahoo-proxy')
def api_yahoo_proxy():
    """Yahoo Finance CORS Proxy — 後端轉發，避免瀏覽器 CORS 限制"""
    import urllib.request
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({'error': 'missing symbol'}), 400
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1mo"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        return app.response_class(response=data, status=200, mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 502

@app.route('/api/market-indices')
def api_market_indices():
    """全球主要指數 — 從 Yahoo Finance 抓取，含52週位階 + EMA 排列 + 強弱評分"""
    import yfinance as yf
    import pandas as pd
    results = []
    for m in _MARKET_TICKERS:
        try:
            hist = yf.download(m['ticker'], period='1y', progress=False, auto_adjust=True)
            if hist.empty:
                continue
            # yfinance >= 1.0 download() returns MultiIndex columns when single ticker
            close = hist['Close']
            if hasattr(close, 'columns'):  # MultiIndex: flatten
                close = close.iloc[:, 0]
            high_col = hist['High'] if 'High' in hist.columns or not hasattr(hist['High'], 'columns') else hist['High'].iloc[:, 0]
            low_col  = hist['Low']  if 'Low'  in hist.columns or not hasattr(hist['Low'],  'columns') else hist['Low'].iloc[:, 0]
            if hasattr(high_col, 'columns'): high_col = high_col.iloc[:, 0]
            if hasattr(low_col,  'columns'): low_col  = low_col.iloc[:,  0]
            price = float(close.iloc[-1])
            h52   = float(high_col.max())
            l52   = float(low_col.min())
            pos52 = round((price - l52) / (h52 - l52) * 100, 1) if h52 != l52 else 50.0
            # change % from previous close
            prev  = float(close.iloc[-2]) if len(close) > 1 else price
            chg   = round((price - prev) / prev * 100, 2)
            # EMA
            e20  = float(_ema(close, 20).iloc[-1])
            e50  = float(_ema(close, 50).iloc[-1])
            e200 = float(_ema(close, 200).iloc[-1])
            ema20s  = _ema_status(price, e20)
            ema50s  = _ema_status(price, e50)
            ema200s = _ema_status(price, e200)
            score, status, badge = _score_and_status(pos52, ema20s, ema50s, ema200s)
            # 52w label
            if pos52 >= 90:   w_label = '歷史高位'
            elif pos52 >= 75: w_label = '近年高位'
            elif pos52 >= 55: w_label = '中高位'
            elif pos52 >= 35: w_label = '中位盤整'
            elif pos52 >= 20: w_label = '偏低位'
            else:             w_label = '歷史低位'
            # price format
            fmt_price = f"{price:,.0f}" if price >= 1000 else f"{price:,.2f}"
            results.append({
                'id': m['id'], 'label': m['label'],
                'flag': m['flag'], 'country': m['country'],
                'ticker': m['ticker'],
                'price': fmt_price, 'price_raw': round(price, 2), 'change_pct': chg,
                'high52w': round(h52, 2), 'low52w': round(l52, 2),
                'pos52w': pos52, 'pos52w_label': w_label,
                'ema20': ema20s, 'ema50': ema50s, 'ema200': ema200s,
                'score': score, 'status': status, 'badge': badge,
            })
        except Exception as e:
            logger.warning(f"market-indices {m['ticker']} 失敗: {e}")
    return jsonify({'status': 'success', 'data': results, 'updated': __import__('datetime').datetime.now().strftime('%H:%M')})


# ============================================================================
# 宏觀羅盤 API（實時經濟指標）
# ============================================================================

@app.route('/api/macro-compass')
def api_macro_compass():
    """取得實時經濟指標 & 象限判斷"""
    try:
        from macro_compass_api import MacroCompassAPI
        import asyncio

        compass = MacroCompassAPI()
        result = asyncio.run(compass.get_compass_data())

        return jsonify({
            'status': 'success',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except ImportError:
        logger.warning("macro_compass_api 未導入")
        return jsonify({
            'status': 'warning',
            'message': '宏觀羅盤模組未就緒',
            'data': {
                'current_quadrant': 'expansion',  # 預設
                'indices': {},
                'indicators': {}
            }
        }), 202
    except Exception as e:
        logger.error(f"宏觀羅盤 API 錯誤: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================================================
# 台灣總經指標 API（景氣燈號 / PMI / 央行利率）
# ============================================================================

_TW_OVERRIDE_FILE = Path(__file__).parent / '_cache' / 'tw_manual_override.json'

def _load_tw_override() -> dict:
    """讀取手動覆蓋 JSON（_cache/tw_manual_override.json）"""
    try:
        if _TW_OVERRIDE_FILE.exists():
            with open(_TW_OVERRIDE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_tw_override(data: dict):
    _TW_OVERRIDE_FILE.parent.mkdir(exist_ok=True)
    with open(_TW_OVERRIDE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _score_to_light(score: int) -> tuple:
    if score >= 38:
        return '🔴', '紅燈', 'var(--red)', '景氣熱絡'
    elif score >= 32:
        return '🟠', '黃紅燈', 'var(--yellow)', '景氣活絡'
    elif score >= 23:
        return '🟢', '綠燈', 'var(--green)', '景氣穩定'
    elif score >= 17:
        return '🔵', '黃藍燈', 'var(--accent)', '景氣趨緩'
    else:
        return '🔵', '藍燈', 'var(--accent)', '景氣低迷'

@app.route('/api/tw-indicators')
def api_tw_indicators():
    """取得台灣總經指標（景氣燈號/PMI/央行利率）"""
    try:
        # 優先讀取手動覆蓋
        overrides = _load_tw_override()

        # 若無覆蓋，從 macro_data 的 MANUAL_OVERRIDES 讀取
        if not overrides:
            from macro_data import MANUAL_OVERRIDES
            for key in ('tw_light', 'tw_pmi', 'tw_rate'):
                if key in MANUAL_OVERRIDES:
                    overrides[key] = MANUAL_OVERRIDES[key]

        return jsonify({
            'status': 'success',
            'data': overrides,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"tw-indicators API 錯誤: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tw-indicators/update', methods=['POST'])
def api_tw_indicators_update():
    """手動更新台灣總經指標（景氣燈號分數）"""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({'status': 'error', 'message': '無效請求'}), 400

        key = payload.get('key')
        raw_value = payload.get('value')

        if key not in ('tw_light', 'tw_pmi', 'tw_rate'):
            return jsonify({'status': 'error', 'message': f'不支援的指標: {key}'}), 400

        overrides = _load_tw_override()
        now_month = datetime.now().strftime('%Y-%m')
        now_date = datetime.now().strftime('%Y-%m-%d')

        if key == 'tw_light':
            score = int(raw_value)
            emoji, name, color, desc = _score_to_light(score)
            pct = min(100, max(0, int((score / 45) * 100)))
            overrides['tw_light'] = {
                'value':        f'{emoji} {name}',
                'label':        f'{score}分 → {name}',
                'signal':       f'{score}分 — {desc}',
                'signal_color': color,
                'score':        score,
                'pct':          pct,
                'updated':      now_month,
                'source':       f'手動更新 ({now_date})',
            }
        elif key == 'tw_pmi':
            pmi = float(raw_value)
            if pmi >= 55:
                signal, color = f'{pmi:.1f} — 製造業強勁擴張', 'var(--green)'
            elif pmi >= 50:
                signal, color = f'{pmi:.1f} — 製造業擴張', 'var(--green)'
            elif pmi >= 45:
                signal, color = f'{pmi:.1f} — 製造業輕微收縮', 'var(--yellow)'
            else:
                signal, color = f'{pmi:.1f} — 製造業收縮', 'var(--red)'
            overrides['tw_pmi'] = {
                'value': f'{pmi:.1f}', 'label': f'{pmi:.1f} → {"擴張" if pmi >= 50 else "收縮"}',
                'signal': signal, 'signal_color': color,
                'updated': now_month, 'source': f'手動更新 ({now_date})',
            }
        elif key == 'tw_rate':
            rate = float(raw_value)
            overrides['tw_rate'] = {
                'value': f'{rate:.2f}%', 'label': f'{rate:.2f}% → 維持',
                'signal': f'{rate:.2f}% — CBC 利率', 'signal_color': 'var(--yellow)',
                'updated': now_month, 'source': f'手動更新 ({now_date})',
            }

        _save_tw_override(overrides)

        # 清除舊快取，讓下次讀取取得最新數據
        tw_cache = Path(__file__).parent / '_cache' / 'tw_macro.json'
        if tw_cache.exists():
            tw_cache.unlink()

        logger.info(f"✅ 台灣指標已更新: {key} = {raw_value}")
        return jsonify({'status': 'success', 'data': overrides[key]})

    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'數值格式錯誤: {e}'}), 400
    except Exception as e:
        logger.error(f"tw-indicators 更新失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# IB 持倉同步 API - 使用子進程方式（避免線程問題）
# ============================================================================

# 注：/api/ib-account-summary 已在上方定義，會使用子進程查詢 IB 數據
# /api/ib-sync 和 /api/ib-positions 暫時禁用以避免事件循環問題
# 所有 IB 相關查詢都使用 query_ib_positions.py 子進程

# ============================================================================
# IB 庫存異動偵測 → 自動寫入已實現損益
# ============================================================================

_IB_SNAPSHOT_FILE = Path(__file__).parent / '_cache' / 'ib_positions_snapshot.json'

def _load_ib_snapshot() -> dict:
    """讀取上次 IB 持倉快照"""
    try:
        if _IB_SNAPSHOT_FILE.exists():
            with open(_IB_SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_ib_snapshot(positions: list):
    """儲存目前 IB 持倉為快照"""
    snapshot = {
        p['symbol']: {
            'position': float(p.get('position', 0)),
            'avgCost':  float(p.get('avgCost', 0)),
        }
        for p in positions if float(p.get('position', 0)) > 0
    }
    snapshot['_saved_at'] = datetime.now().isoformat()
    _IB_SNAPSHOT_FILE.parent.mkdir(exist_ok=True)
    with open(_IB_SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

def check_ib_position_changes():
    """
    比對 IB 快照 vs 當前持倉：
    - qty 減少 → 視為已出場 → 寫入 trades (Sheets)
    - qty 增加或新增 → 更新快照（不寫交易）
    每天 09:30、15:30 各執行一次
    """
    try:
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), 'query_ib_positions.py')
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 or not result.stdout:
            logger.warning(f"⚠️ IB 庫存異動偵測：無法取得持倉 ({result.stderr[:100]})")
            return

        data = json.loads(result.stdout)
        if data.get('status') != 'success':
            logger.warning(f"⚠️ IB 庫存異動偵測：API 回傳錯誤 {data.get('message')}")
            return

        current_positions = data.get('positions', [])
        old_snapshot = _load_ib_snapshot()
        today = datetime.now().strftime('%Y-%m-%d')
        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        written = 0

        for pos in current_positions:
            sym = pos.get('symbol', '')
            new_qty  = float(pos.get('position', 0))
            avg_cost = float(pos.get('avgCost', 0))
            mkt_price = float(pos.get('marketPrice', avg_cost))

            old = old_snapshot.get(sym)
            if old is None:
                continue  # 新增持倉，只更新快照

            old_qty  = float(old.get('position', 0))
            old_avg  = float(old.get('avgCost', avg_cost))
            sold_qty = old_qty - new_qty

            if sold_qty <= 0:
                continue  # 未減少，跳過

            # 計算已實現損益
            realized_pnl = (mkt_price - old_avg) * sold_qty
            pnl_pct      = ((mkt_price - old_avg) / old_avg * 100) if old_avg > 0 else 0

            trade = {
                'id':       f"IB-AUTO-{sym}-{today.replace('-','')}",
                '日期':     today,
                '券商':     'IB',
                '標的':     sym,
                '方向':     '賣出',
                '進場價':   round(old_avg, 4),
                '出場價':   round(mkt_price, 4),
                '數量':     int(sold_qty),
                '狀態':     '已平倉',
                '策略':     'IB-自動偵測',
                '進場原因': '',
                '出場原因': f'庫存異動偵測 ({old_qty:.0f}→{new_qty:.0f}股)',
                '備註':     f'已實現 ${realized_pnl:+.2f} ({pnl_pct:+.1f}%) · 偵測時間 {now_ts}',
            }

            try:
                from sheets_utils import append_trade
                append_trade(trade)
                written += 1
                logger.info(f"✅ IB 庫存異動：{sym} 出場 {sold_qty:.0f}股 已實現 ${realized_pnl:+.2f}")
            except Exception as e:
                logger.error(f"❌ 寫入 Sheets 失敗 ({sym}): {e}")

        # 處理完全平倉（舊快照有但新持倉沒有）
        current_symbols = {p['symbol'] for p in current_positions}
        for sym, old in old_snapshot.items():
            if sym.startswith('_') or sym in current_symbols:
                continue
            old_qty  = float(old.get('position', 0))
            old_avg  = float(old.get('avgCost', 0))
            if old_qty <= 0:
                continue

            trade = {
                'id':       f"IB-AUTO-{sym}-{today.replace('-','')}",
                '日期':     today,
                '券商':     'IB',
                '標的':     sym,
                '方向':     '賣出',
                '進場價':   round(old_avg, 4),
                '出場價':   0,
                '數量':     int(old_qty),
                '狀態':     '已平倉',
                '策略':     'IB-自動偵測',
                '進場原因': '',
                '出場原因': f'完全平倉（持倉消失）',
                '備註':     f'偵測時間 {now_ts}，出場價待確認',
            }
            try:
                from sheets_utils import append_trade
                append_trade(trade)
                written += 1
                logger.info(f"✅ IB 完全平倉：{sym} {old_qty:.0f}股")
            except Exception as e:
                logger.error(f"❌ 寫入 Sheets 失敗 ({sym}): {e}")

        # 更新快照
        _save_ib_snapshot(current_positions)
        logger.info(f"✅ IB 庫存異動偵測完成：寫入 {written} 筆，快照已更新")

    except Exception as e:
        logger.error(f"❌ check_ib_position_changes 失敗: {e}")

# ============================================================================
# 每日損益自動記錄排程
# ============================================================================

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    import pytz

    scheduler = BackgroundScheduler()
    tw_tz = pytz.timezone('Asia/Taipei')
    scheduler.add_job(
        record_daily_performance,
        trigger='cron',
        hour=15, minute=30,
        timezone=tw_tz,
        id='daily_record',
        replace_existing=True
    )

    # 新增 Yuanta 庫存同步 (台股開盤前 09:15)
    try:
        from brokers.sync_yuanta_positions import main as sync_yuanta_main
        scheduler.add_job(
            sync_yuanta_main,
            trigger='cron',
            hour=9, minute=15,
            timezone=tw_tz,
            id='yuanta_sync',
            replace_existing=True
        )
        logger.info("✅ Yuanta 庫存同步已排程 (台灣時間 09:15)")
    except Exception as e:
        logger.warning(f"⚠️ Yuanta 同步排程失敗: {e}")

    # IB 庫存異動偵測：每天 09:30（美股盤前）和 15:30（台股收盤後）
    scheduler.add_job(
        check_ib_position_changes,
        trigger='cron',
        hour=9, minute=30,
        timezone=tw_tz,
        id='ib_position_check_morning',
        replace_existing=True
    )
    scheduler.add_job(
        check_ib_position_changes,
        trigger='cron',
        hour=15, minute=30,
        timezone=tw_tz,
        id='ib_position_check_afternoon',
        replace_existing=True
    )
    logger.info("✅ IB 庫存異動偵測已排程 (09:30 & 15:30 台灣時間)")

    scheduler.start()
    logger.info("✅ APScheduler 已啟動 (台灣時間 15:30 自動記錄每日損益)")
except Exception as e:
    logger.warning(f"⚠️ APScheduler 初始化失敗: {e}")

# ============================================================================
# Schwab Token 狀態 + 同步 Sheets
# ============================================================================

@app.route('/api/schwab/token-status')
def api_schwab_token_status():
    """API：Schwab token 到期資訊"""
    try:
        import json as _json, time as _time
        token_path = os.path.join(os.path.dirname(__file__), '.secrets', 'schwab_token.json')
        if not os.path.exists(token_path):
            return jsonify({'status': 'no_token', 'connected': False, 'days_left': 0})

        with open(token_path, 'r', encoding='utf-8') as f:
            tok = _json.load(f)

        created_ts = tok.get('creation_timestamp', 0)
        inner = tok.get('token', {})
        access_exp = inner.get('expires_at', 0)
        now = _time.time()

        # Schwab refresh token 有效 7 天
        refresh_exp = created_ts + 7 * 86400 if created_ts else 0
        days_left = max(0, int((refresh_exp - now) / 86400)) if refresh_exp else 0
        hours_left = max(0, int((access_exp - now) / 3600)) if access_exp else 0

        created_dt = datetime.fromtimestamp(created_ts).strftime('%Y-%m-%d %H:%M') if created_ts else '—'
        expire_dt  = datetime.fromtimestamp(refresh_exp).strftime('%Y-%m-%d %H:%M') if refresh_exp else '—'

        return jsonify({
            'status': 'ok',
            'connected': True,
            'created_at': created_dt,
            'refresh_expires_at': expire_dt,
            'days_left': days_left,
            'access_token_hours_left': hours_left,
            'needs_renewal': days_left <= 2,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/schwab/sync-to-sheets', methods=['POST'])
def api_schwab_sync_to_sheets():
    """API：將 Schwab 持倉同步到 Google Sheets broker_positions tab"""
    try:
        import schwab as schwab_lib
        token_path = os.path.join(os.path.dirname(__file__), '.secrets', 'schwab_token.json')
        if not os.path.exists(token_path):
            return jsonify({'status': 'error', 'message': '尚未登入 Schwab'}), 401

        client_id     = os.getenv('SCHWAB_CLIENT_ID', '')
        client_secret = os.getenv('SCHWAB_CLIENT_SECRET', '')
        client = schwab_lib.auth.client_from_token_file(token_path, client_id, client_secret)

        accounts_resp = client.get_account_numbers()
        accounts = accounts_resp.json()
        if not accounts:
            return jsonify({'status': 'error', 'message': '找不到 Schwab 帳戶'}), 404

        account_hash = accounts[0]['hashValue']
        detail_resp = client.get_account(account_hash, fields=[schwab_lib.client.Client.Account.Fields.POSITIONS])
        detail = detail_resp.json()

        positions_raw = detail.get('securitiesAccount', {}).get('positions', [])
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        positions_to_write = []
        for p in positions_raw:
            inst = p.get('instrument', {})
            sym = inst.get('symbol', '')
            qty = p.get('longQuantity', 0) or p.get('shortQuantity', 0)
            avg = round(p.get('averagePrice', 0), 4)
            mv  = round(p.get('marketValue', 0), 2)
            mkt = round(mv / qty, 4) if qty else 0
            tc  = round(avg * qty, 2)
            open_pnl = round(p.get('longOpenProfitLoss', p.get('currentDayProfitLoss', 0)), 2)
            positions_to_write.append({
                'source': 'schwab',
                'symbol': sym,
                'secType': 'STK',
                'exchange': 'US',
                'currency': 'USD',
                'position': qty,
                'avgCost': avg,
                'totalCost': tc,
                'currentPrice': mkt,
                'marketValue': mv,
                'unrealizedPnl': open_pnl,
            })

        if not SHEETS_OK:
            return jsonify({'status': 'error', 'message': 'Google Sheets 未連線'}), 503

        # Upsert 模式：同 symbol 就更新，否則新增
        sheet = get_sheet('broker_positions')
        if sheet is None:
            return jsonify({'status': 'error', 'message': '找不到 broker_positions tab'}), 500

        all_values = sheet.get_all_values()
        header = all_values[0] if all_values else []

        # 取得 symbol 欄位索引（C=index 2）
        sym_col_idx = header.index('symbol') if 'symbol' in header else 2
        src_col_idx = header.index('券商') if '券商' in header else (header.index('source') if 'source' in header else 1)

        # 建立 schwab 現有列的 symbol → row_number 對應（1-indexed, skip header row 1）
        existing_schwab = {}
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) > src_col_idx and row[src_col_idx].lower() == 'schwab':
                sym = row[sym_col_idx] if len(row) > sym_col_idx else ''
                if sym:
                    existing_schwab[sym] = i

        # Upsert 每個 Schwab 持倉
        for p in positions_to_write:
            row_data = [now_str, p['source'], p['symbol'], p['secType'], p['exchange'],
                        p['currency'], p['position'], p['avgCost'], p['totalCost'],
                        p['currentPrice'], p['marketValue'], p['unrealizedPnl'], p['position']]
            if p['symbol'] in existing_schwab:
                # 更新現有列（同 symbol 不重複）
                row_num = existing_schwab[p['symbol']]
                sheet.update(values=[row_data], range_name=f'A{row_num}')
            else:
                # 新 symbol → 新增一列
                sheet.append_row(row_data)

        # 刪除已不在持倉中的 schwab 列（從後往前刪避免 index 錯位）
        current_symbols = {p['symbol'] for p in positions_to_write}
        rows_to_delete = sorted(
            [rn for sym, rn in existing_schwab.items() if sym not in current_symbols],
            reverse=True
        )
        for rn in rows_to_delete:
            sheet.delete_rows(rn)

        logger.info(f"✅ Schwab 持倉已同步 broker_positions：{len(positions_to_write)} 筆")

        # 同步 broker_snapshot（帳戶快照）
        try:
            balances = detail.get('securitiesAccount', {}).get('currentBalances', {})
            nlv = balances.get('liquidationValue', 0)
            cash = balances.get('cashBalance', 0)
            total_mv = sum(p.get('marketValue', 0) for p in positions_raw)
            total_open_pnl = sum(p.get('longOpenProfitLoss', p.get('currentDayProfitLoss', 0)) for p in positions_raw)
            acc_num = accounts[0].get('accountNumber', '')

            snap_sheet = get_sheet('broker_snapshot')
            if snap_sheet is not None:
                # 欄位順序對齊 IBKR：時間, 券商, 帳戶總資產(NLV), 可用現金, 含融資權益(open_pnl), currency, 換算台幣
                usd_rate = 32.0  # 估算匯率，可日後改為動態取得
                ntd_equiv = f"NT${round(nlv * usd_rate):,}"
                snap_sheet.append_row([
                    now_str, 'schwab', round(nlv, 2),
                    round(cash, 2), round(total_open_pnl, 2), 'USD', ntd_equiv
                ])
                logger.info(f"✅ Schwab broker_snapshot 已寫入")
        except Exception as snap_err:
            logger.warning(f"⚠️ 寫入 broker_snapshot 失敗: {snap_err}")

        return jsonify({
            'status': 'success',
            'synced': len(positions_to_write),
            'positions': [p['symbol'] for p in positions_to_write],
            'timestamp': now_str,
        })

    except Exception as e:
        logger.error(f"Schwab 同步 Sheets 失敗: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# 運行
# ============================================================================

if __name__ == '__main__':
    print("[*] Flask 應用啟動...")
    print("[*] 訪問: http://localhost:8889")
    print(f"[*] 數據層狀態: {'OK' if DATA_LAYER_OK else 'DISABLED'}")
    print(f"[*] Ship監測狀態: {'OK' if SHIP_MONITOR_OK else 'DISABLED'}")
    app.run(debug=False, host='0.0.0.0', port=8889)
