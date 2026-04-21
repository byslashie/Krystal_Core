"""
Strategy Sync API - 方案 C 核心後端
用於上傳、分析、決策、同步策略
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials

# 導入 MD 生成器
sys.path.insert(0, str(Path(__file__).parent))
from md_template_generator import generate_home_md

# ===== 配置 =====
app = Flask(__name__)
CORS(app)

STRATEGIES_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Strategies')
STAGING_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging')
UPLOADS_PATH = STAGING_PATH / 'uploads'
DRAFTS_PATH = STAGING_PATH / 'drafts'

# 建立資料夾
UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
DRAFTS_PATH.mkdir(parents=True, exist_ok=True)

# Google Sheets 配置
CREDS_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\credentials.json')
SHEETS_ID = '1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8'  # 用戶的 Sheets ID

# ===== Google Sheets 初始化 =====
def get_sheets_client():
    """連接 Google Sheets"""
    if not CREDS_PATH.exists():
        raise FileNotFoundError(f'找不到 credentials.json: {CREDS_PATH}')

    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    return gspread.authorize(creds)

# ===== KPI 計算函數 =====
class KPICalculator:
    """計算策略績效指標"""

    @staticmethod
    def calculate_kpis(df: pd.DataFrame, initial_capital: float = 100000) -> Dict[str, float]:
        """
        從回測 DataFrame 計算 KPI

        預期列名:
        - Date / date / 日期
        - Close / 淨值 / equity
        - PnL / profit / 損益
        """

        # 規範列名
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()

        # 找到淨值列
        equity_col = None
        for col in ['close', '淨值', 'equity', 'nav']:
            if col in df.columns:
                equity_col = col
                break

        if equity_col is None:
            raise ValueError(f'未找到淨值列，可用列: {df.columns.tolist()}')

        # 轉換為數值
        equity = pd.to_numeric(df[equity_col], errors='coerce').dropna()

        if len(equity) < 2:
            raise ValueError('數據不足，無法計算 KPI')

        # 計算報酬率
        returns = equity.pct_change().dropna()

        # CAGR (年化報酬)
        days = len(equity)
        years = days / 252  # 交易日數
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        cagr = (1 + total_return) ** (1 / years) - 1

        # Sharpe Ratio (夏普比率)
        daily_ret_mean = returns.mean()
        daily_ret_std = returns.std()
        sharpe = (daily_ret_mean / daily_ret_std) * np.sqrt(252) if daily_ret_std > 0 else 0

        # MDD (最大回檔)
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        mdd = drawdown.min()

        # 勝率
        if 'pnl' in df.columns or '損益' in df.columns:
            pnl_col = 'pnl' if 'pnl' in df.columns else '損益'
            win_count = (df[pnl_col] > 0).sum()
            total_trades = len(df[df[pnl_col] != 0])
            win_rate = win_count / total_trades if total_trades > 0 else 0

            # 獲利因子
            total_profit = df[df[pnl_col] > 0][pnl_col].sum()
            total_loss = abs(df[df[pnl_col] < 0][pnl_col].sum())
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
        else:
            win_rate = 0
            profit_factor = 0
            total_trades = len(equity) - 1

        return {
            'cagr': cagr,
            'sharpe': sharpe,
            'mdd': mdd,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'total_trades': int(total_trades)
        }

    @staticmethod
    def get_equity_curve(df: pd.DataFrame) -> Dict[str, List]:
        """提取淨值曲線"""
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()

        # 找日期列
        date_col = None
        for col in ['date', '日期', 'datetime']:
            if col in df.columns:
                date_col = col
                break

        # 找淨值列
        equity_col = None
        for col in ['close', '淨值', 'equity', 'nav']:
            if col in df.columns:
                equity_col = col
                break

        if equity_col is None:
            return {'dates': [], 'values': []}

        dates = df[date_col].astype(str).tolist() if date_col else [str(i) for i in range(len(df))]
        values = pd.to_numeric(df[equity_col], errors='coerce').tolist()

        return {'dates': dates[:100], 'values': values[:100]}  # 只返回最近 100 筆


# ===== API 端點 =====

@app.route('/api/strategy/analyze', methods=['POST'])
def analyze_strategy():
    """
    上傳 CSV 並分析 KPI

    POST /api/strategy/analyze
    {
        "strategy_name": "Wave Strategy",
        "initial_capital": 100000,
        "python_version": "1.0.0",
        "note": "...",
        "csv_data": [[...], ...],
        "csv_headers": [...]
    }
    """
    try:
        data = request.json

        strategy_name = data.get('strategy_name', 'Unknown').strip()
        initial_capital = float(data.get('initial_capital', 100000))
        python_version = data.get('python_version', '1.0.0')
        note = data.get('note', '')

        # 重建 DataFrame
        csv_data = data.get('csv_data', [])
        csv_headers = data.get('csv_headers', [])

        if not csv_data or not csv_headers:
            return jsonify({'status': 'error', 'message': '無效的 CSV 數據'}), 400

        df = pd.DataFrame(csv_data, columns=csv_headers)

        # 計算 KPI
        kpis = KPICalculator.calculate_kpis(df, initial_capital)
        equity_curve = KPICalculator.get_equity_curve(df)

        # 找下一個 S 號
        existing_folders = [d.name for d in STRATEGIES_PATH.iterdir() if d.is_dir() and d.name.startswith('S')]
        next_num = max([int(d.split('-')[0][1:]) for d in existing_folders], default=0) + 1

        # 生成分析 ID
        analysis_id = f'T{next_num:03d}'

        # 保存分析結果到臨時文件
        analysis_meta = {
            'analysis_id': analysis_id,
            'strategy_name': strategy_name,
            'next_folder_id': next_num,
            'initial_capital': initial_capital,
            'python_version': python_version,
            'note': note,
            'kpis': kpis,
            'equity_curve': equity_curve,
            'timestamp': datetime.now().isoformat()
        }

        # 保存 meta 到臨時檔案
        meta_path = UPLOADS_PATH / f'{analysis_id}_meta.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_meta, f, ensure_ascii=False, indent=2, default=str)

        return jsonify({
            'status': 'success',
            'analysis_id': analysis_id,
            'strategy_name': strategy_name,
            'next_folder_id': next_num,
            'kpis': kpis,
            'equity_curve': equity_curve,
            'csv_data': csv_data
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'分析失敗: {str(e)}'
        }), 500


@app.route('/api/strategy/confirm-preview', methods=['POST'])
def confirm_preview():
    """
    確認預覽，創建 Staging 資料夾

    POST /api/strategy/confirm-preview
    {
        "analysis_id": "T001",
        "strategy_name": "Wave Strategy",
        "kpis": {...},
        "csv_data": [...]
    }
    """
    try:
        data = request.json

        analysis_id = data.get('analysis_id')
        strategy_name = data.get('strategy_name', 'Unknown').strip()
        kpis = data.get('kpis', {})
        csv_data = data.get('csv_data', [])
        initial_capital = data.get('initial_capital', 100000)

        # 嘗試從 meta 文件讀取（如果有 analysis_id）
        meta = None
        next_num = None

        if analysis_id:
            meta_path = UPLOADS_PATH / f'{analysis_id}_meta.json'
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                next_num = meta.get('next_folder_id')

        # Fallback：如果沒有 meta 文件，直接用請求的 kpis
        if not meta:
            # 自動生成下一個資料夾 ID（找現存最大的 S 編號）
            import re
            from pathlib import Path
            drafts_dir = Path(DRAFTS_PATH)
            if drafts_dir.exists():
                existing_folders = [d.name for d in drafts_dir.iterdir() if d.is_dir() and d.name.startswith('S')]
                if existing_folders:
                    nums = []
                    for f in existing_folders:
                        m = re.match(r'S(\d+)', f)
                        if m:
                            nums.append(int(m.group(1)))
                    next_num = max(nums) + 1 if nums else 1
                else:
                    next_num = 1
            else:
                next_num = 1

            meta = {
                'kpis': kpis,
                'next_folder_id': next_num,
                'initial_capital': initial_capital,
                'note': ''
            }

        # 創建 Staging 資料夾結構
        staging_folder = DRAFTS_PATH / f'S{next_num}-{strategy_name}'
        staging_folder.mkdir(parents=True, exist_ok=True)

        # 準備完整的 meta 用於 MD 生成
        meta_for_md = {
            'run_date': data.get('run_date', datetime.now().strftime('%Y-%m-%d')),
            'start_date': data.get('start_date', '2008-06-02'),
            'end_date': data.get('end_date', datetime.now().strftime('%Y-%m-%d')),
            'initial_capital': initial_capital
        }

        # 用 MD 生成器生成完整的 Home.md
        home_md = generate_home_md(strategy_name, kpis, meta_for_md)

        home_path = staging_folder / f'S{next_num}-{strategy_name}-Home.md'
        home_path.write_text(home_md, encoding='utf-8')

        # 創建 Versions 資料夾
        versions_folder = staging_folder / 'Versions'
        versions_folder.mkdir(exist_ok=True)

        version_md = f"""---
name: {strategy_name}
version: v1.0
version_seq: 1
type: module_version
created_date: {datetime.now().strftime('%Y-%m-%d')}
cagr: {meta['kpis']['cagr']}
sharpe: {meta['kpis']['sharpe']}
mdd: {meta['kpis']['mdd']}
win_rate: {meta['kpis']['win_rate']}
profit_factor: {meta['kpis']['profit_factor']}
---

# {strategy_name} - v1.0

## 版本信息
- 版本號：v1.0
- 發佈日期：{datetime.now().strftime('%Y-%m-%d')}
- 狀態：Staging（待審批）

## KPI
{json.dumps(meta['kpis'], indent=2)}
"""

        version_path = versions_folder / f'S{next_num}-{strategy_name}-v1.0.md'
        version_path.write_text(version_md, encoding='utf-8')

        # 創建 Backtests 資料夾
        backtests_folder = staging_folder / 'Backtests' / 'baseline'
        backtests_folder.mkdir(parents=True, exist_ok=True)

        # 保存 CSV 到 Backtests
        csv_path = backtests_folder / f'{strategy_name}_backtest.csv'
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')

        # 創建 Knowledge 資料夾
        knowledge_folder = staging_folder / 'Knowledge'
        knowledge_folder.mkdir(exist_ok=True)

        # 記錄到同步日誌
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'confirm',
            'strategy_id': analysis_id,
            'strategy_name': strategy_name,
            'folder_id': f'S{next_num}',
            'status': 'success',
            'message': f'已確認預覽，創建 Staging 資料夾'
        }

        append_sync_log(log_entry)

        return jsonify({
            'success': True,
            'status': 'success',
            'folder_id': f'S{next_num}',
            'folder_path': str(staging_folder),
            'meta': meta
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'確認預覽失敗: {str(e)}'
        }), 500


@app.route('/api/sync/status', methods=['GET'])
def get_sync_status():
    """獲取系統同步狀態"""
    try:
        # 獲取 Staging 策略數
        staging_count = len([d for d in DRAFTS_PATH.iterdir() if d.is_dir()])

        # 獲取 Git 狀態
        git_branch = 'main'
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=str(STRATEGIES_PATH.parent),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_branch = result.stdout.strip()
        except:
            pass

        # 獲取 Google Sheets 待審策略數
        backtest_pending = 0
        try:
            client = get_sheets_client()
            sheet = client.open_by_key(SHEETS_ID)
            # 假設第一個 sheet 是 BacktestPool
            ws = sheet.get_worksheet(0)
            rows = ws.get_all_records()
            backtest_pending = len([r for r in rows if '待審' in str(r.get('狀態', ''))])
        except:
            pass

        return jsonify({
            'status': 'ok',
            'sheets_last_sync': datetime.now().isoformat(),
            'local_last_sync': datetime.now().isoformat(),
            'git_last_sync': datetime.now().isoformat(),
            'staging_draft_count': staging_count,
            'backtest_pending_count': backtest_pending,
            'git_branch': git_branch
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/staging/list', methods=['GET'])
def list_staging():
    """列出所有 Staging 草稿策略"""
    try:
        strategies = []

        for folder in DRAFTS_PATH.iterdir():
            if not folder.is_dir():
                continue

            # 讀取 Home.md
            home_files = list(folder.glob('*-Home.md'))
            if not home_files:
                continue

            home_path = home_files[0]
            content = home_path.read_text(encoding='utf-8')

            # 解析 YAML 前置
            import re
            match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)
            if match:
                yaml_content = match.group(1)
                # 簡單解析
                cagr = float(re.search(r'cagr:\s*([\d.-]+)', yaml_content).group(1) or 0) if re.search(r'cagr:', yaml_content) else 0
                sharpe = float(re.search(r'sharpe:\s*([\d.-]+)', yaml_content).group(1) or 0) if re.search(r'sharpe:', yaml_content) else 0
                win_rate = float(re.search(r'win_rate:\s*([\d.-]+)', yaml_content).group(1) or 0) if re.search(r'win_rate:', yaml_content) else 0

                strategies.append({
                    'id': folder.name,
                    'name': folder.name.split('-', 1)[1] if '-' in folder.name else folder.name,
                    'kpis': {
                        'cagr': cagr / 100,
                        'sharpe': sharpe,
                        'win_rate': win_rate / 100
                    },
                    'path': str(folder)
                })

        return jsonify({'status': 'success', 'strategies': strategies})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/sync/log', methods=['GET'])
def get_sync_log():
    """獲取同步日誌"""
    try:
        limit = request.args.get('limit', 20, type=int)

        log_path = STAGING_PATH / 'sync.log'
        if not log_path.exists():
            return jsonify({'status': 'success', 'logs': []})

        logs = []
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f.readlines()[-limit:]:
                try:
                    logs.append(json.loads(line))
                except:
                    pass

        return jsonify({'status': 'success', 'logs': logs[::-1]})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===== 輔助函數 =====

def append_sync_log(entry: Dict[str, Any]):
    """添加同步日誌"""
    log_path = STAGING_PATH / 'sync.log'
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + '\n')


# ===== 主程序 =====
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
