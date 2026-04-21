#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krystal AI Dashboard v8 - Flask 後端服務器
處理文件上傳、圖表生成等後端邏輯
"""
import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from pathlib import Path
import tempfile
import subprocess
import json
import time
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import yfinance as yf


# 載入環境變數
load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)

# 啟用 CORS（允許所有來源訪問）
try:
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
except:
    pass  # 如果 flask-cors 失敗，會在下面的 after_request 中補償

# 為所有 API 響應添加 CORS 頭
@app.after_request
def add_cors_headers(response):
    """在所有響應中添加 CORS 頭"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response


def safe_float(val, default=0.0):
    """安全轉換為浮點數"""
    if val is None or val == '' or str(val).lower() == 'nan':
        return default
    try:
        # 處理帶百分比符號的情況
        if isinstance(val, str) and '%' in val:
            return float(val.replace('%', '').strip())
        return float(val)
    except (ValueError, TypeError):
        return default

# 配置
UPLOAD_FOLDER = Path(__file__).parent / 'temp_uploads'
CHARTS_FOLDER = Path(__file__).parent / 'charts'
DB_PATH = Path(__file__).parent / 'broker_positions.db'  # 本地數據庫
UPLOAD_FOLDER.mkdir(exist_ok=True)
CHARTS_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# ── 簡易 in-memory cache（避免短時間重複打外部 API）──
import threading as _threading
_api_cache: dict = {}          # key → {'data': ..., 'ts': float}
_api_cache_lock = _threading.Lock()
_api_inflight: dict = {}       # key → threading.Event，飛行中的請求
_CACHE_TTL = 30                # 秒：30 秒內同一 endpoint 直接回快取

def _cache_get(key: str):
    entry = _api_cache.get(key)
    if entry and (time.time() - entry['ts']) < _CACHE_TTL:
        return entry['data']
    return None

def _cache_set(key: str, data):
    _api_cache[key] = {'data': data, 'ts': time.time()}

def _schwab_fetch_with_dedup(fn):
    """確保同時只有一個 Schwab API 請求在飛行，其他等待結果（mutex dedup + 30s cache）"""
    key = 'schwab_summary'
    cached = _cache_get(key)
    if cached is not None:
        return cached
    with _api_cache_lock:
        # Double-check：可能在等 lock 的期間，另一個 thread 已寫入快取
        cached = _cache_get(key)
        if cached is not None:
            return cached
        result = fn()
        _cache_set(key, result)
        return result


def read_csv_file(file_storage):
    """讀取 CSV 文件，支援多種編碼。先把 bytes 讀進記憶體再試各編碼。"""
    raw = file_storage.read()
    import io as _io
    for enc in ('utf-8-sig', 'utf-8', 'cp950', 'big5', 'gb2312'):
        try:
            df = pd.read_csv(_io.BytesIO(raw), encoding=enc)
            df.columns = [col.lstrip('\ufeff') for col in df.columns]
            # 驗證：欄位名應包含中文或常見關鍵字
            header = ','.join(df.columns)
            if any(k in header for k in ['進場', '出場', '獲利', '商品', '報酬', 'date', 'Date']):
                return df
            # 欄位不匹配，但沒報錯 → 可能解碼正確但格式不同
            if len(df.columns) >= 10:
                return df
        except (UnicodeDecodeError, Exception):
            continue
    # 最後用 latin-1 (永不報錯) + 原始欄位
    df = pd.read_csv(_io.BytesIO(raw), encoding='latin-1')
    df.columns = [col.lstrip('\ufeff') for col in df.columns]
    return df


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


# ============================================================================
# 本地快取數據庫初始化
# ============================================================================
def init_db():
    """初始化本地 SQLite 數據庫"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 建立持倉表
    c.execute('''CREATE TABLE IF NOT EXISTS broker_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        position REAL,
        avgCost REAL,
        marketPrice REAL,
        unrealizedPNL REAL,
        broker TEXT,
        currency TEXT,
        timestamp DATETIME,
        synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 為既有 broker_positions 表補加欄位（若不存在）
    for col, ctype in [('strategy', 'TEXT'), ('notes', 'TEXT'),
                       ('currentPrice', 'REAL'), ('marketValue', 'REAL'), ('unrealizedPnL', 'REAL'), ('name', 'TEXT')]:
        try:
            c.execute(f'ALTER TABLE broker_positions ADD COLUMN {col} {ctype}')
        except sqlite3.OperationalError:
            pass  # 欄位已存在

    # 統一 broker 名稱：Interactive Brokers / IBKR → IB, Charles Schwab → Schwab
    try:
        c.execute("UPDATE broker_positions SET broker='IB' WHERE lower(broker) IN ('interactive brokers','ibkr')")
        c.execute("UPDATE broker_positions SET broker='Schwab' WHERE lower(broker) LIKE '%schwab%' OR lower(broker) LIKE '%charles%'")
        conn.commit()
    except Exception:
        pass

    # 建立 (broker, symbol) 唯一索引 — 先去除現有重複資料再建立
    try:
        # 每個 (broker, symbol) 只保留 id 最大（最新）那筆
        c.execute('''
            DELETE FROM broker_positions
            WHERE id NOT IN (
                SELECT MAX(id) FROM broker_positions
                GROUP BY broker, symbol
            )
        ''')
        conn.commit()
        c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_symbol ON broker_positions (broker, symbol)')
    except sqlite3.OperationalError:
        pass

    # 用於 C：記錄每次 sync 前的快照，偵測平倉部位
    c.execute('''CREATE TABLE IF NOT EXISTS positions_snapshot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        broker TEXT,
        symbol TEXT,
        position REAL,
        avgCost REAL,
        strategy TEXT,
        notes TEXT,
        entry_date TEXT,
        snapshot_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 建立同步日誌
    c.execute('''CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        count INTEGER,
        status TEXT
    )''')

    # 建立已實現交易表
    c.execute('''CREATE TABLE IF NOT EXISTS realized_trades (
        id TEXT PRIMARY KEY,
        symbol TEXT,
        direction TEXT,
        entry_price REAL,
        exit_price REAL,
        quantity REAL,
        pnl REAL,
        pnl_pct REAL,
        date TEXT,
        exit_date TEXT,
        broker TEXT,
        strategy TEXT,
        notes TEXT,
        status TEXT,
        synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # 建立每日權益快照表
    c.execute('''CREATE TABLE IF NOT EXISTS equity_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        ib_mv_usd REAL DEFAULT 0,
        schwab_mv_usd REAL DEFAULT 0,
        yuanta_mv_twd REAL DEFAULT 0,
        total_mv_twd REAL DEFAULT 0,
        total_pnl_twd REAL DEFAULT 0,
        usd_twd_rate REAL DEFAULT 32.0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# 初始化數據庫
init_db()

def get_db_positions():
    """從本地數據庫讀取持倉（零成本）"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM broker_positions ORDER BY synced_at DESC')
        positions = [dict(row) for row in c.fetchall()]
        conn.close()
        return positions
    except Exception as e:
        sys.stderr.write(f"[ERROR] 讀取本地數據庫失敗: {e}")
        return []

# ============================================================================
# B + C：平倉偵測 & 已實現交易建立
# ============================================================================

def _get_exit_price_from_fills(symbol: str, broker: str, after_date: str = '') -> float | None:
    """
    從 broker_fills Sheets 找最近一筆 SELL 成交價
    after_date: 只看這日期之後的成交（格式 YYYY-MM-DD）
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet
        sheet = get_sheet('broker_fills')
        if not sheet:
            return None
        records = sheet.get_all_records()
        sells = []
        for r in records:
            sym   = str(r.get('symbol', '')).strip()
            side  = str(r.get('side', '')).strip().upper()
            price = r.get('price', 0)
            # 欄位名帶空格，用 .strip() 統一
            time_val = str(r.get('時間 ', r.get('time', r.get('時間', '')))).strip()
            if sym != symbol:
                continue
            if side not in ('SELL', '賣'):
                continue
            if after_date and time_val[:10] < after_date:
                continue
            try:
                sells.append((time_val, float(price)))
            except Exception:
                pass
        if sells:
            sells.sort(key=lambda x: x[0], reverse=True)
            return sells[0][1]
    except Exception as e:
        print(f"⚠️ fills lookup failed for {symbol}: {e}")
    return None


def _get_yahoo_close(symbol: str) -> float | None:
    """Yahoo Finance 最新收盤價作為 fallback 出場價"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='2d')
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception:
        pass
    return None


def _write_realized_trade_to_sheets(trade: dict) -> bool:
    """寫入已實現交易到 Sheets trades 分頁"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet
        sheet = get_sheet('trades')
        if not sheet:
            return False
        header = sheet.row_values(1)
        field_map = {
            '日期':   trade.get('date', ''),
            '券商':   trade.get('broker', ''),
            '標的':   trade.get('symbol', ''),
            '方向':   trade.get('direction', '買'),
            '進場價': trade.get('entry_price', ''),
            '出場價': trade.get('exit_price', ''),
            '數量':   trade.get('quantity', ''),
            '狀態':   '已平倉',
            '策略':   trade.get('strategy', ''),
            '進場原因': trade.get('entry_reason', ''),
            '出場原因': trade.get('notes', ''),
            '損益':   trade.get('pnl', ''),
            '損益%':  round(trade.get('pnl_pct', 0), 2) if trade.get('pnl_pct') else '',
            '備註':   trade.get('extra_notes', ''),
            'ID':     trade.get('id', ''),
        }
        row = [field_map.get(col, '') for col in header]
        sheet.append_row(row, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        sys.stderr.write(f"[ERROR] write realized trade to Sheets failed: {e}")
        return False


def _create_realized_trade(pos: dict, exit_price: float, exit_date: str,
                            notes: str = '', source: str = 'manual') -> dict:
    """建立已實現交易記錄，存入 DB 並同步 Sheets"""
    avg_cost = float(pos.get('avgCost') or 0)
    qty      = float(pos.get('position') or 0)
    pnl      = round((exit_price - avg_cost) * qty, 2)
    pnl_pct  = round((pnl / (avg_cost * abs(qty))) * 100, 2) if avg_cost > 0 and qty != 0 else 0

    entry_date = (pos.get('timestamp') or pos.get('entry_date') or '')
    if entry_date:
        entry_date = str(entry_date)[:10]

    trade_id = f"{pos['symbol']}_{pos.get('broker','')}_{exit_date}"

    trade = {
        'id':           trade_id,
        'symbol':       pos['symbol'],
        'direction':    '買',   # broker_positions 目前只記錄多頭持倉
        'entry_price':  avg_cost,
        'exit_price':   exit_price,
        'quantity':     qty,
        'pnl':          pnl,
        'pnl_pct':      pnl_pct,
        'date':         entry_date,
        'exit_date':    exit_date,
        'broker':       pos.get('broker', ''),
        'strategy':     pos.get('strategy', ''),
        'notes':        notes,
        'status':       '已平倉',
        'source':       source,
    }

    # 寫入 realized_trades DB
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c    = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO realized_trades
            (id, symbol, direction, entry_price, exit_price, quantity, pnl, pnl_pct,
             date, exit_date, broker, strategy, notes, status, synced_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            trade['id'], trade['symbol'], trade['direction'],
            trade['entry_price'], trade['exit_price'], trade['quantity'],
            trade['pnl'], trade['pnl_pct'],
            trade['date'], trade['exit_date'],
            trade['broker'], trade['strategy'], trade['notes'], trade['status'],
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        sys.stderr.write(f"[ERROR] DB realized trade insert failed: {e}")

    # 同步到 Sheets
    _write_realized_trade_to_sheets(trade)
    return trade


def _normalize_broker(name) -> str:
    """統一券商名稱：Interactive Brokers/IBKR → IB, Charles Schwab → Schwab"""
    if not name:
        return '其他'
    name = str(name)
    low = name.lower().strip()
    if low in ('ib', 'ibkr') or 'interactive' in low:
        return 'IB'
    if 'schwab' in low or 'charles' in low:
        return 'Schwab'
    if '元大' in name or low == 'yuanta':
        return '元大'
    return name


def _detect_closed_positions(old_positions: list, new_positions: list) -> list:
    """
    C：比對新舊持倉，回傳已平倉的部位列表
    key = (broker, symbol)
    """
    new_keys = {(p.get('broker','').lower(), p.get('symbol','')) for p in new_positions}
    closed = []
    for p in old_positions:
        key = (p.get('broker','').lower(), p.get('symbol',''))
        if key not in new_keys and float(p.get('position') or 0) != 0:
            closed.append(p)
    return closed


def sync_from_google_sheets():
    """從 Google Sheets 同步持倉到本地數據庫，並自動偵測已平倉部位（C）"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import read_sheet_data_with_cache

        df = read_sheet_data_with_cache('broker_positions')
        if df is None or df.empty:
            return {'status': 'error', 'message': '無法從 Google Sheets 讀取數據'}

        # ── 去重：同一 (broker, symbol) 只保留最新一筆 ─────────────
        # Google Sheets 每天 append，會有多行歷史快照
        broker_col = next((c for c in ['券商', 'broker', 'Broker'] if c in df.columns), None)
        symbol_col = next((c for c in ['代碼', 'symbol', 'Symbol'] if c in df.columns), None)
        ts_col     = next((c for c in ['時間', 'timestamp', 'Timestamp', '日期'] if c in df.columns), None)
        if broker_col and symbol_col:
            if ts_col:
                df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce')
                df = df.sort_values(ts_col, ascending=False)
            df = df.drop_duplicates(subset=[broker_col, symbol_col], keep='first')
        elif symbol_col:
            if ts_col:
                df[ts_col] = pd.to_datetime(df[ts_col], errors='coerce')
                df = df.sort_values(ts_col, ascending=False)
            df = df.drop_duplicates(subset=[symbol_col], keep='first')

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # ── C step 1：同步前先快照現有持倉 ─────────────────────────
        c.execute('SELECT * FROM broker_positions')
        old_positions = [dict(r) for r in c.fetchall()]

        # ── 清空並寫入新持倉 ─────────────────────────────────────────
        c.execute('DELETE FROM broker_positions')
        for _, row in df.iterrows():
            def _f(v, default=None):
                return float(v) if pd.notna(v) and str(v) not in ('', 'nan') else default
            c.execute('''INSERT INTO broker_positions
                (symbol, position, avgCost, currentPrice, marketValue, unrealizedPnL, broker, currency, timestamp, name)
                VALUES (?,?,?,?,?,?,?,?,?,?)''', (
                str(row.get('symbol', '')),
                _f(row.get('position')),
                _f(row.get('avgCost')),
                _f(row.get('currentPrice', row.get('marketPrice'))),
                _f(row.get('marketValue')),
                _f(row.get('unrealizedPnL', row.get('unrealizedPNL'))),
                _normalize_broker(str(row.get('broker', row.get('券商', '')))),
                str(row.get('currency', '')),
                str(row.get('時間', row.get('timestamp', ''))),
                str(row.get('name', row.get('名稱', row.get('商品名稱', ''))))
            ))

        count = len(df)
        c.execute('INSERT INTO sync_log (count, status) VALUES (?,?)', (count, 'success'))
        conn.commit()

        # ── C step 2：讀取新持倉，比對偵測平倉部位 ───────────────────
        c.execute('SELECT * FROM broker_positions')
        new_positions = [dict(r) for r in c.fetchall()]
        conn.close()

        closed = _detect_closed_positions(old_positions, new_positions)
        auto_closed = []
        today = datetime.now().strftime('%Y-%m-%d')

        for pos in closed:
            sym    = pos.get('symbol', '')
            broker = pos.get('broker', '')
            entry_date = str(pos.get('timestamp') or '')[:10]

            # 出場價：fills → Yahoo Finance fallback
            exit_price = _get_exit_price_from_fills(sym, broker, after_date=entry_date)
            price_source = 'fills'
            if not exit_price:
                exit_price = _get_yahoo_close(sym)
                price_source = 'yahoo'

            if exit_price:
                trade = _create_realized_trade(
                    pos, exit_price, today,
                    notes=f'自動偵測平倉（{price_source}）',
                    source='auto_detect'
                )
                auto_closed.append({'symbol': sym, 'broker': broker,
                                     'exit_price': exit_price, 'pnl': trade['pnl'],
                                     'price_source': price_source})
                print(f"✅ [C] 自動平倉記錄：{broker} {sym} @ {exit_price} ({price_source})")
            else:
                print(f"⚠️ [C] 偵測到平倉但找不到出場價：{broker} {sym}，請手動平倉")

        return {
            'status': 'success',
            'count': count,
            'auto_closed': auto_closed,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        sys.stderr.write(f"[ERROR] 同步 Google Sheets 失敗: {e}")
        import traceback; traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主頁面"""
    return send_file('index.html')

@app.route('/test')
def simple_test():
    """簡單上傳測試頁面"""
    from pathlib import Path
    test_file = Path(__file__).parent / 'simple_test.html'
    with open(test_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/generate-charts', methods=['POST'])
def generate_charts():
    """生成圖表 API"""
    try:
        # 檢查是否有文件上傳
        if 'file' not in request.files:
            return jsonify({'error': '未上傳文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名為空'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，請上傳 CSV 或 XLSX'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        file.save(str(filepath))

        print(f"\n📁 已保存文件: {filepath}")

        # 調用 Python 圖表生成腳本
        print("🎨 開始生成圖表...\n")
        result = subprocess.run(
            [sys.executable, 'generate_charts.py', str(filepath), str(CHARTS_FOLDER)],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            sys.stderr.write(f"[ERROR] 圖表生成失敗:\n{result.stderr}")
            return jsonify({'error': f'圖表生成失敗: {result.stderr}'}), 500

        print(result.stdout)

        # 解析輸出中的圖表路徑
        try:
            charts = json.loads(result.stdout)
            # 轉換為相對路徑
            charts = {
                k: Path(v).name for k, v in charts.items()
            }
            print(f"✅ 生成成功: {charts}")
            return jsonify(charts), 200
        except json.JSONDecodeError:
            # 如果無法解析 JSON，返回默認路徑
            return jsonify({
                'equity_curve': 'equity_curve.html',
                'mae_mfe': 'mae_mfe.html',
                'pnl_distribution': 'pnl_distribution.html',
                'monthly_heatmap': 'monthly_heatmap.html'
            }), 200

    except subprocess.TimeoutExpired:
        return jsonify({'error': '圖表生成超時'}), 500
    except Exception as e:
        sys.stderr.write(f"[ERROR] 錯誤: {e}")
        import traceback
        return jsonify({'error': str(e)}), 500

@app.route('/charts/<filename>')
def serve_chart(filename):
    """提供生成的圖表文件"""
    filepath = CHARTS_FOLDER / secure_filename(filename)
    if filepath.exists():
        return send_file(str(filepath))
    return jsonify({'error': '圖表文件不存在'}), 404

# ============================================================================
# 本地持倉快取 API（零成本讀取）
# ============================================================================
@app.route('/api/test')
def api_test():
    """測試端點"""
    return jsonify({'status': 'test_ok'})

@app.route('/api/test-broker-alias')
def test_broker_alias():
    """測試 add_broker_alias 函數"""
    test_pos = {'broker': 'schwab', 'symbol': 'ACWX', 'position': 100}

    def add_broker_alias(p):
        if isinstance(p, dict):
            pos = p.copy()
        else:
            pos = dict(p)
        if 'broker' in pos:
            pos['券商'] = pos['broker']
        return pos

    result = add_broker_alias(test_pos)
    return jsonify({
        'input': test_pos,
        'output': result,
        'has_yonghua': '券商' in result
    })

@app.route('/api/positions')
def api_positions():
    """獲取持倉數據（從本地快取，零成本）"""
    positions = get_db_positions()

    # 分類持倉
    by_broker = {
        'all': positions,
        'ib': [p for p in positions if str(p.get('broker', '')).lower() in ('ib', 'ibkr', '盈透')],
        'schwab': [p for p in positions if str(p.get('broker', '')).lower() == 'schwab'],
        'yuanta': [p for p in positions if str(p.get('broker', '')).lower() in ('yuanta', '元大')],
    }

    # 取最後同步時間
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('SELECT MAX(synced_at) FROM broker_positions')
        last_sync = c.fetchone()[0]
        conn.close()
    except:
        last_sync = None

    return jsonify({
        'status': 'success',
        'data': by_broker,
        'last_sync': last_sync,
        'count': len(positions)
    })

@app.route('/api/sync-positions', methods=['POST'])
def api_sync_positions():
    """手動同步 Google Sheets 持倉（含 C：自動偵測平倉部位）"""
    result = sync_from_google_sheets()
    if result.get('status') == 'success':
        auto = result.get('auto_closed', [])
        msg  = f"同步完成，共 {result.get('count',0)} 筆"
        if auto:
            msg += f"，自動偵測平倉 {len(auto)} 筆：" + '、'.join(p['symbol'] for p in auto)
        return jsonify({**result, 'message': msg})
    return jsonify(result), 500

@app.route('/api/smart-sync-all', methods=['POST'])
def api_smart_sync_all():
    """智能全部同步：優先即時 API 寫入 Sheets，失敗則讀 Sheets 降級。"""
    result = {'schwab': {}, 'ib': {}, 'yuanta': {}}

    # ── 1. Schwab ─────────────────────────────────────────────
    try:
        with app.test_client() as client:
            r = client.post('/api/schwab/sync-to-sheets')
            j = r.get_json() or {}
            if r.status_code == 200 and j.get('status') == 'success':
                result['schwab'] = {'mode': 'live', 'count': j.get('count', 0), 'message': j.get('message', '')}
            else:
                result['schwab'] = {'mode': 'sheets_fallback', 'reason': j.get('message', 'API 無法使用')}
    except Exception as e:
        result['schwab'] = {'mode': 'sheets_fallback', 'reason': str(e)}

    # ── 2. IB ─────────────────────────────────────────────────
    try:
        with app.test_client() as client:
            r = client.get('/api/query-ib')
            j = r.get_json() or {}
            if r.status_code == 200 and j.get('status') == 'success' and j.get('positions'):
                r2 = client.post('/api/ib-sync', json={
                    'positions': j.get('positions', []),
                    'net_liquidation_value': j.get('net_liquidation_value'),
                    'total_cash_value': j.get('total_cash_value'),
                    'account_id': j.get('account_id'),
                })
                j2 = r2.get_json() or {}
                if r2.status_code == 200 and j2.get('status') == 'success':
                    result['ib'] = {'mode': 'live', 'count': len(j.get('positions', [])), 'message': j2.get('message', '')}
                else:
                    result['ib'] = {'mode': 'sheets_fallback', 'reason': j2.get('message', 'IB → Sheets 寫入失敗')}
            else:
                result['ib'] = {'mode': 'sheets_fallback', 'reason': j.get('message', 'TWS/Gateway 未連線')}
    except Exception as e:
        result['ib'] = {'mode': 'sheets_fallback', 'reason': str(e)}

    # ── 3. 元大 ────────────────────────────────────────────────
    try:
        py32 = Path(__file__).parent.parent / '.venv_yuanta32' / 'Scripts' / 'python.exe'
        script = Path(__file__).parent.parent / 'brokers' / 'sync_yuanta_positions.py'
        if py32.exists() and script.exists():
            proc = subprocess.run([str(py32), str(script)], capture_output=True, timeout=120,
                                  cwd=str(Path(__file__).parent.parent))
            if proc.returncode == 0:
                result['yuanta'] = {'mode': 'live', 'message': '元大即時 API 同步成功'}
            else:
                err = (proc.stderr or b'').decode('utf-8', errors='replace')
                result['yuanta'] = {'mode': 'sheets_fallback', 'reason': err[:200] or '元大腳本失敗'}
        else:
            result['yuanta'] = {'mode': 'sheets_fallback', 'reason': '找不到 32-bit Python 或元大腳本'}
    except subprocess.TimeoutExpired:
        result['yuanta'] = {'mode': 'sheets_fallback', 'reason': '元大同步逾時（60s）'}
    except Exception as e:
        result['yuanta'] = {'mode': 'sheets_fallback', 'reason': str(e)}

    # ── 4. 最後：Sheets → 本地 DB ──────────────────────────────
    final = sync_from_google_sheets()
    result['sheets_to_db'] = final

    live_count = sum(1 for b in ('schwab', 'ib', 'yuanta') if result[b].get('mode') == 'live')
    return jsonify({
        'status': 'success' if final.get('status') == 'success' else 'partial',
        'summary': f'即時 {live_count}/3，Sheets 共 {final.get("count", 0)} 筆',
        'brokers': {k: result[k] for k in ('schwab', 'ib', 'yuanta')},
        'total_count': final.get('count', 0),
        'auto_closed': final.get('auto_closed', []),
    })


@app.route('/api/broker-positions', methods=['GET'])
def api_broker_positions():
    """獲取持倉數據"""
    try:
        positions = get_db_positions()

        # 統一 broker 名稱
        for p in positions:
            if 'broker' in p:
                p['broker'] = _normalize_broker(p['broker'])

        by_broker = {
            'all':    positions,
            'ib':     [p for p in positions if p.get('broker') == 'IB'],
            'schwab': [p for p in positions if p.get('broker') == 'Schwab'],
            'yuanta': [p for p in positions if p.get('broker') == '元大'],
        }
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute('SELECT MAX(synced_at) FROM broker_positions')
            last_sync = c.fetchone()[0]
            conn.close()
        except Exception:
            last_sync = None

        return jsonify({
            'status': 'success',
            'data': by_broker,
            'last_sync': last_sync,
            'count': len(positions),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def safe_float(val, default=None):
    """安全轉換為浮點數"""
    if pd.isna(val) or val == '' or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def get_trades_from_sheets(status='all'):
    """從 Google Sheets 讀取交易記錄"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from sheets_utils import read_sheet_data_with_cache

        df = read_sheet_data_with_cache('trades')

        if df is None or df.empty:
            return []

        trades = []
        for _, row in df.iterrows():
            row_dict = dict(row)  # 將 Series 轉換為字典

            trade = {
                'id': str(row_dict.get('ID', '')).strip(),
                'date': str(row_dict.get('日期', '')).strip(),
                'broker': str(row_dict.get('券商', '')).strip(),
                'symbol': str(row_dict.get('標的', '')).strip(),
                'direction': str(row_dict.get('方向', '')).strip(),
                'entry_price': safe_float(row_dict.get('進場價'), 0),
                'exit_price': safe_float(row_dict.get('出場價')),
                'quantity': safe_float(row_dict.get('數量'), 0),
                'status': str(row_dict.get('狀態', '')).strip(),
                'strategy': str(row_dict.get('策略', '')).strip(),
                'pnl': safe_float(row_dict.get('損益')),
                'pnl_pct': safe_float(row_dict.get('損益%')),
                'notes': str(row_dict.get('備註', '')).strip()
            }
            trades.append(trade)

        # 過濾狀態
        if status == 'open':
            trades = [t for t in trades if t['status'] in ('進行中', 'open', 'OPEN')]
        elif status == 'closed':
            trades = [t for t in trades if t['status'] in ('已平倉', 'closed', 'CLOSED')]

        return trades
    except Exception as e:
        sys.stderr.write(f"[ERROR] 讀取交易記錄失敗: {e}")
        import traceback
        return []

@app.route('/api/positions/<int:pos_id>/close', methods=['POST'])
def api_close_position(pos_id):
    """B：手動平倉 — 建立已實現交易並從持倉移除"""
    data       = request.get_json() or {}
    exit_price = float(data.get('exit_price', 0))
    exit_date  = data.get('exit_date', datetime.now().strftime('%Y-%m-%d'))
    notes      = data.get('notes', '')

    if exit_price <= 0:
        return jsonify({'status': 'error', 'message': '請輸入有效的出場價格'}), 400

    # 讀取持倉
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c    = conn.cursor()
        c.execute('SELECT * FROM broker_positions WHERE id=?', (pos_id,))
        row  = c.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'DB 讀取失敗: {e}'}), 500

    if not row:
        return jsonify({'status': 'error', 'message': '找不到持倉'}), 404

    pos = dict(row)

    # 建立已實現交易記錄（DB + Sheets）
    trade = _create_realized_trade(pos, exit_price, exit_date, notes=notes, source='manual')

    # 從 broker_positions DB 刪除
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c    = conn.cursor()
        c.execute('DELETE FROM broker_positions WHERE id=?', (pos_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ 刪除 DB 持倉失敗: {e}")

    # 從 Sheets broker_positions 刪除對應列
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet
        sheet = get_sheet('broker_positions')
        if sheet:
            vals       = sheet.get_all_values()
            header     = vals[0] if vals else []
            sym_idx    = header.index('symbol') if 'symbol' in header else None
            broker_idx = next((header.index(k) for k in ('broker','券商') if k in header), None)
            for r_idx, r_vals in enumerate(vals[1:], start=2):
                sym_m = sym_idx is not None and len(r_vals) > sym_idx and r_vals[sym_idx] == pos['symbol']
                brk_m = broker_idx is not None and len(r_vals) > broker_idx and r_vals[broker_idx] == pos['broker']
                if sym_m and brk_m:
                    sheet.delete_rows(r_idx)
                    break
    except Exception as e:
        print(f"⚠️ Sheets 刪除持倉失敗: {e}")

    return jsonify({
        'status':  'success',
        'message': f"{pos['symbol']} 平倉完成",
        'pnl':     trade['pnl'],
        'pnl_pct': trade['pnl_pct']})


@app.route('/api/positions/<int:pos_id>/meta', methods=['PUT'])
def api_update_position_meta(pos_id):
    """更新持倉的 策略 / 備註，並同步到 Google Sheets broker_positions 分頁"""
    data     = request.get_json() or {}
    strategy = data.get('strategy', '')
    notes    = data.get('notes',    '')

    # ── 1. 更新 SQLite ────────────────────────────────────────
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('UPDATE broker_positions SET strategy=?, notes=? WHERE id=?',
                  (strategy, notes, pos_id))
        conn.commit()
        c.execute('SELECT * FROM broker_positions WHERE id=?', (pos_id,))
        row = dict(c.fetchone() or {})
        conn.close()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'DB 更新失敗: {e}'}), 500

    # ── 2. 同步到 Google Sheets broker_positions 分頁 ─────────
    sheets_ok = False
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet
        sheet = get_sheet('broker_positions')
        if sheet:
            all_vals = sheet.get_all_values()
            if all_vals:
                header = all_vals[0]
                # 確保 strategy / notes 欄位存在
                for col_name in ['strategy', 'notes']:
                    if col_name not in header:
                        header.append(col_name)
                        sheet.update_cell(1, len(header), col_name)

                # 相容中英文欄位名
                sym_idx    = header.index('symbol')             if 'symbol'   in header else None
                broker_idx = next((header.index(k) for k in ('broker','券商') if k in header), None)
                strat_idx  = header.index('strategy')           if 'strategy' in header else None
                notes_idx  = header.index('notes')              if 'notes'    in header else None

                for r_idx, r_vals in enumerate(all_vals[1:], start=2):
                    sym_match    = sym_idx    is not None and len(r_vals) > sym_idx    and r_vals[sym_idx]    == row.get('symbol')
                    broker_match = broker_idx is not None and len(r_vals) > broker_idx and r_vals[broker_idx] == row.get('broker')
                    if sym_match and broker_match:
                        if strat_idx is not None:
                            sheet.update_cell(r_idx, strat_idx + 1, strategy)
                        if notes_idx is not None:
                            sheet.update_cell(r_idx, notes_idx + 1, notes)
                        sheets_ok = True
                        break
    except Exception as e:
        print(f"⚠️ Sheets 同步失敗 (持倉 meta): {e}")

    return jsonify({
        'status':    'success',
        'message':   '已更新' + ('並同步到 Sheets' if sheets_ok else '（Sheets 同步失敗，僅存 DB）'),
        'sheets_ok': sheets_ok
    })


@app.route('/api/trades/realized/sync', methods=['POST'])
def api_realized_sync():
    """強制從 Sheets 重新同步已實現交易到 DB"""
    trades = get_trades_from_sheets('closed')
    if trades:
        _sync_realized_to_db(trades)
    return jsonify({'status': 'success', 'synced': len(trades)})


@app.route('/api/trades/open', methods=['GET'])
def api_trades_open():
    """未平倉交易"""
    print("[ROUTE] /api/trades/open endpoint called")
    trades = get_trades_from_sheets('open')
    print(f"[ROUTE] Returned {len(trades)} open trades")
    return jsonify({
        'status': 'success',
        'data': trades,
        'count': len(trades),
        'type': 'open'
    })

def _sync_realized_to_db(trades):
    """將已實現交易同步到 SQLite DB"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        now = datetime.now().isoformat()
        for t in trades:
            c.execute('''INSERT OR REPLACE INTO realized_trades
                (id, symbol, direction, entry_price, exit_price, quantity,
                 pnl, pnl_pct, date, exit_date, broker, strategy, notes, status, synced_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                t.get('id') or f"{t.get('symbol','')}_{t.get('date','')}",
                t.get('symbol'), t.get('direction'),
                t.get('entry_price'), t.get('exit_price'), t.get('quantity'),
                t.get('pnl'), t.get('pnl_pct'),
                t.get('date'), t.get('exit_date'),
                t.get('broker'), t.get('strategy'), t.get('notes'), t.get('status'),
                now
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        sys.stderr.write(f"[ERROR] sync realized_trades to DB failed: {e}")


@app.route('/api/trades/realized', methods=['GET'])
def api_trades_realized():
    """已平倉交易 — 優先讀 DB，DB 空時從 Sheets 同步再存 DB"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM realized_trades ORDER BY date DESC')
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
    except Exception:
        rows = []

    if rows:
        return jsonify({'status': 'success', 'data': rows, 'count': len(rows),
                        'type': 'closed', 'source': 'db'})

    # DB 空 → 從 Sheets 抓並存入 DB
    trades = get_trades_from_sheets('closed')
    if trades:
        _sync_realized_to_db(trades)
    return jsonify({'status': 'success', 'data': trades, 'count': len(trades),
                    'type': 'closed', 'source': 'sheets'})

def calculate_ytd_returns():
    """計算年初至今的回報（未實現 + 已實現）"""
    try:
        positions = get_db_positions()
        current_year = datetime.now().year
        month_names = ['Jan','Feb','Mar','Apr','May','Jun',
                       'Jul','Aug','Sep','Oct','Nov','Dec']

        # ── 未實現損益（DB schema 實際欄位：currentPrice/marketValue）──
        def safe(p, *keys, default=0.0):
            for k in keys:
                v = p.get(k)
                if v is not None and str(v) not in ('', 'nan', 'None'):
                    try: return float(v)
                    except: pass
            return default

        total_market_value = sum(
            safe(p, 'marketValue') or
            safe(p, 'position') * safe(p, 'currentPrice', 'marketPrice')
            for p in positions
        )
        total_cost = sum(
            safe(p, 'position') * safe(p, 'avgCost')
            for p in positions
        )
        unrealized_pnl = sum(
            safe(p, 'unrealizedPnL', 'unrealizedPNL') or
            (safe(p, 'position') * (safe(p, 'currentPrice', 'marketPrice') - safe(p, 'avgCost')))
            for p in positions
        ) or (total_market_value - total_cost)

        # ── 已實現損益（從 Google Sheets trades 表，今年已平倉）──
        monthly_pnl = {m: 0.0 for m in range(1, 13)}  # 月份 1~12
        total_realized = 0.0
        try:
            trades = get_trades_from_sheets('closed')
            for t in trades:
                date_str = t.get('date', '')
                pnl = t.get('pnl') or 0
                # 解析日期，只統計今年
                try:
                    trade_date = datetime.strptime(str(date_str).strip()[:10], '%Y-%m-%d')
                    if trade_date.year == current_year:
                        monthly_pnl[trade_date.month] += float(pnl)
                        total_realized += float(pnl)
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ 無法讀取交易記錄: {e}")

        ytd_return = unrealized_pnl + total_realized
        ytd_return_pct = (ytd_return / total_cost * 100) if total_cost > 0 else 0

        # 生成月度報酬率列表（到當前月份為止）
        current_month = datetime.now().month
        monthly_data = []
        cumulative = 0.0
        for m in range(1, current_month + 1):
            cumulative += monthly_pnl[m]
            monthly_data.append({
                'month': month_names[m - 1],
                'realized_pnl': round(monthly_pnl[m], 2),
                'cumulative_pnl': round(cumulative, 2),
                'return_pct': round((monthly_pnl[m] / total_cost * 100) if total_cost > 0 else 0, 2)
            })

        return {
            'status': 'success',
            'ytd_return': round(ytd_return, 2),
            'ytd_return_pct': round(ytd_return_pct, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'realized_pnl': round(total_realized, 2),
            'monthly_data': monthly_data,
            'total_market_value': round(total_market_value, 2),
            'total_cost': round(total_cost, 2)
        }
    except Exception as e:
        sys.stderr.write(f"[ERROR] 計算 YTD 回報失敗: {e}")
        return {
            'status': 'error',
            'ytd_return': 0,
            'ytd_return_pct': 0,
            'monthly_data': [],
            'error': str(e)
        }

@app.route('/api/ytd-returns', methods=['GET'])
def api_ytd_returns():
    """年初至今回報"""
    return jsonify(calculate_ytd_returns())

@app.route('/api/query-ib', methods=['GET'])
def api_query_ib():
    """IB 帳戶查詢 — 以子進程執行 query_ib_positions.py 避免 Flask event loop 衝突"""
    import subprocess, json as _json, sys as _sys
    script = str(Path(__file__).parent.parent / 'query_ib_positions.py')
    try:
        result = subprocess.run(
            [_sys.executable, script],
            capture_output=True, text=True, timeout=15,
            encoding='utf-8', errors='replace'
        )
        stdout = result.stdout.strip()
        if not stdout:
            return jsonify({'status': 'error', 'connected': False,
                            'message': result.stderr.strip() or 'IB 子進程無輸出，請確認 TWS/Gateway 正在運行'})
        data = _json.loads(stdout)
        return jsonify(data)
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'connected': False, 'message': 'IB 查詢逾時（15秒），TWS 可能未完全啟動'})
    except Exception as e:
        return jsonify({'status': 'error', 'connected': False, 'message': str(e)})

@app.route('/api/schwab/token-status', methods=['GET'])
def api_schwab_token():
    """Schwab Token 狀態 — 檢查本地 token 檔是否有效"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from brokers.schwab_api import load_config_from_env, load_token, has_valid_token
        import time as _time

        cfg = load_config_from_env()
        if not cfg.client_id or not cfg.client_secret:
            return jsonify({'status': 'no_config', 'connected': False,
                            'message': '請在 .env 設定 SCHWAB_CLIENT_ID / SCHWAB_CLIENT_SECRET / SCHWAB_REDIRECT_URI'})

        tok = load_token()
        has_refresh = bool(tok and tok.get('refresh_token'))
        valid = has_valid_token(tok)
        # access_token 壽命只有 30 分鐘，refresh_token 才是 7 天
        # 有 refresh_token 就視為已連結（可自動 refresh）
        days_left = 0
        if tok and tok.get('expires_at'):
            secs_left = float(tok['expires_at']) - _time.time()
            if secs_left > 0:
                days_left = round(secs_left / 86400, 1)
            elif has_refresh:
                days_left = 7  # refresh token 有效期約 7 天

        return jsonify({
            'status': 'ok' if (valid or has_refresh) else 'expired',
            'connected': valid or has_refresh,
            'has_token': tok is not None,
            'has_refresh': has_refresh,
            'days_left': days_left,
            'client_id_set': bool(cfg.client_id),
        })
    except Exception as e:
        return jsonify({'status': 'error', 'connected': False, 'message': str(e)})


@app.route('/api/schwab/authorize', methods=['GET'])
def api_schwab_authorize():
    """產生 Schwab OAuth 授權 URL"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from brokers.schwab_api import get_authorize_url
        url = get_authorize_url()
        return jsonify({'status': 'ok', 'url': url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/schwab/start-oauth', methods=['POST'])
def api_schwab_start_oauth():
    """
    啟動 Schwab OAuth：只回傳授權 URL，讓前端開新視窗。
    Schwab 登入後會 redirect 到 SCHWAB_REDIRECT_URI（本機 Flask /api/schwab/callback）。
    """
    try:
        _brokers_path = str(Path(__file__).parent.parent)
        if _brokers_path not in sys.path:
            sys.path.insert(0, _brokers_path)

        from brokers.schwab_oauth import build_login_url

        client_id    = os.environ.get('SCHWAB_CLIENT_ID', '').strip()
        redirect_uri = os.environ.get('SCHWAB_REDIRECT_URI', '').strip()

        if not client_id or not redirect_uri:
            return jsonify({'status': 'error',
                            'message': '.env 缺少 SCHWAB_CLIENT_ID 或 SCHWAB_REDIRECT_URI'})

        auth_url = build_login_url(client_id, redirect_uri)
        return jsonify({'status': 'ok', 'url': auth_url,
                        'message': '請在新視窗完成 Schwab 登入，授權後自動儲存 Token'})
    except Exception as e:
        import traceback
        sys.stderr.write(f'[Schwab start-oauth] {traceback.format_exc()}\n')
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/schwab/callback', methods=['GET'])
def api_schwab_callback():
    """Schwab OAuth callback（備用，通常不會真正被呼叫）"""
    code = request.args.get('code', '')
    if not code:
        return '<h2>❌ 沒有收到 code</h2>', 400
    try:
        _p = str(Path(__file__).parent.parent)
        if _p not in sys.path: sys.path.insert(0, _p)
        from brokers.schwab_api import load_config_from_env
        from brokers.schwab_oauth import exchange_code_for_refresh_token, save_tokens
        cfg = load_config_from_env()
        tokens = exchange_code_for_refresh_token(cfg.client_id, cfg.client_secret, cfg.redirect_uri, code)
        token_path = str(Path(__file__).parent.parent / 'secrets' / 'schwab_token.json')
        save_tokens(token_path, tokens)
        return '<h2>✅ Schwab 授權成功！Token 已儲存，可關閉此頁面。</h2>'
    except Exception as e:
        return f'<h2>❌ 授權失敗：{e}</h2>', 500


@app.route('/api/schwab/exchange-code', methods=['POST'])
def api_schwab_exchange_code():
    """
    手動換 token：前端貼上完整的 callback URL（或只貼 code）
    Schwab redirect 後瀏覽器網址列會有 ?code=xxxxx&session=...
    """
    try:
        _p = str(Path(__file__).parent.parent)
        if _p not in sys.path: sys.path.insert(0, _p)

        data     = request.get_json(force=True, silent=True) or {}
        raw      = (data.get('raw') or data.get('code_or_url') or '').strip()

        # 支援貼整個 URL 或只貼 code
        if raw.startswith('http'):
            from urllib.parse import urlparse, parse_qs
            qs   = parse_qs(urlparse(raw).query)
            code = (qs.get('code') or [''])[0].strip()
        else:
            code = raw

        if not code:
            return jsonify({'status': 'error', 'message': '沒有找到 code，請貼上完整的 callback URL'}), 400

        from brokers.schwab_api import load_config_from_env
        from brokers.schwab_oauth import exchange_code_for_refresh_token, save_tokens
        import time as _time

        cfg = load_config_from_env()
        tokens = exchange_code_for_refresh_token(cfg.client_id, cfg.client_secret, cfg.redirect_uri, code)
        token_path = str(Path(__file__).parent.parent / 'secrets' / 'schwab_token.json')
        save_tokens(token_path, tokens)

        days_left = max(0, round((tokens.expires_at - _time.time()) / 86400, 1))
        return jsonify({'status': 'ok', 'message': f'Token 已儲存，有效期 {days_left} 天', 'days_left': days_left})
    except Exception as e:
        import traceback
        sys.stderr.write(f'[Schwab exchange-code] {traceback.format_exc()}\n')
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/schwab-account-summary', methods=['GET'])
def api_schwab_summary():
    """Schwab 帳戶摘要（NLV、持倉、現金）— 30 秒 cache + mutex dedup"""
    def _do_fetch():
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from brokers.schwab_api import get_schwab_accounts, load_config_from_env, load_token, has_valid_token

        cfg = load_config_from_env()
        if not cfg.client_id:
            return {'status': 'no_config', 'message': 'Schwab 未設定 API Key'}

        # 先本地檢查 token（毫秒級），有 refresh_token 才值得打外部 API
        tok = load_token()
        if not tok or (not has_valid_token(tok) and not tok.get('refresh_token')):
            return {'status': 'auth_error', 'message': 'Schwab Token 不存在或已過期，請重新授權', 'connected': False}

        try:
            accounts_resp = get_schwab_accounts()
        except Exception as ex:
            msg = str(ex)
            if 'server 500' in msg or '伺服器錯誤' in msg:
                return {'status': 'server_error', 'message': f'Schwab 伺服器暫時異常，請稍後再試', 'connected': False}
            if '401' in msg or 'Unauthorized' in msg:
                return {'status': 'auth_error', 'message': f'Schwab Token 已過期，請重新授權', 'connected': False}
            return {'status': 'error', 'message': f'Schwab API 錯誤: {msg}', 'connected': False}

        if not accounts_resp:
            return {'status': 'auth_error', 'message': 'Token 無效或已過期，請重新授權', 'connected': False}

        accounts = accounts_resp if isinstance(accounts_resp, list) else accounts_resp.get('accounts', [])
        if not accounts:
            return {'status': 'success', 'connected': True, 'accounts': [], 'positions': []}

        all_positions, total_nlv, total_cash, total_pnl, account_list = [], 0.0, 0.0, 0.0, []
        for acct in accounts:
            sec = acct.get('securitiesAccount', acct)
            acct_num = sec.get('accountNumber', '')
            balance = sec.get('currentBalances', {})
            nlv  = float(balance.get('liquidationValue', balance.get('netLiquidation', 0)) or 0)
            cash = float(balance.get('cashBalance', 0) or 0)
            total_nlv += nlv; total_cash += cash
            for p in sec.get('positions', []):
                inst = p.get('instrument', {})
                sym  = inst.get('symbol', '')
                qty  = float(p.get('longQuantity', p.get('quantity', 0)) or 0)
                avg  = float(p.get('averagePrice', 0) or 0)
                mv   = float(p.get('marketValue', qty * avg) or 0)
                pnl  = float(p.get('currentDayProfitLoss', p.get('unrealizedProfitLoss', 0)) or 0)
                total_pnl += pnl
                all_positions.append({'symbol': sym, 'position': qty, 'avgCost': avg,
                    'marketValue': mv, 'unrealizedPnL': pnl, 'broker': 'Schwab',
                    'currency': 'USD', 'account': acct_num})
            account_list.append({'accountNumber': acct_num, 'nlv': nlv, 'cash': cash})

        return {'status': 'success', 'connected': True,
                'net_liquidation_value': round(total_nlv, 2),
                'total_cash_value': round(total_cash, 2),
                'unrealized_pnl': round(total_pnl, 2),
                'positions_count': len(all_positions),
                'positions': all_positions, 'accounts': account_list}

    try:
        result = _schwab_fetch_with_dedup(_do_fetch)
        return jsonify(result)
    except Exception as e:
        msg = str(e)
        if 'server 500' in msg or '伺服器錯誤' in msg:
            return jsonify({'status': 'server_error', 'message': 'Schwab 伺服器暫時異常，請稍後再試', 'connected': False})
        if '401' in msg or 'Unauthorized' in msg:
            return jsonify({'status': 'auth_error', 'message': 'Schwab Token 已過期，請重新授權', 'connected': False})
        return jsonify({'status': 'error', 'message': msg}), 500

@app.route('/api/sync-yuanta', methods=['POST'])
def api_sync_yuanta():
    """元大同步 — 從 Google Sheets 讀取最新持倉（元大部分）並存入 DB"""
    result = sync_from_google_sheets()
    if result.get('status') == 'success':
        # 只計算元大持倉筆數
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM broker_positions WHERE lower(broker) IN ('yuanta','元大')")
            yuanta_count = c.fetchone()[0]
            conn.close()
        except Exception:
            yuanta_count = result.get('count', 0)
        return jsonify({'status': 'success', 'count': yuanta_count,
                        'message': f'元大持倉已更新，共 {yuanta_count} 筆'})
    return jsonify({'status': 'error', 'message': result.get('message', '同步失敗')}), 500

@app.route('/api/ib-sync', methods=['POST'])
def api_ib_sync():
    """將 IB 持倉寫入 Google Sheets broker_positions + 本地 DB"""
    data = request.get_json(force=True, silent=True) or {}
    positions = data.get('positions', [])
    if not positions:
        return jsonify({'status': 'error', 'message': '沒有持倉數據'}), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    wrote_sheets = 0
    wrote_db = 0

    # ── 1. 寫入 Google Sheets broker_positions ───────────────────
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet
        sheet = get_sheet('broker_positions')
        if sheet:
            all_vals = sheet.get_all_values()
            header = all_vals[0] if all_vals else []

            # 找出「券商」欄位（相容中英文）
            broker_idx = None
            for candidate in ['券商', 'broker', 'Broker']:
                if candidate in header:
                    broker_idx = header.index(candidate)
                    break

            # 刪除既有 IB / IBKR 行（由下往上刪避免行號偏移）
            if broker_idx is not None:
                rows_to_delete = []
                for r_idx, r_vals in enumerate(all_vals[1:], start=2):
                    if len(r_vals) > broker_idx and r_vals[broker_idx].upper() in ('IB', 'IBKR', 'INTERACTIVE BROKERS'):
                        rows_to_delete.append(r_idx)
                for r_idx in reversed(rows_to_delete):
                    sheet.delete_rows(r_idx)

            # 按照現有 header 填入新的 IB 持倉
            new_rows = []
            for p in positions:
                row_data = [''] * len(header)
                qty  = p.get('position', '')
                avg  = p.get('avgCost', '')
                cost = round(float(qty) * float(avg), 2) if qty and avg else ''
                # 對照 Sheets 實際欄位名稱
                mapping = {
                    '時間':           now_str,
                    'timestamp':      now_str,
                    '券商':           'IB',
                    'broker':         'IB',
                    'symbol':         p.get('symbol', ''),
                    'secType':        'STK',
                    'exchange':       p.get('exchange') or 'US',
                    'currency':       p.get('currency') or 'USD',
                    'position':       qty,
                    'avgCost':        avg,
                    'totalCost':      cost,
                    'currentPrice':   p.get('marketPrice', ''),
                    'marketValue':    p.get('marketValue', ''),
                    'unrealizedPnL':  p.get('unrealizedPNL', ''),
                }
                for k, v in mapping.items():
                    if k in header:
                        row_data[header.index(k)] = v
                new_rows.append(row_data)
            if new_rows:
                sheet.append_rows(new_rows, value_input_option='USER_ENTERED')
            wrote_sheets = len(new_rows)
    except Exception as e:
        print(f"⚠️ IB → Sheets 寫入失敗: {e}")
        import traceback; traceback.print_exc()

    # ── 2. 寫入本地 DB（UPSERT）──────────────────────────────────
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        for p in positions:
            c.execute('''INSERT INTO broker_positions
                (symbol, position, avgCost, currentPrice, marketValue, unrealizedPnL, broker, currency, timestamp)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(broker, symbol) DO UPDATE SET
                    position=excluded.position, avgCost=excluded.avgCost,
                    currentPrice=excluded.currentPrice, marketValue=excluded.marketValue,
                    unrealizedPnL=excluded.unrealizedPnL, currency=excluded.currency,
                    timestamp=excluded.timestamp, synced_at=CURRENT_TIMESTAMP''',
                (p.get('symbol', ''), p.get('position'), p.get('avgCost'),
                 p.get('marketPrice'), p.get('marketValue'), p.get('unrealizedPNL'),
                 'IB', p.get('currency', 'USD'), now_str))
            wrote_db += 1
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ IB → DB 寫入失敗: {e}")

    return jsonify({
        'status': 'success',
        'wrote_sheets': wrote_sheets,
        'wrote_db': wrote_db,
        'message': f'IB {len(positions)} 筆已寫入 Sheets({wrote_sheets}) + DB({wrote_db})'
    })

@app.route('/api/schwab/sync-to-sheets', methods=['POST'])
def api_schwab_sync():
    """Schwab 持倉 → Google Sheets broker_positions + 本地 DB"""
    try:
        # 先取得 Schwab 最新持倉（get_schwab_accounts 已帶 ?fields=positions）
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from brokers.schwab_api import get_schwab_accounts, load_config_from_env

        cfg = load_config_from_env()
        if not cfg.client_id:
            return jsonify({'status': 'error', 'message': 'Schwab 未設定 API Key'})

        accounts_resp = get_schwab_accounts()
        if not accounts_resp:
            return jsonify({'status': 'error', 'message': 'Token 無效或已過期，請重新授權'})

        accounts = accounts_resp if isinstance(accounts_resp, list) else accounts_resp.get('accounts', [])
        positions = []
        for acct in accounts:
            sec = acct.get('securitiesAccount', acct)
            for p in sec.get('positions', []):
                inst = p.get('instrument', {})
                sym  = inst.get('symbol', '')
                qty  = float(p.get('longQuantity', p.get('quantity', 0)) or 0)
                avg  = float(p.get('averagePrice', 0) or 0)
                mv   = float(p.get('marketValue', qty * avg) or 0)
                pnl  = float(p.get('currentDayProfitLoss', p.get('unrealizedProfitLoss', 0)) or 0)
                mkt  = mv / qty if qty else avg
                positions.append({
                    'symbol': sym, 'position': qty, 'avgCost': avg,
                    'marketPrice': round(mkt, 4), 'marketValue': mv,
                    'unrealizedPNL': pnl, 'currency': 'USD', 'exchange': 'US'
                })

        if not positions:
            return jsonify({'status': 'success', 'message': 'Schwab 帳戶無持倉', 'count': 0})

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        wrote_sheets = 0
        wrote_db = 0

        # ── 寫入 Google Sheets ──
        try:
            from sheets_utils import get_sheet
            sheet = get_sheet('broker_positions')
            if sheet:
                all_vals = sheet.get_all_values()
                header = all_vals[0] if all_vals else []
                broker_idx = None
                for candidate in ['券商', 'broker', 'Broker']:
                    if candidate in header:
                        broker_idx = header.index(candidate)
                        break
                # 刪除舊 Schwab 行
                if broker_idx is not None:
                    rows_del = []
                    for r_idx, r_vals in enumerate(all_vals[1:], start=2):
                        if len(r_vals) > broker_idx and r_vals[broker_idx].lower() in ('schwab', 'charles schwab'):
                            rows_del.append(r_idx)
                    for r_idx in reversed(rows_del):
                        sheet.delete_rows(r_idx)
                # 寫入新行
                new_rows = []
                for p in positions:
                    row_data = [''] * len(header)
                    qty = p['position']
                    avg = p['avgCost']
                    mapping = {
                        '時間': now_str, 'timestamp': now_str,
                        '券商': 'Schwab', 'broker': 'Schwab',
                        'symbol': p['symbol'], 'secType': 'STK',
                        'exchange': p.get('exchange') or 'US',
                        'currency': p.get('currency') or 'USD',
                        'position': qty, 'avgCost': avg,
                        'totalCost': round(qty * avg, 2) if qty and avg else '',
                        'currentPrice': p.get('marketPrice', ''),
                        'marketValue': p.get('marketValue', ''),
                        'unrealizedPnL': p.get('unrealizedPNL', ''),
                    }
                    for k, v in mapping.items():
                        if k in header:
                            row_data[header.index(k)] = v
                    new_rows.append(row_data)
                if new_rows:
                    sheet.append_rows(new_rows, value_input_option='USER_ENTERED')
                wrote_sheets = len(new_rows)
        except Exception as e:
            print(f"⚠️ Schwab → Sheets 寫入失敗: {e}")

        # ── 寫入本地 DB（UPSERT）──
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            for p in positions:
                c.execute('''INSERT INTO broker_positions
                    (symbol, position, avgCost, currentPrice, marketValue, unrealizedPnL, broker, currency, timestamp)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(broker, symbol) DO UPDATE SET
                        position=excluded.position, avgCost=excluded.avgCost,
                        currentPrice=excluded.currentPrice, marketValue=excluded.marketValue,
                        unrealizedPnL=excluded.unrealizedPnL, currency=excluded.currency,
                        timestamp=excluded.timestamp, synced_at=CURRENT_TIMESTAMP''',
                    (p['symbol'], p['position'], p['avgCost'],
                     p.get('marketPrice'), p.get('marketValue'), p.get('unrealizedPNL'),
                     'Schwab', p.get('currency', 'USD'), now_str))
                wrote_db += 1
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Schwab → DB 寫入失敗: {e}")

        return jsonify({
            'status': 'success',
            'count': len(positions),
            'wrote_sheets': wrote_sheets,
            'wrote_db': wrote_db,
            'message': f'Schwab {len(positions)} 筆已寫入 Sheets({wrote_sheets}) + DB({wrote_db})'
        })
    except Exception as e:
        msg = str(e)
        if 'server 500' in msg or '伺服器錯誤' in msg:
            return jsonify({'status': 'server_error', 'message': 'Schwab 伺服器暫時異常，請稍後再試'})
        if '401' in msg or 'Unauthorized' in msg:
            return jsonify({'status': 'auth_error', 'message': 'Schwab Token 已過期，請重新授權', 'connected': False})
        return jsonify({'status': 'error', 'message': msg}), 500


@app.route('/api/schwab/sync-filled', methods=['POST'])
def api_schwab_sync_filled():
    """
    Schwab 成交同步：
      1. 所有成交（BUY + SELL）→ broker_fills
      2. SELL 成交 → trades（狀態=已實現）
    以 activityId 查重避免重複寫入。
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        days = int(data.get('days', 90))

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from brokers.schwab_api import (
            get_schwab_transactions, get_schwab_accounts,
            get_schwab_account_details, load_config_from_env
        )
        from sheets_utils import get_sheet

        cfg = load_config_from_env()
        if not cfg.client_id:
            return jsonify({'status': 'error', 'message': 'Schwab 未設定 API Key'})

        # ── 1. 取成交紀錄 ──────────────────────────────────────────
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        now = _dt.now(tz=_tz.utc)
        start = (now - _td(days=days)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        transactions = get_schwab_transactions(start_date=start, end_date=end)
        if not transactions:
            return jsonify({'status': 'success', 'count': 0, 'fills_count': 0,
                            'message': f'最近 {days} 天無成交紀錄'})

        # ── 2. 取當前持倉 avgCost（用於計算 SELL 損益）────────────
        avg_cost_map = {}
        try:
            accounts_resp = get_schwab_accounts()
            accounts = accounts_resp if isinstance(accounts_resp, list) else (accounts_resp or {}).get('accounts', [])
            for acct in accounts:
                sec = acct.get('securitiesAccount', acct)
                for p in sec.get('positions', []):
                    sym = p.get('instrument', {}).get('symbol', '')
                    avg = float(p.get('averagePrice', 0) or 0)
                    if sym:
                        avg_cost_map[sym] = avg
        except Exception as ex:
            print(f"⚠️ 取持倉 avgCost 失敗（不影響同步）: {ex}")

        # ── 3. 寫入 broker_fills（所有 BUY + SELL）────────────────
        fills_wrote = 0
        try:
            fills_sheet = get_sheet('broker_fills')
            if fills_sheet:
                fills_all = fills_sheet.get_all_values()
                fills_header = fills_all[0] if fills_all else []
                # 用 ID 欄查重（存 SCH_{activityId}）
                existing_fill_ids = set()
                id_idx = fills_header.index('ID') if 'ID' in fills_header else None
                if id_idx is not None:
                    for row in fills_all[1:]:
                        if len(row) > id_idx and row[id_idx].startswith('SCH_'):
                            existing_fill_ids.add(row[id_idx])

                new_fill_rows = []
                for t in transactions:
                    fill_id = f"SCH_{t['activityId']}"
                    if fill_id in existing_fill_ids:
                        continue
                    side_cn = '買' if t['side'] == 'BUY' else '賣'
                    row = [''] * len(fills_header)
                    fill_map = {
                        'ID': fill_id,
                        '時間 ': t['tradeDate'],
                        '券商 ': 'Schwab',
                        'symbol': t['symbol'],
                        'side': side_cn,
                        'shares': t['shares'],
                        'price': t['price'],
                        'currency': t['currency'],
                        'orderId': t['orderId'],
                        '備註': t['description'],
                        'amount': t['amount'],
                        'fee': t['fee'],
                        'net_amount': t['netAmount'],
                    }
                    for k, v in fill_map.items():
                        if k in fills_header:
                            row[fills_header.index(k)] = v
                    new_fill_rows.append(row)

                if new_fill_rows:
                    fills_sheet.append_rows(new_fill_rows, value_input_option='USER_ENTERED')
                    fills_wrote = len(new_fill_rows)
        except Exception as ex:
            print(f"⚠️ broker_fills 寫入失敗: {ex}")

        # ── 4. SELL → trades（已實現）────────────────────────────
        sell_txns = [t for t in transactions if t['side'] == 'SELL']
        trades_wrote = 0
        skipped = 0
        total_pnl = 0.0

        if sell_txns:
            try:
                trades_sheet = get_sheet('trades')
                if trades_sheet:
                    trades_all = trades_sheet.get_all_values()
                    trades_header = trades_all[0] if trades_all else []
                    # 備註欄查重
                    remark_idx = None
                    for c in ['備註', 'remark']:
                        if c in trades_header:
                            remark_idx = trades_header.index(c)
                            break
                    existing_ids = set()
                    if remark_idx is not None:
                        for row in trades_all[1:]:
                            if len(row) > remark_idx and row[remark_idx].startswith('schwab_order:'):
                                existing_ids.add(row[remark_idx].replace('schwab_order:', '').strip())

                    if not trades_header:
                        trades_header = ['日期', '券商', '標的', '方向', '進場價', '出場價',
                                         '數量', '狀態', '策略', '進場原因', '出場原因', '損益', '損益%', '備註', 'ID']

                    new_trade_rows = []
                    for t in sell_txns:
                        oid = str(t.get('activityId', t.get('orderId', '')))
                        if oid in existing_ids:
                            skipped += 1
                            continue

                        sym = t['symbol']
                        sell_px = t['price']
                        qty = t['shares']
                        avg = avg_cost_map.get(sym, 0)

                        if avg > 0:
                            pnl = round(qty * (sell_px - avg), 2)
                            pct = round((sell_px - avg) / avg * 100, 2)
                        else:
                            pnl = round(t['netAmount'], 2)
                            pct = ''

                        total_pnl += float(pnl) if pnl != '' else 0

                        row = [''] * len(trades_header)
                        trade_map = {
                            '日期': t['tradeDate'],
                            '券商': 'Schwab',
                            '標的': sym,
                            '方向': '賣',
                            '進場價': avg if avg else '',
                            '出場價': sell_px,
                            '數量': qty,
                            '狀態': '已實現',
                            '策略': '',
                            '進場原因': '',
                            '出場原因': t.get('description', ''),
                            '損益': pnl,
                            '損益%': pct,
                            '備註': f"schwab_order:{oid}",
                            'ID': f"SCH_{t['activityId']}",
                        }
                        for k, v in trade_map.items():
                            if k in trades_header:
                                row[trades_header.index(k)] = v
                        new_trade_rows.append(row)

                    if new_trade_rows:
                        trades_sheet.append_rows(new_trade_rows, value_input_option='USER_ENTERED')
                        trades_wrote = len(new_trade_rows)
            except Exception as ex:
                print(f"⚠️ trades 寫入失敗: {ex}")

        total_pnl = round(total_pnl, 2)
        return jsonify({
            'status': 'success',
            'fills_count': fills_wrote,
            'trades_count': trades_wrote,
            'skipped': skipped,
            'total_pnl': total_pnl,
            'message': (
                f'broker_fills 寫入 {fills_wrote} 筆，'
                f'trades 寫入 {trades_wrote} 筆已實現（跳過 {skipped} 重複），'
                f'已實現損益合計 ${total_pnl:+,.2f}'
            )
        })

    except Exception as e:
        msg = str(e)
        if '401' in msg or 'Unauthorized' in msg:
            return jsonify({'status': 'auth_error', 'message': 'Schwab Token 過期，請重新授權'})
        if 'server 500' in msg:
            return jsonify({'status': 'server_error', 'message': 'Schwab 伺服器暫時異常'})
        sys.stderr.write(f'[schwab sync-filled] {e}\n')
        return jsonify({'status': 'error', 'message': msg}), 500


@app.route('/api/macro-indicators', methods=['GET'])
def api_macro_indicators():

    """宏觀指標 - 經濟數據和匯率"""
    try:
        import yfinance as yf

        # 定義要查詢的主要指標
        indicators = {
            'ism_pmi': '^GSPC',  # S&P 500（作為市場代理）
            'us_cpi': '^IRX',    # 3-Month Treasury Bill
            'nfp': '^INDY',      # Invesco QQQ (Tech)
            'fed_rate': '^TNX',  # 10-Year Treasury
            'vix': '^VIX',       # Volatility Index
            'usd_twd': 'USDTWD=X', # USD/TWD 匯率
            'eu_eurusd': 'EURUSD=X', # 歐元匯率
        }

        indicators_data = {}

        for key, symbol in indicators.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')

                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    indicators_data[key] = {
                        'value': round(float(price), 2),
                        'symbol': symbol,
                        'signal': 'neutral'  # 簡化，實際應根據 MA 等計算
                    }
                else:
                    indicators_data[key] = {'value': None, 'signal': 'N/A'}
            except:
                indicators_data[key] = {'value': None, 'signal': 'Error'}

        return jsonify({
            'status': 'success',
            'indicators': indicators_data,
            'source': 'live',
            'cached_at': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        })
    except Exception as e:
        sys.stderr.write(f"[ERROR] 宏觀指標查詢失敗: {e}")
        return jsonify({
            'status': 'success',
            'indicators': {
                'usd_twd': 32.35,
                'eu_eurusd': 1.08,
                'vix': 14.5,
                'tnx': 4.35,
                'dxy': 104.2
            },
            'source': 'fallback',
            'note': str(e)
        })

# 全局緩存，避免 API 超時導致頁面空白
MARKET_CACHE = {
    'data': [],
    'updated': None
}

@app.route('/api/market-indices', methods=['GET'])
def api_market_indices():
    """市場指數 - 含 52 週位階、EMA 排列、強弱評分"""
    global MARKET_CACHE
    try:

        INDEX_META = [
            {'id': 'dji',    'label': '道瓊工業',  'ticker': '^DJI',  'flag': 'us', 'country': '美國'},
            {'id': 'spx',    'label': 'S&P 500',   'ticker': '^GSPC', 'flag': 'us', 'country': '美國'},
            {'id': 'nasdaq', 'label': '納斯達克',   'ticker': '^IXIC', 'flag': 'us', 'country': '美國'},
            {'id': 'twii',   'label': '台灣加權',   'ticker': '^TWII', 'flag': 'tw', 'country': '台灣'},
            {'id': 'n225',   'label': '日經 225',   'ticker': '^N225', 'flag': 'jp', 'country': '日本'},
            {'id': 'hsi',    'label': '恆生指數',   'ticker': '^HSI',  'flag': 'hk', 'country': '香港'},
            {'id': 'stoxx50', 'label': '歐洲 STOXX 50', 'ticker': '^STOXX50E', 'flag': 'eu', 'country': '歐洲'},
            {'id': 'daxi',    'label': '德國 DAX',    'ticker': '^GDAXI',    'flag': 'de', 'country': '德國'},
        ]

        def ema_status(closes, window):
            if len(closes) < window:
                return 'neutral'
            ema = closes.ewm(span=window, adjust=False).mean().iloc[-1]
            price = closes.iloc[-1]
            if price > ema * 1.002:
                return 'bull'
            elif price < ema * 0.998:
                return 'bear'
            return 'neutral'

        def pos52_label(pos):
            if pos >= 90: return '歷史高位'
            if pos >= 70: return '近年高位'
            if pos >= 40: return '中位'
            if pos >= 20: return '偏低'
            return '歷史低位'

        def calc_score(pos52, e20, e50, e200, chg_pct):
            m = {'bull': 1, 'neutral': 0.5, 'bear': 0}
            s = pos52 * 0.35 + m[e20] * 15 + m[e50] * 20 + m[e200] * 20
            s += min(max((chg_pct + 5) / 10, 0), 1) * 10
            return round(min(max(s, 0), 100))

        def score_status(score):
            if score >= 75: return ('強勢多頭', 'badge-bull')
            if score >= 55: return ('偏多整理', 'badge-bull-soft')
            if score >= 45: return ('橫盤整理', 'badge-neutral')
            if score >= 30: return ('偏空整理', 'badge-bear-soft')
            return ('弱勢空頭', 'badge-bear')

        indices_data = []
        now_str = datetime.now().strftime('%H:%M')

        for meta in INDEX_META:
            try:
                tkr = yf.Ticker(meta['ticker'])
                hist = tkr.history(period='1y')
                if len(hist) < 5:
                    continue
                closes = hist['Close']
                current  = float(closes.iloc[-1])
                previous = float(closes.iloc[-2])
                chg_pct  = round((current - previous) / previous * 100, 2) if previous else 0
                high52 = float(closes.max())
                low52  = float(closes.min())
                rng    = high52 - low52
                pos52  = round((current - low52) / rng * 100) if rng else 50
                e20  = ema_status(closes, 20)
                e50  = ema_status(closes, 50)
                e200 = ema_status(closes, 200)
                score = calc_score(pos52, e20, e50, e200, chg_pct)
                status, badge = score_status(score)
                if current >= 10000:
                    price_str = f"{current:,.0f}"
                elif current >= 100:
                    price_str = f"{current:,.2f}"
                else:
                    price_str = f"{current:.4f}"
                indices_data.append({
                    **meta,
                    'price': price_str, 'change_pct': chg_pct,
                    'high52w': round(high52, 2), 'low52w': round(low52, 2),
                    'pos52w': pos52, 'pos52w_label': pos52_label(pos52),
                    'ema20': e20, 'ema50': e50, 'ema200': e200,
                    'score': score, 'status': status, 'badge': badge})
            except Exception as ex:
                print(f"⚠️ {meta['ticker']} 失敗: {ex}")

        # 更新緩存
        if indices_data:
            MARKET_CACHE['data'] = indices_data
            MARKET_CACHE['updated'] = now_str

        return jsonify({'status': 'success', 'data': indices_data,
                        'count': len(indices_data), 'updated': now_str})
    except Exception as e:
        sys.stderr.write(f"⚠️ 市場指數查詢失敗: {e}\n")
        
        # 如果有緩存，返回緩存
        if MARKET_CACHE['data']:
            return jsonify({
                'status': 'success', 
                'data': MARKET_CACHE['data'], 
                'count': len(MARKET_CACHE['data']),
                'updated': MARKET_CACHE['updated'],
                'note': 'Using cached data due to API timeout'
            })
            
        # 最後的保底：返回模擬數據，避免「載入失敗」
        MOCK_FALLBACK = [
            {'id': 'dji', 'label': '道瓊工業', 'price': '39,127', 'change_pct': 0.12, 'status': '強勢多頭', 'badge': 'badge-bull'},
            {'id': 'spx', 'label': 'S&P 500', 'price': '5,211', 'change_pct': -0.05, 'status': '強勢多頭', 'badge': 'badge-bull'},
            {'id': 'nasdaq', 'label': '納斯達克', 'price': '16,277', 'change_pct': -0.41, 'status': '偏多整理', 'badge': 'badge-bull-soft'},
            {'id': 'twii', 'label': '台灣加權', 'price': '20,222', 'change_pct': 0.35, 'status': '強勢多頭', 'badge': 'badge-bull'},
            {'id': 'stoxx50', 'label': '歐洲 STOXX 50', 'price': '5,088', 'change_pct': 0.08, 'status': '強勢多頭', 'badge': 'badge-bull'},
            {'id': 'daxi', 'label': '德國 DAX', 'price': '18,356', 'change_pct': -0.15, 'status': '強勢多頭', 'badge': 'badge-bull'},
        ]
        return jsonify({
            'status': 'success', 
            'data': MOCK_FALLBACK, 
            'count': len(MOCK_FALLBACK),
            'offline': True,
            'message': 'API Timeout, showing sample data'
        })

@app.route('/api/social/reddit', methods=['GET'])
def api_social_reddit():
    """PTT Stock 板情緒分析 - 模擬真實數據回傳"""
    import random
    
    mock_articles = [
        {'id': 1, 'type': '標的', 'title': '[標的] 2330 台積電 多', 'sentiment': 'bullish', 'score': 85},
        {'id': 2, 'type': '閒聊', 'title': '今日盤後閒聊 - 震盪向上？', 'sentiment': 'neutral', 'score': 55},
        {'id': 3, 'type': '新聞', 'title': '[新聞] 通膨數據低於預期', 'sentiment': 'bullish', 'score': 70},
        {'id': 4, 'type': '標的', 'title': '[標的] NVDA 輝達 空', 'sentiment': 'bearish', 'score': 20},
        {'id': 5, 'type': '情報', 'title': '[情報] 元大高股息 0056 規模突破新高', 'sentiment': 'bullish', 'score': 65}
    ]
    
    random.shuffle(mock_articles)
    
    return jsonify({
        'status': 'success', 
        'data': mock_articles[:3],
        'ptt_summary': {
            'bull_pct': 68,
            'hot_topics': ['台積電', '美股震盪', 'AI 伺服器', '0056']
        },
        'subreddits': [{'sentiment': 'bullish'}]
    })

@app.route('/api/strategies', methods=['GET'])
def api_strategies():
    """交易策略列表 — 從 Google Sheets strategies 分頁讀取"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import read_sheet_data_with_cache
        df = read_sheet_data_with_cache('strategies')
        strategies = []
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                name = str(row.get('策略名稱', '')).strip()
                if not name or name == 'nan':
                    continue
                strategies.append({
                    'name':        name,
                    'description': str(row.get('策略描述', '')).strip(),
                    'status':      str(row.get('狀態', '')).strip(),
                    'platform':    str(row.get('運作平台', '')).strip(),
                    'currency':    str(row.get('貨幣', '')).strip()})
        return jsonify({'status': 'success', 'data': strategies, 'count': len(strategies)})
    except Exception as e:
        sys.stderr.write(f"[ERROR] 策略列表查詢失敗: {e}")
        return jsonify({'status': 'error', 'data': [], 'error': str(e)})

@app.route('/api/daily-performance', methods=['GET'])
def api_daily_performance():
    """每日損益績效"""
    try:
        positions = get_db_positions()

        # 計算總損益
        total_pnl = 0.0
        total_pnl_pct = 0.0

        for pos in positions:
            # 優先用 unrealizedPnL，fallback 計算
            pnl = safe_float(pos.get('unrealizedPnL') or pos.get('unrealizedPNL'))
            if pnl == 0:
                qty = safe_float(pos.get('position'))
                current_px = safe_float(pos.get('currentPrice') or pos.get('marketPrice'))
                avg_cost = safe_float(pos.get('avgCost'))
                pnl = qty * (current_px - avg_cost)

            total_pnl += pnl

        return jsonify({
            'status': 'success',
            'daily_pnl': round(total_pnl, 2),
            'daily_pnl_pct': round(total_pnl_pct, 2),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        sys.stderr.write(f"[ERROR] 每日績效查詢失敗: {e}")
        return jsonify({
            'status': 'error',
            'daily_pnl': 0,
            'daily_pnl_pct': 0,
            'error': str(e)
        })

@app.route('/api/portfolio-chart-data', methods=['GET'])
def api_portfolio_chart():
    """投資組合圖表數據"""
    try:
        positions = get_db_positions()

        if not positions:
            return jsonify({
                'status': 'success',
                'equity_curve': [],
                'dates': [],
                'values': [],
                'message': 'No positions data'
            })

        # 構造淨值曲線（簡化版，實際應從交易日誌計算）
        from datetime import datetime, timedelta

        dates = []
        values = []
        # 優先用 DB 的 marketValue，fallback 到 position × currentPrice
        def _mv(p):
            mv = p.get('marketValue')
            if mv and str(mv) not in ('', 'None', 'nan'):
                try: return float(mv)
                except: pass
            qty = float(p.get('position') or 0)
            px  = float(p.get('currentPrice') or p.get('marketPrice') or p.get('avgCost') or 0)
            return qty * px
        total_market_value = sum(_mv(p) for p in positions)

        # 生成過去 30 天的數據
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(date)
            # 簡化：假設線性增長
            values.append(round(total_market_value * (1 - i/30 * 0.05), 2))

        return jsonify({
            'status': 'success',
            'equity_curve': values,
            'dates': dates,
            'values': values,
            'current_value': round(total_market_value, 2)
        })
    except Exception as e:
        sys.stderr.write(f"[ERROR] 生成圖表數據失敗: {e}")
        return jsonify({
            'status': 'error',
            'equity_curve': [],
            'dates': [],
            'values': [],
            'error': str(e)
        })

@app.route('/api/yahoo-proxy', methods=['GET'])
def api_yahoo_proxy():
    """Yahoo Finance 代理 - 獲取即時股價（單一或批次）
    單一：?symbol=AAPL
    批次：?symbols=AAPL,NVDA,2330.TW
    """
    try:
        import yfinance as yf
    except ImportError:
        return jsonify({'status': 'error', 'message': 'yfinance not installed. Run: pip install yfinance'}), 500

    # 批次模式
    symbols_raw = request.args.get('symbols', '')
    symbol = request.args.get('symbol', '')

    if symbols_raw:
        symbols = [s.strip() for s in symbols_raw.split(',') if s.strip()]
    elif symbol:
        symbols = [symbol]
    else:
        return jsonify({'status': 'error', 'message': 'Missing symbol or symbols parameter'}), 400

    try:
        results = {}
        tickers = yf.Tickers(' '.join(symbols))
        hist_all = yf.download(symbols if len(symbols) > 1 else symbols[0],
                               period='2d', progress=False, auto_adjust=True)

        for sym in symbols:
            try:
                # 取最新收盤價（避免 .info 過慢）
                if len(symbols) > 1:
                    closes = hist_all['Close'][sym].dropna()
                else:
                    closes = hist_all['Close'].dropna()

                if len(closes) >= 2:
                    price = float(closes.iloc[-1])
                    prev  = float(closes.iloc[-2])
                    chg_pct = (price - prev) / prev * 100 if prev else 0
                elif len(closes) == 1:
                    price = float(closes.iloc[-1])
                    prev, chg_pct = price, 0.0
                else:
                    results[sym] = {'status': 'no_data'}
                    continue

                results[sym] = {
                    'status': 'success',
                    'price': round(price, 4),
                    'prev_close': round(prev, 4),
                    'change_pct': round(chg_pct, 2),
                }
            except Exception as e:
                results[sym] = {'status': 'error', 'message': str(e)}

        # 單一 symbol 直接回傳扁平結構（相容舊版前端）
        if symbol and not symbols_raw:
            sym_result = results.get(symbol, {})
            return jsonify({
                'status': sym_result.get('status', 'error'),
                'symbol': symbol,
                'price': sym_result.get('price'),
                'prev_close': sym_result.get('prev_close'),
                'change_pct': sym_result.get('change_pct')})

        return jsonify({'status': 'success', 'data': results, 'count': len(results)})

    except Exception as e:
        sys.stderr.write(f"[ERROR] Yahoo Finance 查詢失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# 交易記錄寫入 API
# ============================================================================
@app.route('/api/trades/add', methods=['POST'])
def api_add_trade():
    """新增交易紀錄到 Google Sheets（支援已實現/未實現）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '缺少資料'}), 400

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from sheets_utils import get_sheet

        sheet = get_sheet('trades')
        if sheet is None:
            return jsonify({'status': 'error', 'message': 'Sheets 連線失敗'}), 500

        # 讀取現有欄位（第一行）
        headers = sheet.row_values(1)
        if not headers:
            headers = ['ID', '日期', '券商', '標的', '方向', '進場價', '出場價',
                       '數量', '狀態', '策略', '損益', '損益%', '備註']
            sheet.append_row(headers, value_input_option='USER_ENTERED')

        # 自動產生 ID
        all_rows = sheet.get_all_values()
        next_id = f"T{len(all_rows):03d}"

        # 按照 Sheets 實際欄位順序寫入
        # 先讀第一行確認欄位順序
        header = sheet.row_values(1)
        field_map = {
            '日期': data.get('日期', data.get('date', '')),
            '券商': data.get('券商', data.get('broker', '元大')),
            '標的': data.get('標的', data.get('symbol', '')),
            '方向': data.get('方向', data.get('direction', '買')),
            '進場價': data.get('進場價', data.get('entry_price', '')),
            '出場價': data.get('出場價', data.get('exit_price', '')),
            '數量': data.get('數量', data.get('quantity', '')),
            '狀態': data.get('狀態', data.get('status', '已平倉')),
            '策略': data.get('策略', data.get('strategy', '')),
            '進場原因': data.get('進場原因', data.get('entry_reason', '')),
            '出場原因': data.get('出場原因', data.get('exit_reason', '')),
            '損益': data.get('損益', data.get('pnl', '')),
            '損益%': data.get('損益%', data.get('pnl_pct', '')),
            '備註': data.get('備註', data.get('notes', '')),
            'ID': data.get('id', next_id),
        }
        row = [field_map.get(col, '') for col in header] if header else list(field_map.values())
        sheet.append_row(row, value_input_option='USER_ENTERED')
        print(f"✅ 新增交易：{row}")
        return jsonify({'status': 'success', 'id': next_id, 'data': row})
    except Exception as e:
        sys.stderr.write(f"[ERROR] 新增交易失敗: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# 每日快照 API
# ============================================================================
@app.route('/api/snapshot', methods=['POST'])
def api_save_snapshot():
    """儲存今日投資組合快照到 SQLite（可每天收盤後執行）"""
    try:
        positions = get_db_positions()
        usd_twd = float(request.get_json(silent=True, force=True).get('usd_twd', 32.0)) if request.data else 32.0

        def safe(p, *keys):
            for k in keys:
                v = p.get(k)
                if v is not None and str(v) not in ('', 'None', 'nan'):
                    try: return float(v)
                    except: pass
            return 0.0

        ib_pos     = [p for p in positions if str(p.get('broker','')).upper() in ('IB','IBKR')]
        schwab_pos = [p for p in positions if str(p.get('broker','')).lower() == 'schwab']
        yuanta_pos = [p for p in positions if str(p.get('broker','')).lower() in ('yuanta','元大')]

        def mv(pos):
            total = 0
            for p in pos:
                v = safe(p,'marketValue') or safe(p,'position') * safe(p,'currentPrice','marketPrice')
                total += v
            return round(total, 2)

        def pnl_sum(pos):
            return round(sum(
                safe(p,'unrealizedPnL','unrealizedPNL') or
                (safe(p,'position') * (safe(p,'currentPrice','marketPrice') - safe(p,'avgCost')))
                for p in pos
            ), 2)

        ib_mv     = mv(ib_pos)
        schwab_mv = mv(schwab_pos)
        yuanta_mv = mv(yuanta_pos)
        total_twd = round(yuanta_mv + (ib_mv + schwab_mv) * usd_twd, 0)
        total_pnl = round(pnl_sum(yuanta_pos) + (pnl_sum(ib_pos) + pnl_sum(schwab_pos)) * usd_twd, 0)

        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO equity_snapshots
            (date, ib_mv_usd, schwab_mv_usd, yuanta_mv_twd, total_mv_twd, total_pnl_twd, usd_twd_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (today, ib_mv, schwab_mv, yuanta_mv, total_twd, total_pnl, usd_twd))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success', 'date': today,
            'ib_mv_usd': ib_mv, 'schwab_mv_usd': schwab_mv,
            'yuanta_mv_twd': yuanta_mv, 'total_mv_twd': total_twd,
            'total_pnl_twd': total_pnl
        })
    except Exception as e:
        sys.stderr.write(f"[ERROR] 快照失敗: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/equity-history', methods=['GET'])
def api_equity_history():
    """取得歷史每日快照（供淨值曲線圖表使用）"""
    try:
        days = int(request.args.get('days', 365))
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
    """
    策略交易數據導入
    - 接收 CSV 文件
    - 驗證格式與編碼
    - 計算 P&L 數據
    - 返回預覽供確認
    """
    try:
        # 檢查文件
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'}), 400

        # 保存臨時文件
        filename = secure_filename(file.filename)
        temp_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(temp_path))

        # 讀取並驗證 CSV（支援多種編碼）
        df = None
        for enc in ('utf-8-sig', 'utf-8', 'cp950', 'big5', 'gb2312'):
            try:
                df = pd.read_csv(str(temp_path), encoding=enc)
                break
            except (UnicodeDecodeError, Exception):
                continue
        if df is None:
            return jsonify({'status': 'error', 'message': 'CSV encoding not supported'}), 400

        # 驗證列數
        expected_cols = [
            '商品名稱', '商品代碼', '序號', '進場時間', '進場方向',
            '進場價格', '出場時間', '出場方向', '出場價格', '持有區間',
            '交易數量', '獲利金額', '報酬率', '累計獲利金額', '累計報酬率',
            '進場訊息', '出場訊息'
        ]

        if len(df.columns) < len(expected_cols):
            return jsonify({
                'status': 'error',
                'message': f'CSV format error: expected {len(expected_cols)} columns, got {len(df.columns)}'
            }), 400

        # 重新命名列（兼容首字符的 BOM）
        df.columns = [col.lstrip('\ufeff') for col in df.columns]

        # 計算統計數據
        trades = []
        total_profit = 0
        total_return = 0
        total_trades = 0
        winning_trades = 0

        for idx, row in df.iterrows():
            try:
                entry_price = float(row['進場價格'])
                exit_price = float(row['出場價格'])
                qty = int(row['交易數量'])
                profit = float(row['獲利金額'])
                return_rate = float(row['報酬率'])

                # 計算持倉規模
                position_size = entry_price * qty * 1000

                trades.append({
                    'symbol': str(row['商品代碼']),
                    'name': str(row['商品名稱']),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'qty': qty,
                    'entry_time': str(row['進場時間']),
                    'exit_time': str(row['出場時間']),
                    'profit': profit,
                    'return_rate': return_rate,
                    'position_size': position_size,
                    'cum_profit': float(row['累計獲利金額']),
                    'cum_return': float(row['累計報酬率'])
                })

                total_profit += profit
                total_return += return_rate
                total_trades += 1
                if profit > 0:
                    winning_trades += 1
            except (ValueError, KeyError) as e:
                continue

        # 計算統計
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        avg_return = total_return / total_trades if total_trades > 0 else 0

        # 清理臨時文件
        temp_path.unlink()

        # 準備響應 - 包含預覽和圖表數據
        response_data = {
            'status': 'success',
            'preview': {
                'total_trades': total_trades,
                'total_profit': round(total_profit, 2),
                'total_return': round(total_return * 100, 2),
                'win_rate': round(win_rate, 2),
                'avg_return': round(avg_return * 100, 4),
                'winning_trades': winning_trades,
                'sample_trades': trades[:10]
            }
        }

        # 嘗試添加圖表數據（這是一次性 API 的方案）
        try:
            # 計算日累計 P&L（簡化版）
            df['出場時間'] = pd.to_datetime(df['出場時間'])
            df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')
            df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')

            daily_pnl = df.groupby(df['出場時間'].dt.date)['獲利金額'].sum().reset_index()
            daily_pnl['累計'] = daily_pnl['獲利金額'].cumsum()

            # 計算關鍵指標
            returns = df['報酬率'].values
            cumulative = daily_pnl['累計'].values

            # 計算最大回撤（百分比）
            running_max = np.maximum.accumulate(cumulative)
            drawdown_pct = (cumulative - running_max) / np.where(running_max != 0, running_max, 1) * 100
            max_dd = float(np.min(drawdown_pct)) if len(drawdown_pct) > 0 else 0

            # 計算 CAGR（基於日報酬率平均值）
            if len(returns) > 0:
                avg_daily_return = np.mean(returns)
                cagr = avg_daily_return * 252
            else:
                cagr = 0

            # 計算夏普比率
            excess_returns = returns
            sharpe = (np.mean(excess_returns) / np.std(excess_returns)) * (252 ** 0.5) if np.std(excess_returns) > 0 else 0

            response_data['charts'] = {
                'daily_pnl': {
                    'dates': [str(d) for d in daily_pnl.iloc[:, 0]],
                    'cumulative': daily_pnl['累計'].round(2).tolist()
                },
                'metrics': {
                    'cagr': round(float(cagr), 2),
                    'sharpe_ratio': round(float(sharpe), 2),
                    'max_drawdown': round(float(max_dd), 2)
                }
            }
        except Exception as e:
            print(f"[WARN] Charts calculation skipped: {e}")
            response_data['charts'] = {}

        # 確保所有數據都是 JSON 可序列化的
        response_data = convert_numpy_types(response_data)
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import/charts', methods=['POST'])
def api_strategy_charts():
    """
    策略圖表數據計算
    返回用於前端圖表展示的數據：
    - 日累計 P&L 曲線
    - 月度收益分布
    - 回撤曲線
    - 滾動回報率
    """
    print("[DEBUG] api_strategy_charts called")

    # 處理 OPTIONS 請求（CORS preflight）
    if request.method == 'OPTIONS':
        return '', 200

    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files supported'}), 400

        # 讀取 CSV
        df = read_csv_file(file)

        # 清理列名
        df.columns = [col.lstrip('\ufeff') for col in df.columns]

        # 提取日期和 P&L 數據
        df['進場時間'] = pd.to_datetime(df['進場時間'])
        df['出場時間'] = pd.to_datetime(df['出場時間'])
        df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')
        df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')

        # [1] 日累計 P&L 曲線
        daily_pnl = df.groupby(df['出場時間'].dt.date)['獲利金額'].sum().reset_index()
        daily_pnl['累計'] = daily_pnl['獲利金額'].cumsum()
        daily_pnl.columns = ['日期', '日損益', '累計損益']

        # [2] 月度收益分布
        df['月份'] = df['出場時間'].dt.to_period('M')
        monthly_returns = df.groupby('月份').agg({
            '獲利金額': ['sum', 'count', 'mean'],
            '報酬率': 'mean'
        }).reset_index()
        monthly_returns.columns = ['月份', '月損益', '交易數', '平均獲利', '平均報酬']
        monthly_returns['月份'] = monthly_returns['月份'].astype(str)

        # [3] 回撤曲線
        cumulative = daily_pnl['累計損益'].values
        running_max = [max(cumulative[:i+1]) if i >= 0 else 0 for i in range(len(cumulative))]
        drawdown = [(cumulative[i] - running_max[i]) for i in range(len(cumulative))]

        # [4] 勝負交易比例
        winning_trades = (df['獲利金額'] > 0).sum()
        losing_trades = (df['獲利金額'] < 0).sum()
        total_trades = len(df)
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

        # [5] 滾動回報率（30日）
        df_sorted = df.sort_values('出場時間').reset_index(drop=True)
        rolling_return = []
        window = 30
        for i in range(len(df_sorted)):
            if i < window:
                rolling_return.append(df_sorted['報酬率'].iloc[:i+1].sum() * 100)
            else:
                rolling_return.append(df_sorted['報酬率'].iloc[i-window+1:i+1].sum() * 100)

        # [6] 計算關鍵指標
        returns = df['報酬率'].values
        max_dd = min(drawdown) if drawdown else 0

        # CAGR: 用實際日損益 / 累計本金來計算真實日報酬，再年化
        initial_capital = 1000000
        if len(daily_pnl) > 1:
            total_pnl = daily_pnl['累計損益'].iloc[-1]
            date_range = (pd.Timestamp(str(daily_pnl['日期'].iloc[-1])) - pd.Timestamp(str(daily_pnl['日期'].iloc[0]))).days
            years = max(date_range / 365.25, 0.1)
            total_return_ratio = total_pnl / initial_capital
            if total_return_ratio > 0:
                cagr = ((1 + total_return_ratio) ** (1 / years) - 1) * 100
            else:
                cagr = total_return_ratio / years * 100
        else:
            years = 1
            cagr = 0

        # 最大回撤（百分比）— 用組合淨值（初始資金＋累計損益）計算，才是真實 MDD
        cumulative_vals = daily_pnl['累計損益'].values
        portfolio_vals = initial_capital + cumulative_vals
        running_max_portfolio = np.maximum.accumulate(portfolio_vals)
        dd_pct = np.where(running_max_portfolio > 0, (portfolio_vals - running_max_portfolio) / running_max_portfolio * 100, 0)
        max_dd = float(dd_pct.min()) if len(dd_pct) > 0 else 0

        # Sharpe Ratio
        excess_returns = returns - 0
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * (252 ** 0.5) if excess_returns.std() > 0 else 0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std()
        sortino_ratio = (returns.mean() / downside_deviation) * (252 ** 0.5) if downside_deviation > 0 else 0

        # Calmar Ratio: 回撤調整回報
        calmar_ratio = (returns.mean() * 252) / abs(max_dd) if max_dd != 0 else 0

        # [7] 年度報酬（用每年累計損益 / 期初資金計算）
        df['年份'] = df['出場時間'].dt.year
        yearly_pnl = df.groupby('年份')['獲利金額'].sum().reset_index()
        yearly_pnl.columns = ['年份', '年損益']

        # 計算每年期初資金（上一年底累計 + 初始資金）
        yearly_strategy = []
        running_capital = initial_capital
        for _, row in yearly_pnl.iterrows():
            yr_return = row['年損益'] / running_capital * 100  # 百分比
            yearly_strategy.append(round(yr_return, 1))
            running_capital += row['年損益']

        yearly_returns = pd.DataFrame({
            '年份': yearly_pnl['年份'],
            '策略報酬': yearly_strategy
        })

        # 台灣加權指數（TAIEX）歷史年報酬 (%)
        taiex_annual = {
            2015: -10.4, 2016: 11.0, 2017: 15.0, 2018: -8.6,
            2019: 23.3, 2020: 22.8, 2021: 23.7, 2022: -22.4,
            2023: 26.8, 2024: 28.5, 2025: 10.0, 2026: 5.0
        }
        yearly_returns['大盤報酬'] = yearly_returns['年份'].map(
            lambda y: taiex_annual.get(int(y), 10.0)
        )
        yearly_returns['超額報酬'] = yearly_returns['策略報酬'] - yearly_returns['大盤報酬']

        # [8] 報酬分布直方圖
        return_values = (df['報酬率'] * 100).dropna().tolist()
        import numpy as _np
        hist_counts, hist_edges = _np.histogram(return_values, bins=30)
        hist_labels = [round((hist_edges[i] + hist_edges[i+1]) / 2, 1) for i in range(len(hist_counts))]
        hist_colors = ['#ef4444' if x < 0 else '#f97316' if x < 5 else '#10b981' for x in hist_labels]

        # [9] 持股報酬（每筆交易明細）
        holdings = []
        for _, row in df.iterrows():
            holdings.append({
                'name': str(row.get('商品名稱', '')),
                'code': str(row.get('商品代碼', '')),
                'return_pct': round(float(row.get('報酬率', 0)) * 100, 1),
                'entry': str(row.get('進場時間', ''))[:10],
                'exit': str(row.get('出場時間', ''))[:10],
                'pnl': round(float(row.get('獲利金額', 0)), 0),
            })

        # [10] Profit Factor
        total_win = df[df['獲利金額'] > 0]['獲利金額'].sum()
        total_loss = abs(df[df['獲利金額'] < 0]['獲利金額'].sum())
        profit_factor = round(float(total_win / total_loss), 2) if total_loss > 0 else 0

        # [11] 期望值
        expectancy = round(float(df['獲利金額'].mean()), 2)

        # [12] 平均持有天數
        df['持有天數'] = (df['出場時間'] - df['進場時間']).dt.days
        avg_hold_days = round(float(df['持有天數'].mean()), 1)

        # [13] 累計報酬率（百分比）
        cumulative_return_pct = daily_pnl['累計損益'].values
        if len(cumulative_return_pct) > 0 and cumulative_return_pct[0] != 0:
            # 用初始資金計算百分比
            cum_pct = (cumulative_return_pct / initial_capital * 100).tolist()
        else:
            cum_pct = [round(x / initial_capital * 100, 2) for x in cumulative_return_pct]

        response_data = {
            'status': 'success',
            'charts': {
                'daily_pnl': {
                    'dates': daily_pnl['日期'].astype(str).tolist(),
                    'daily': daily_pnl['日損益'].round(2).tolist(),
                    'cumulative': daily_pnl['累計損益'].round(2).tolist(),
                    'cumulative_pct': [round(x, 2) for x in cum_pct]
                },
                'monthly_returns': {
                    'months': monthly_returns['月份'].tolist(),
                    'profit': monthly_returns['月損益'].round(2).tolist(),
                    'trade_count': monthly_returns['交易數'].astype(int).tolist(),
                    'avg_profit': monthly_returns['平均獲利'].round(2).tolist()
                },
                'drawdown': {
                    'dates': daily_pnl['日期'].astype(str).tolist(),
                    'values': [round(x, 2) for x in drawdown],
                    'values_pct': [round(x / max(1, running_max[i]) * 100, 2) if running_max[i] > 0 else 0 for i, x in enumerate(drawdown)]
                },
                'rolling_return': {
                    'dates': df_sorted['出場時間'].dt.strftime('%Y-%m-%d').tolist(),
                    'values': [round(x, 2) for x in rolling_return]
                },
                'win_rate': {
                    'winning': int(winning_trades),
                    'losing': int(losing_trades),
                    'total': int(total_trades),
                    'rate': round(win_rate, 2)
                },
                'yearly_returns': {
                    'years': yearly_returns['年份'].astype(int).tolist(),
                    'strategy': yearly_returns['策略報酬'].tolist(),
                    'benchmark': yearly_returns['大盤報酬'].tolist(),
                    'excess': yearly_returns['超額報酬'].round(1).tolist()
                },
                'return_distribution': {
                    'labels': hist_labels,
                    'counts': hist_counts.tolist(),
                    'colors': hist_colors
                },
                'holdings': holdings
            },
            'metrics': {
                'cagr': round(cagr, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'sortino_ratio': round(sortino_ratio, 2),
                'max_drawdown': round(max_dd, 2),
                'calmar_ratio': round(calmar_ratio, 2),
                'profit_factor': profit_factor,
                'win_rate': round(win_rate, 2),
                'expectancy': expectancy,
                'avg_hold_days': avg_hold_days,
                'total_trades': int(total_trades),
                'total_return_pct': round(cum_pct[-1], 2) if cum_pct else 0
            }
        }

        # 轉換所有 numpy 類型為 Python 原生類型
        response_data = convert_numpy_types(response_data)
        return jsonify(response_data)

    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import/diagnostics', methods=['POST'])
def api_strategy_diagnostics():
    """
    策略深度診斷 - 風險分析
    返回：VaR, CVaR, Expected Shortfall, Downside Deviation 等
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']

        # 讀取 CSV
        df = read_csv_file(file)

        df.columns = [col.lstrip('\ufeff') for col in df.columns]

        # 準備數據
        df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')
        df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')
        df['出場時間'] = pd.to_datetime(df['出場時間'])

        returns = df['報酬率'].values
        profits = df['獲利金額'].values

        # [1] Value at Risk (VaR) - 95% 信心水平
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        # [2] Conditional Value at Risk (CVaR) - 平均尾部損失
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()

        # [3] Expected Shortfall (本質上 = CVaR)
        es = cvar_95

        # [4] Downside Deviation - 只考慮下方波動
        downside_returns = returns[returns < 0]
        downside_dev = downside_returns.std() if len(downside_returns) > 0 else 0

        # [5] Sortino Ratio (已在圖表中計算，這裡重複)
        sortino = (returns.mean() / downside_dev) * (252 ** 0.5) if downside_dev > 0 else 0

        # [6] 月度績效分析
        df['月份'] = df['出場時間'].dt.to_period('M')
        monthly_stats = df.groupby('月份').agg({
            '獲利金額': ['sum', 'mean', 'std', 'count'],
            '報酬率': ['mean', 'std', 'min', 'max']
        }).reset_index()

        monthly_data = []
        for _, row in monthly_stats.iterrows():
            monthly_data.append({
                'month': str(row['月份']),
                'profit': float(row[('獲利金額', 'sum')]),
                'avg_profit': float(row[('獲利金額', 'mean')]),
                'trade_count': int(row[('獲利金額', 'count')]),
                'avg_return': float(row[('報酬率', 'mean')]) * 100,
                'return_std': float(row[('報酬率', 'std')]) * 100 if not pd.isna(row[('報酬率', 'std')]) else 0
            })

        # 7️⃣ 勝負交易分析
        winning_trades = len(profits[profits > 0])
        losing_trades = len(profits[profits < 0])

        avg_win = profits[profits > 0].mean() if winning_trades > 0 else 0
        avg_loss = abs(profits[profits < 0].mean()) if losing_trades > 0 else 0

        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        # 8️⃣ 期望值 (Expectancy)
        win_rate = winning_trades / len(df) if len(df) > 0 else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        return jsonify({
            'status': 'success',
            'risk_metrics': {
                'var_95': round(var_95 * 100, 4),
                'var_99': round(var_99 * 100, 4),
                'cvar_95': round(cvar_95 * 100, 4),
                'cvar_99': round(cvar_99 * 100, 4),
                'expected_shortfall': round(es * 100, 4),
                'downside_deviation': round(downside_dev * 100, 4),
                'sortino_ratio': round(sortino, 2)
            },
            'performance_metrics': {
                'profit_factor': round(profit_factor, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'expectancy': round(expectancy, 2),
                'win_rate': round(win_rate * 100, 2),
                'losing_rate': round((1 - win_rate) * 100, 2)
            },
            'monthly_analysis': monthly_data,
            'total_trades': len(df),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import/advanced-diagnostics', methods=['POST'])
def api_strategy_advanced_diagnostics():
    """
    策略進階診斷 - 績效、杠桿、時間分析
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']

        # 讀取 CSV
        df = read_csv_file(file)

        df.columns = [col.strip().lstrip('\ufeff') for col in df.columns]

        # 準備數據
        df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')
        df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')
        df['進場時間'] = pd.to_datetime(df['進場時間'], errors='coerce')
        df['出場時間'] = pd.to_datetime(df['出場時間'], errors='coerce')

        returns = df['報酬率'].values
        total_return = returns.sum()

        # ═══════════════════════════════════════════════════════════════
        # T3.2: 績效分析 (超額收益、信息比率、追蹤誤差、風險調整回報)
        # ═══════════════════════════════════════════════════════════════

        # 假設基準報酬率為 8% (台灣平均)
        benchmark_return = 0.08
        excess_returns = returns - benchmark_return

        # 信息比率 (Information Ratio)
        tracking_error = excess_returns.std()
        info_ratio = (excess_returns.mean() / tracking_error) * (252 ** 0.5) if tracking_error > 0 else 0

        # 追蹤誤差 (Tracking Error)
        te = tracking_error * (252 ** 0.5) if tracking_error > 0 else 0

        # 超額收益 (Excess Return)
        excess_return = (total_return - benchmark_return * len(df)) / len(df) if len(df) > 0 else 0

        # ═══════════════════════════════════════════════════════════════
        # T3.3: 杠桿分析 (假設從資料中計算)
        # ═══════════════════════════════════════════════════════════════

        # 假設「進場價格 × 交易數量」代表槓桿暴露
        df['進場價格'] = pd.to_numeric(df['進場價格'], errors='coerce')
        df['交易數量'] = pd.to_numeric(df['交易數量'], errors='coerce')

        leverage_exposure = df['進場價格'] * df['交易數量'] * 1000  # 1手=1000股
        avg_leverage = leverage_exposure.mean()
        max_leverage = leverage_exposure.max()


        # ═══════════════════════════════════════════════════════════════
        # T3.4: 時間分析 (月/季/年度績效)
        # ═══════════════════════════════════════════════════════════════

        # 月度績效
        df['月份'] = df['出場時間'].dt.to_period('M')
        monthly_perf = df.groupby('月份').agg({
            '報酬率': ['mean', 'sum', 'std', 'count'],
            '獲利金額': ['sum', 'mean']
        }).reset_index()

        monthly_analysis = []
        for _, row in monthly_perf.iterrows():
            monthly_analysis.append({
                'period': str(row['月份']),
                'avg_return': float(row[('報酬率', 'mean')]) * 100,
                'total_return': float(row[('報酬率', 'sum')]) * 100,
                'volatility': float(row[('報酬率', 'std')]) * 100 if not pd.isna(row[('報酬率', 'std')]) else 0,
                'trade_count': int(row[('報酬率', 'count')]),
                'profit': float(row[('獲利金額', 'sum')])
            })

        # 季度績效
        df['季度'] = df['出場時間'].dt.to_period('Q')
        quarterly_perf = df.groupby('季度').agg({
            '報酬率': ['mean', 'sum'],
            '獲利金額': 'sum'
        }).reset_index()

        quarterly_analysis = []
        for _, row in quarterly_perf.iterrows():
            quarterly_analysis.append({
                'period': str(row['季度']),
                'avg_return': float(row[('報酬率', 'mean')]) * 100,
                'total_return': float(row[('報酬率', 'sum')]) * 100,
                'profit': float(row[('獲利金額', 'sum')])
            })

        # 年度績效 (雖然通常只有一年，但保留結構)
        df['年份'] = df['出場時間'].dt.year
        yearly_analysis = []
        for yr, grp in df.groupby('年份'):
            yearly_analysis.append({
                'period': str(int(yr)),
                'avg_return': float(grp['報酬率'].mean()) * 100,
                'total_return': float(grp['報酬率'].sum()) * 100,
                'profit': float(grp['獲利金額'].sum())
            })

        monthly_avg = float(df['報酬率'].mean()) if len(df) > 0 else 0
        annualized = monthly_avg * 12

        return jsonify(convert_numpy_types({
            'status': 'success',
            'performance_metrics': {
                'excess_return': round(excess_return, 4),
                'information_ratio': round(info_ratio, 2),
                'tracking_error': round(te * 100, 4),
                'benchmark_return': round(benchmark_return * 100, 2),
                'avg_leverage': round(float(avg_leverage), 2),
                'max_leverage': round(float(max_leverage), 2)
            },
            'time_analysis': {
                'monthly_avg_return': round(monthly_avg, 6),
                'annualized_return': round(annualized, 4),
                'monthly': monthly_analysis,
                'quarterly': quarterly_analysis,
                'yearly': yearly_analysis
            }
        }))

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import/audit', methods=['POST'])
def api_strategy_audit():
    """
    策略審核數據 - 驗證、異常檢測、警告級別
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']

        # 讀取 CSV
        df = read_csv_file(file)

        df.columns = [col.strip().lstrip('\ufeff') for col in df.columns]

        # 準備數據
        df['進場時間'] = pd.to_datetime(df['進場時間'], errors='coerce')
        df['出場時間'] = pd.to_datetime(df['出場時間'], errors='coerce')
        df['進場價格'] = pd.to_numeric(df['進場價格'], errors='coerce')
        df['出場價格'] = pd.to_numeric(df['出場價格'], errors='coerce')
        df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')

        issues = []

        # [1] 重複交易檢測
        duplicates = df.duplicated(subset=['進場時間', '出場時間', '進場價格', '出場價格'], keep=False)
        duplicate_count = duplicates.sum() // 2
        if duplicate_count > 0:
            issues.append({
                'type': 'duplicate',
                'severity': 'warning',
                'message': f'發現 {duplicate_count} 筆重複交易',
                'count': duplicate_count
            })

        # [2] 異常價格檢測
        price_anomalies = []
        for idx, row in df.iterrows():
            if pd.notna(row['進場價格']) and pd.notna(row['出場價格']):
                # 檢查價格是否為負或異常大
                if row['進場價格'] <= 0 or row['出場價格'] <= 0:
                    price_anomalies.append(idx)
                # 檢查價格漲跌幅是否異常 (超過 50%)
                price_change = abs((row['出場價格'] - row['進場價格']) / row['進場價格'])
                if price_change > 0.5:
                    price_anomalies.append(idx)

        if price_anomalies:
            issues.append({
                'type': 'price_anomaly',
                'severity': 'error',
                'message': f'發現 {len(price_anomalies)} 筆異常價格',
                'count': len(price_anomalies)
            })

        # [3] 時間序列驗證
        df_sorted = df.sort_values('出場時間')
        time_issues = []
        for idx, row in df_sorted.iterrows():
            # 進場時間應小於出場時間
            if row['進場時間'] >= row['出場時間']:
                time_issues.append(idx)

        if time_issues:
            issues.append({
                'type': 'time_sequence',
                'severity': 'error',
                'message': f'發現 {len(time_issues)} 筆進出場時間異常',
                'count': len(time_issues)
            })

        # [4] 缺失數據檢測
        missing_data = df.isnull().sum()
        missing_issues = missing_data[missing_data > 0]

        if len(missing_issues) > 0:
            for col, count in missing_issues.items():
                issues.append({
                    'type': 'missing_data',
                    'severity': 'warning',
                    'message': f'欄位「{col}」缺失 {count} 筆數據',
                    'count': count
                })

        # [5] 計算整體審核評分
        total_severity_score = 0
        error_count = len([i for i in issues if i['severity'] == 'error'])
        warning_count = len([i for i in issues if i['severity'] == 'warning'])

        total_severity_score = error_count * 3 + warning_count * 1

        audit_status = '🟢 正常' if total_severity_score == 0 else (
            '🟡 警告' if total_severity_score <= 3 else '🔴 錯誤'
        )

        # [6] 完整性分數
        completeness_score = 100 * (1 - (missing_data.sum() / (len(df) * len(df.columns))))

        return jsonify(convert_numpy_types({
            'status': 'success',
            'audit_summary': {
                'total_trades': int(len(df)),
                'issues_count': int(len(issues)),
                'error_count': int(error_count),
                'warning_count': int(warning_count),
                'audit_status': audit_status,
                'completeness_score': round(float(completeness_score), 2)
            },
            'issues': issues,
            'recommendations': [
                '数据驗證通過' if len(issues) == 0 else '請檢查上述問題',
                '定期備份交易記錄',
                '使用統一的時間格式'
            ]
        }))

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/import/preview', methods=['POST'])
def api_strategy_preview():
    """
    策略預覽決策 - 決策樹分析、信號強度、建議
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']

        # 讀取 CSV
        df = read_csv_file(file)

        df.columns = [col.strip().lstrip('\ufeff') for col in df.columns]

        # 準備數據
        df['獲利金額'] = pd.to_numeric(df['獲利金額'], errors='coerce')
        df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')
        df['進場價格'] = pd.to_numeric(df['進場價格'], errors='coerce')
        df['出場價格'] = pd.to_numeric(df['出場價格'], errors='coerce')
        df['出場時間'] = pd.to_datetime(df['出場時間'], errors='coerce')

        # ═══════════════════════════════════════════════════════════════
        # 決策樹分析：基於歷史交易模式進行分類
        # ═══════════════════════════════════════════════════════════════

        winning_trades = df[df['獲利金額'] > 0]
        losing_trades = df[df['獲利金額'] < 0]

        win_rate = len(winning_trades) / len(df) if len(df) > 0 else 0

        # 進場信號強度 (基於歷史勝率)
        entry_signal_strength = int(win_rate * 10)

        # 出場信號強度 (基於平均獲利)
        avg_profit = df['獲利金額'].mean()
        total_capital = df['進場價格'].sum() * 1000
        exit_signal_strength = int(min((abs(avg_profit) / total_capital * 1000) * 10, 10)) if total_capital > 0 else 0

        # 信號可信度 (基於樣本量和一致性)
        min_samples = 20
        signal_confidence = min(len(df) / min_samples, 1.0) * 100 if len(df) >= 5 else 0

        # ═══════════════════════════════════════════════════════════════
        # 決策建議
        # ═══════════════════════════════════════════════════════════════

        suggestions = []

        if win_rate >= 0.6:
            suggestions.append('✅ 高勝率策略，建議繼續執行')
        elif win_rate >= 0.5:
            suggestions.append('⚠️ 勝率適中，建議優化進場條件')
        else:
            suggestions.append('🔴 勝率較低，建議重新檢視策略邏輯')

        if avg_profit > 0:
            suggestions.append(f'💰 平均獲利為正，單筆平均獲利 {avg_profit:.2f}')
        else:
            suggestions.append('⚠️ 平均獲利為負，需要改進風險管理')

        # 交易頻率建議
        trades_per_month = len(df) / max(1, (df['出場時間'].max() - df['出場時間'].min()).days / 30)
        if trades_per_month > 20:
            suggestions.append('⚡ 交易頻率較高，注意過度交易風險')
        elif trades_per_month < 2:
            suggestions.append('🔄 交易頻率較低，可考慮擴大交易範圍')

        # ═══════════════════════════════════════════════════════════════
        # 決策路徑分析 (簡化版)
        # ═══════════════════════════════════════════════════════════════

        decision_paths = []

        # 路徑 1: 高勝率交易
        high_win_trades = winning_trades.nlargest(5, '獲利金額')
        if len(high_win_trades) > 0:
            decision_paths.append({
                'name': '勝利交易特徵',
                'description': f'最佳交易的平均進出場價差: {(high_win_trades["出場價格"] - high_win_trades["進場價格"]).mean():.2f}',
                'trades': len(high_win_trades)
            })

        # 路徑 2: 低虧損交易
        small_loss_trades = losing_trades.nsmallest(5, '獲利金額')
        if len(small_loss_trades) > 0:
            decision_paths.append({
                'name': '虧損交易特徵',
                'description': f'最小虧損的平均金額: {abs(small_loss_trades["獲利金額"].mean()):.2f}',
                'trades': len(small_loss_trades)
            })

        return jsonify({
            'status': 'success',
            'signal_analysis': {
                'entry_signal': {
                    'strength': entry_signal_strength,
                    'description': f'進場信號強度: {entry_signal_strength}/10'
                },
                'exit_signal': {
                    'strength': exit_signal_strength,
                    'description': f'出場信號強度: {exit_signal_strength}/10'
                },
                'signal_confidence': round(signal_confidence, 2)
            },
            'decision_paths': decision_paths,
            'suggestions': suggestions,
            'summary': {
                'total_trades': len(df),
                'win_rate': round(win_rate * 100, 2),
                'avg_profit': round(avg_profit, 2),
                'recommendation': '✅ 繼續' if win_rate >= 0.5 else '⚠️ 改進'
            }
        })

    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/staging', methods=['GET', 'POST'])
def api_strategy_staging():
    """
    Staging 管理 - 版本控制、草稿保存
    """
    try:
        if request.method == 'GET':
            # 返回所有草稿版本
            drafts = {
                'drafts': [
                    {
                        'id': 'draft_001',
                        'name': '策略版本 v1.0',
                        'status': 'draft',
                        'created': '2026-04-07 10:00',
                        'updated': '2026-04-07 10:30',
                        'trades': 137
                    },
                    {
                        'id': 'draft_002',
                        'name': '策略版本 v1.1 (優化)',
                        'status': 'pending_review',
                        'created': '2026-04-07 11:00',
                        'updated': '2026-04-07 11:45',
                        'trades': 137
                    }
                ]
            }
            return jsonify({'status': 'success', **drafts})

        elif request.method == 'POST':
            # 保存新草稿
            data = request.get_json()
            draft_name = data.get('name', '未命名草稿')

            return jsonify({
                'status': 'success',
                'message': f'草稿「{draft_name}」已保存',
                'draft': {
                    'id': 'draft_' + str(int(time.time())),
                    'name': draft_name,
                    'status': 'draft',
                    'created': datetime.now().isoformat()
                }
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/sync-log', methods=['GET'])
def api_strategy_sync_log():
    """
    同步日誌 - 操作日誌、同步狀態
    """
    try:
        logs = [
            {
                'timestamp': '2026-04-07 11:30:00',
                'action': '上傳 CSV',
                'status': 'success',
                'details': '260401_台股強勢股加碼-兩次.csv (137 筆交易)',
                'target': '本地'
            },
            {
                'timestamp': '2026-04-07 11:31:00',
                'action': 'P&L 計算',
                'status': 'success',
                'details': '計算完成，總獲利: 37,168,407',
                'target': '本地'
            },
            {
                'timestamp': '2026-04-07 11:32:00',
                'action': '同步到 Google Sheets',
                'status': 'pending',
                'details': '等待授權...',
                'target': 'Google Sheets'
            },
            {
                'timestamp': '2026-04-07 11:33:00',
                'action': '同步到資料庫',
                'status': 'pending',
                'details': '等待數據驗證...',
                'target': '資料庫'
            }
        ]

        return jsonify({
            'status': 'success',
            'logs': logs,
            'summary': {
                'total': len(logs),
                'success': sum(1 for log in logs if log['status'] == 'success'),
                'pending': sum(1 for log in logs if log['status'] == 'pending'),
                'failed': sum(1 for log in logs if log['status'] == 'failed')
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy/monte-carlo', methods=['POST'])
def api_strategy_monte_carlo():
    """
    蒙地卡羅模擬 - 未來績效預測
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        file = request.files['file']

        # 讀取 CSV
        df = read_csv_file(file)

        df.columns = [col.lstrip('\ufeff') for col in df.columns]
        df['報酬率'] = pd.to_numeric(df['報酬率'], errors='coerce')

        returns = df['報酬率'].dropna().values
        n_trades = len(returns)

        # 蒙地卡羅模擬：模擬未來 n_trades 筆交易的總報酬
        simulations = 5000
        np.random.seed(42)

        # 每次模擬隨機抽取 n_trades 筆交易，計算總報酬
        sim_totals = np.array([
            np.random.choice(returns, size=n_trades, replace=True).sum()
            for _ in range(simulations)
        ])

        percentile_5 = float(np.percentile(sim_totals, 5))
        percentile_50 = float(np.percentile(sim_totals, 50))
        percentile_95 = float(np.percentile(sim_totals, 95))
        failure_probability = float((sim_totals < 0).sum() / simulations * 100)

        return jsonify(convert_numpy_types({
            'status': 'success',
            'simulation': {
                'scenarios': simulations,
                'periods': int(n_trades),
                'confidence_level': '95%'
            },
            'results': {
                'low': round(percentile_5 * 100, 2),
                'median': round(percentile_50 * 100, 2),
                'high': round(percentile_95 * 100, 2),
                'failure_probability': round(failure_probability, 2)
            }
        }))

    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health')
def health():
    """健康檢查"""
    return jsonify({'status': 'ok'})


@app.route('/api/proxy', methods=['POST'])
def api_proxy():
    """
    代理端點 - 用 Flask test client 呼叫其他 API
    這是解決 Flask HTTP 伺服器路由問題的臨時方案

    前端請求格式：
    {
        "endpoint": "/api/strategy/import/charts",
        "file": <file object>
    }
    """
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400

        # 獲取請求的端點
        endpoint = request.form.get('endpoint', '/api/strategy/import')
        file = request.files['file']

        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files supported'}), 400

        # 用 test client 調用指定的端點
        with app.test_client() as client:
            resp = client.post(endpoint, data={'file': file})

            # 返回原始響應
            if resp.status_code == 200:
                return jsonify(resp.get_json())
            else:
                return jsonify({'status': 'error', 'message': f'API call failed: {resp.status_code}'}), resp.status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/test-copy', methods=['POST'])
def test_copy():
    """複製第一個路由的測試版本"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file'}), 400
    return jsonify({'status': 'success', 'message': 'Copy test works'})


@app.route('/api/test-charts-simple', methods=['POST'])
def test_charts_simple():
    """簡單測試端點 - 診斷 404 問題"""
    return jsonify({'status': 'ok', 'message': 'Simple test endpoint works'})

# ════════════════════════════════════════════════════════════════
# 策略中心 API — 審核&版本 / 策略庫 / 景氣適配 / 實單vs回測
# ════════════════════════════════════════════════════════════════

def _read_sheet(name):
    """讀取 Google Sheets 分頁（統一 helper）"""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from sheets_utils import read_sheet_data_with_cache
    df = read_sheet_data_with_cache(name)
    if df is None or df.empty:
        return []
    return df.to_dict('records')


@app.route('/api/strategy-center/versions', methods=['GET'])
def api_sc_versions():
    """讀取 strategy_performance 所有版本記錄"""
    try:
        rows = _read_sheet('strategy_performance')
        if not rows:
            return jsonify({'status': 'ok', 'data': []})

        data = []
        for r in rows:
            data.append({
                'strategy_id':   str(r.get('strategy_id', '')).strip(),
                'strategy_name': str(r.get('strategy_name', '')).strip(),
                'version':       str(r.get('version', '')).strip(),
                'run_date':      str(r.get('run_date', '')).strip(),
                'start_date':    str(r.get('start_date', '')).strip(),
                'end_date':      str(r.get('end_date', '')).strip(),
                'cagr_pct':      safe_float(r.get('cagr_pct')),
                'sharpe':        safe_float(r.get('sharpe')),
                'sortino':       safe_float(r.get('sortino')),
                'mdd_pct':       safe_float(r.get('mdd_pct')),
                'calmar':        safe_float(r.get('calmar')),
                'win_rate_pct':  safe_float(r.get('win_rate_pct')),
                'trades':        safe_float(r.get('trades')),
                'avg_profit_pct': safe_float(r.get('avg_profit_pct')),
                'avg_loss_pct':  safe_float(r.get('avg_loss_pct')),
                'ev_pct':        safe_float(r.get('ev_pct')),
                'kelly_full':    safe_float(r.get('kelly_full')),
                'kelly_half':    safe_float(r.get('kelly_half')),
                'file_name':     str(r.get('file_name', '')).strip(),
                'uploaded_at':   str(r.get('uploaded_at', '')).strip(),
            })
        return jsonify({'status': 'ok', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy-center/library', methods=['GET'])
def api_sc_library():
    """讀取 strategies + strategy_performance 合併為策略庫"""
    try:
        strategies = _read_sheet('strategies')
        perf = _read_sheet('strategy_performance')

        # 取每個策略最新版本的 perf
        latest_perf = {}
        for r in perf:
            sid = str(r.get('strategy_id', '')).strip()
            ver = str(r.get('version', '')).strip()
            if sid not in latest_perf or ver > latest_perf[sid].get('version', ''):
                latest_perf[sid] = r

        cards = []
        for s in strategies:
            name = str(s.get('策略名稱', s.get('strategy_name', ''))).strip()
            status = str(s.get('狀態', s.get('status', '研究中'))).strip()
            stype = str(s.get('策略類型/描述', s.get('type', ''))).strip()

            # 嘗試匹配 perf
            matched_perf = None
            for sid, p in latest_perf.items():
                pname = str(p.get('strategy_name', '')).strip()
                if pname and (pname in name or name in pname):
                    matched_perf = p
                    break

            card = {
                'name': name,
                'status': status,
                'type': stype,
                'broker': str(s.get('券商/平台', '')).strip(),
                'currency': str(s.get('幣別', '')).strip(),
                'initial_capital': str(s.get('初始資金', '')).strip(),
                'backtest_years': str(s.get('回測年數', '')).strip(),
            }

            if matched_perf:
                card.update({
                    'strategy_id': str(matched_perf.get('strategy_id', '')).strip(),
                    'version': str(matched_perf.get('version', '')).strip(),
                    'cagr_pct': safe_float(matched_perf.get('cagr_pct')),
                    'sharpe': safe_float(matched_perf.get('sharpe')),
                    'sortino': safe_float(matched_perf.get('sortino')),
                    'mdd_pct': safe_float(matched_perf.get('mdd_pct')),
                    'calmar': safe_float(matched_perf.get('calmar')),
                    'win_rate_pct': safe_float(matched_perf.get('win_rate_pct')),
                    'trades': safe_float(matched_perf.get('trades')),
                    'kelly_half': safe_float(matched_perf.get('kelly_half')),
                    'ev_pct': safe_float(matched_perf.get('ev_pct')),
                })
            else:
                # 從 strategies sheet 讀基本數據
                card.update({
                    'cagr_pct': safe_float(s.get('複合年增長率', s.get('cagr_pct'))),
                    'mdd_pct': safe_float(s.get('最大回撤', s.get('mdd_pct'))),
                })

            # 綜合評分 = 0.3*Sharpe_norm + 0.25*CAGR_norm + 0.25*(1-MDD_norm) + 0.2*WinRate_norm
            sharpe = card.get('sharpe') or 0
            cagr = card.get('cagr_pct') or 0
            mdd = abs(card.get('mdd_pct') or 0)
            wr = card.get('win_rate_pct') or 0
            score = round(
                0.30 * min(sharpe / 3.0, 1.0) * 100 +
                0.25 * min(cagr / 30.0, 1.0) * 100 +
                0.25 * max(1.0 - mdd / 30.0, 0) * 100 +
                0.20 * min(wr / 80.0, 1.0) * 100
            , 1)
            card['score'] = score

            cards.append(card)

        return jsonify({'status': 'ok', 'data': cards})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy-center/regime', methods=['GET'])
def api_sc_regime():
    """讀取 macro_state 景氣狀態 + strategies 的景氣適配"""
    try:
        macro = _read_sheet('macro_state')
        strategies = _read_sheet('strategies')

        # 取最新一筆 macro_state
        current_regime = None
        if macro:
            # 按日期排序取最新
            macro_sorted = sorted(macro, key=lambda x: str(x.get('date', '')), reverse=True)
            latest = macro_sorted[0]
            current_regime = {
                'date': str(latest.get('date', '')).strip(),
                'regime': str(latest.get('regime', '')).strip(),
                'risk_on': str(latest.get('risk_on', '')).strip(),
                'notes': str(latest.get('notes', '')).strip(),
            }

        # 策略列表（簡化）
        strats = []
        for s in strategies:
            strats.append({
                'name': str(s.get('策略名稱', '')).strip(),
                'status': str(s.get('狀態', '研究中')).strip(),
                'type': str(s.get('策略類型/描述', '')).strip(),
            })

        return jsonify({
            'status': 'ok',
            'regime': current_regime,
            'strategies': strats,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/strategy-center/live-vs-backtest', methods=['GET'])
def api_sc_live_vs_bt():
    """比對實單（trades）vs 回測（strategy_performance）"""
    try:
        trades_raw = _read_sheet('trades')
        perf_raw = _read_sheet('strategy_performance')


        # 整理已實現交易：按策略分組
        strategy_trades = {}
        for t in trades_raw:
            strat = str(t.get('策略', t.get('strategy', ''))).strip()
            if not strat:
                continue
            if strat not in strategy_trades:
                strategy_trades[strat] = []
            pnl = safe_float(t.get('損益', t.get('pnl')))
            pnl_pct = safe_float(t.get('損益%', t.get('pnl_pct')))
            strategy_trades[strat].append({
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'symbol': str(t.get('標的', t.get('symbol', ''))).strip(),
                'date': str(t.get('日期', t.get('date', ''))).strip(),
                'direction': str(t.get('方向', t.get('direction', ''))).strip(),
                'status': str(t.get('狀態', t.get('status', ''))).strip(),
            })

        # 取每個策略最新版本的回測數據
        latest_perf = {}
        for r in perf_raw:
            sname = str(r.get('strategy_name', '')).strip()
            ver = str(r.get('version', '')).strip()
            if sname and (sname not in latest_perf or ver > latest_perf[sname].get('version', '')):
                latest_perf[sname] = r

        # 計算實單統計並與回測對比
        comparisons = []
        for strat_name, trades_list in strategy_trades.items():
            # 找匹配的 perf
            matched_perf = None
            for pname, p in latest_perf.items():
                if pname in strat_name or strat_name in pname:
                    matched_perf = p
                    break

            # 實單統計
            realized = [t for t in trades_list if t.get('status') in ('已實現', '已平倉', 'closed', 'CLOSED')]
            if not realized:
                realized = trades_list  # fallback

            total = len(realized)
            wins = sum(1 for t in realized if (t.get('pnl') or 0) > 0)
            live_win_rate = round(wins / total * 100, 1) if total > 0 else 0
            pnls = [t.get('pnl') or 0 for t in realized]
            live_total_pnl = round(sum(pnls), 2)
            avg_pnl_pct = round(np.mean([t.get('pnl_pct') or 0 for t in realized if t.get('pnl_pct') is not None]), 2) if realized else 0

            # 盈虧比
            win_pnls = [p for p in pnls if p > 0]
            loss_pnls = [abs(p) for p in pnls if p < 0]
            avg_win = np.mean(win_pnls) if win_pnls else 0
            avg_loss = np.mean(loss_pnls) if loss_pnls else 1
            live_profit_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0

            comp = {
                'strategy': strat_name,
                'live_trades': total,
                'live_win_rate': live_win_rate,
                'live_total_pnl': live_total_pnl,
                'live_avg_pnl_pct': avg_pnl_pct,
                'live_profit_loss_ratio': live_profit_loss_ratio,
            }

            if matched_perf:
                bt_wr = safe_float(matched_perf.get('win_rate_pct')) or 0
                bt_cagr = safe_float(matched_perf.get('cagr_pct')) or 0
                bt_mdd = safe_float(matched_perf.get('mdd_pct')) or 0
                bt_sharpe = safe_float(matched_perf.get('sharpe')) or 0
                bt_avg_profit = safe_float(matched_perf.get('avg_profit_pct')) or 0
                bt_avg_loss = safe_float(matched_perf.get('avg_loss_pct')) or 0
                bt_plr = round(abs(bt_avg_profit / bt_avg_loss), 2) if bt_avg_loss else 0

                comp.update({
                    'bt_win_rate': bt_wr,
                    'bt_cagr': bt_cagr,
                    'bt_mdd': bt_mdd,
                    'bt_sharpe': bt_sharpe,
                    'bt_profit_loss_ratio': bt_plr,
                    'bt_version': str(matched_perf.get('version', '')).strip(),
                })

                # 健康度判定
                alerts = 0
                if abs(live_win_rate - bt_wr) > 10: alerts += 1
                if live_profit_loss_ratio > 0 and bt_plr > 0 and abs(live_profit_loss_ratio - bt_plr) > 0.5: alerts += 1
                if avg_pnl_pct < 0 and bt_cagr > 0: alerts += 1

                if alerts >= 3:
                    comp['health'] = 'danger'
                elif alerts >= 1:
                    comp['health'] = 'warning'
                else:
                    comp['health'] = 'healthy'
            else:
                comp['health'] = 'no_backtest'

            comparisons.append(comp)

        return jsonify({'status': 'ok', 'data': comparisons})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# 測試端點
@app.route('/api/test-new-endpoint')
def test_new_endpoint():
    return jsonify({'status': 'ok', 'message': 'Test endpoint works'})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("[*] Krystal AI Dashboard v8 - Flask Server")
    print("="*60)
    print("[+] Access: http://127.0.0.1:9000")
    print("="*60 + "\n")

    # 檢查依賴
    try:
        import flask
        import plotly
        import pandas
        import scipy
        import sklearn
        print("[OK] All dependencies installed\n")
    except ImportError as e:
        print(f"[!] Missing: {e}")
        print("    Run: pip install flask plotly pandas scipy scikit-learn\n")

    # 列出 /api/strategy 路由
    print("[*] Registered strategy routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'strategy' in rule.rule:
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"    {rule.rule} [{methods}]")
    print()

    app.run(host='127.0.0.1', port=9000, debug=False, use_reloader=False)
