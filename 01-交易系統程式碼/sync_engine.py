"""
Sync Engine - 三向同步引擎
監聽 Google Sheets → 本地 → Git 的自動同步
"""

import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from threading import Thread
import logging

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.background import BackgroundScheduler

# ===== 日誌設置 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging\sync_engine.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ===== 配置 =====
STRATEGIES_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Strategies')
STAGING_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\02-策略知識庫\Staging')
DRAFTS_PATH = STAGING_PATH / 'drafts'
SYNC_LOG_PATH = STAGING_PATH / 'sync.log'

CREDS_PATH = Path(r'G:\我的雲端硬碟\Krystal_完整系統\01-交易系統程式碼\credentials.json')
SHEETS_ID = '1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8'  # 用戶的 Sheets ID

# ===== Google Sheets API =====
class SheetsAPI:
    """Google Sheets 操作類"""

    def __init__(self):
        self.client = None
        self.workbook = None

    def connect(self):
        """連接 Google Sheets"""
        if not CREDS_PATH.exists():
            raise FileNotFoundError(f'找不到 credentials.json: {CREDS_PATH}')

        creds = Credentials.from_service_account_file(
            CREDS_PATH,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        self.client = gspread.authorize(creds)
        self.workbook = self.client.open_by_key(SHEETS_ID)
        logger.info('✓ Google Sheets 連接成功')

    def get_backtest_pool(self):
        """獲取回測候選池"""
        try:
            # 假設第一個 sheet 是 BacktestPool
            ws = self.workbook.get_worksheet(0)
            rows = ws.get_all_records()
            return rows
        except Exception as e:
            logger.error(f'✗ 獲取 BacktestPool 失敗: {e}')
            return []

    def update_backtest_pool(self, row_index: int, updates: Dict[str, Any]):
        """更新 BacktestPool 中的一行"""
        try:
            ws = self.workbook.get_worksheet(0)
            # 更新指定行
            # gspread 的行編號從 2 開始（跳過標頭）
            for col_name, value in updates.items():
                ws.update([[value]], f'{col_name}{row_index + 2}')
            logger.info(f'✓ 已更新 BacktestPool 第 {row_index} 行')
        except Exception as e:
            logger.error(f'✗ 更新 BacktestPool 失敗: {e}')

    def append_to_live_strategies(self, strategy_data: Dict[str, Any]):
        """添加策略到 LiveStrategies 表"""
        try:
            # 假設第二個 sheet 是 LiveStrategies
            ws = self.workbook.get_worksheet(1)
            row = [
                strategy_data.get('folder_id'),
                strategy_data.get('strategy_name'),
                strategy_data.get('version'),
                strategy_data.get('upload_date'),
                strategy_data.get('cagr'),
                strategy_data.get('sharpe'),
                strategy_data.get('mdd'),
                strategy_data.get('win_rate'),
                strategy_data.get('trades'),
                '',  # 實盤月報酬
                '',  # 實盤年報酬
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                '',  # 回測文件
                '',  # Home 頁面
                '✅ 運行中'
            ]
            ws.append_row(row)
            logger.info(f'✓ 已添加 {strategy_data["strategy_name"]} 到 LiveStrategies')
        except Exception as e:
            logger.error(f'✗ 添加到 LiveStrategies 失敗: {e}')

    def append_to_version_history(self, version_data: Dict[str, Any]):
        """添加版本記錄到 VersionHistory"""
        try:
            # 假設第三個 sheet 是 VersionHistory
            ws = self.workbook.get_worksheet(2)
            row = [
                version_data.get('folder_id'),
                version_data.get('version'),
                version_data.get('release_date'),
                version_data.get('cagr'),
                version_data.get('sharpe'),
                version_data.get('mdd'),
                version_data.get('win_rate'),
                version_data.get('changes'),
                version_data.get('decision_maker'),
                version_data.get('git_commit'),
                version_data.get('notes')
            ]
            ws.append_row(row)
            logger.info(f'✓ 已添加版本記錄: {version_data["folder_id"]} {version_data["version"]}')
        except Exception as e:
            logger.error(f'✗ 添加版本記錄失敗: {e}')

    def append_to_sync_log(self, log_entry: Dict[str, Any]):
        """添加同步日誌到 SyncLog 表"""
        try:
            # 假設第四個 sheet 是 SyncLog
            ws = self.workbook.get_worksheet(3)
            row = [
                log_entry.get('timestamp'),
                log_entry.get('event_type'),
                log_entry.get('strategy_id'),
                log_entry.get('strategy_name'),
                log_entry.get('status'),
                log_entry.get('message')
            ]
            ws.append_row(row)
            logger.info(f'✓ 已記錄同步日誌: {log_entry["event_type"]}')
        except Exception as e:
            logger.error(f'✗ 記錄同步日誌失敗: {e}')


# ===== 本地文件操作 =====
class LocalStorage:
    """本地檔案系統操作"""

    @staticmethod
    def move_from_staging_to_strategies(staging_folder: Path) -> bool:
        """從 Staging 移動資料夾到 Strategies"""
        try:
            # 獲取資料夾 ID（例如 S7）
            folder_id = staging_folder.name.split('-')[0]
            target_folder = STRATEGIES_PATH / staging_folder.name

            # 檢查是否已存在
            if target_folder.exists():
                logger.warning(f'⚠️ 目標資料夾已存在: {target_folder}')
                return False

            # 複製資料夾結構
            import shutil
            shutil.copytree(staging_folder, target_folder)
            logger.info(f'✓ 已將 {staging_folder.name} 移動到 Strategies')

            return True

        except Exception as e:
            logger.error(f'✗ 移動資料夾失敗: {e}')
            return False

    @staticmethod
    def update_registry_md():
        """更新 Registry策略總表.md（基於本地 Strategies 資料夾）"""
        try:
            # 掃描 Strategies 資料夾
            strategies = []
            for folder in STRATEGIES_PATH.iterdir():
                if not folder.is_dir() or not folder.name.startswith('S'):
                    continue

                # 讀取 Home.md
                home_files = list(folder.glob('*-Home.md'))
                if not home_files:
                    continue

                home_path = home_files[0]
                content = home_path.read_text(encoding='utf-8')

                # 簡單解析 KPI
                import re
                cagr_match = re.search(r'cagr:\s*([\d.-]+)%', content)
                sharpe_match = re.search(r'sharpe:\s*([\d.-]+)', content)
                mdd_match = re.search(r'mdd:\s*([\d.-]+)%', content)

                strategies.append({
                    'id': folder.name,
                    'name': folder.name.split('-', 1)[1] if '-' in folder.name else folder.name,
                    'cagr': float(cagr_match.group(1)) if cagr_match else 0,
                    'sharpe': float(sharpe_match.group(1)) if sharpe_match else 0,
                    'mdd': float(mdd_match.group(1)) if mdd_match else 0,
                })

            logger.info(f'✓ 掃描完成，找到 {len(strategies)} 個策略')

        except Exception as e:
            logger.error(f'✗ 更新 Registry 失敗: {e}')


# ===== Git 操作 =====
class GitManager:
    """Git 版本控制操作"""

    @staticmethod
    def commit_changes(message: str) -> bool:
        """提交變更到 Git"""
        try:
            # 添加所有變更
            subprocess.run(
                ['git', 'add', '.'],
                cwd=str(STRATEGIES_PATH.parent),
                check=True,
                capture_output=True
            )

            # 提交
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=str(STRATEGIES_PATH.parent),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f'✓ Git 提交成功: {message}')
                return True
            else:
                logger.warning(f'⚠️ 無新變更需要提交')
                return True

        except subprocess.CalledProcessError as e:
            logger.error(f'✗ Git 提交失敗: {e}')
            return False

    @staticmethod
    def push_to_remote() -> bool:
        """推送到遠程倉庫"""
        try:
            subprocess.run(
                ['git', 'push'],
                cwd=str(STRATEGIES_PATH.parent),
                check=True,
                capture_output=True
            )
            logger.info('✓ 已推送到遠程倉庫')
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f'✗ 推送到遠程失敗: {e}')
            return False

    @staticmethod
    def get_commit_hash() -> str:
        """獲取當前 commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=str(STRATEGIES_PATH.parent),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return 'unknown'


# ===== 同步引擎核心 =====
class SyncEngine:
    """三向同步引擎"""

    def __init__(self):
        self.sheets_api = SheetsAPI()
        self.processed_strategies = set()  # 追蹤已處理的策略，防止重複

    def start(self):
        """啟動同步引擎"""
        logger.info('🚀 同步引擎啟動...')

        try:
            self.sheets_api.connect()
        except Exception as e:
            logger.error(f'無法連接 Google Sheets: {e}')
            logger.info('⚠️ 將以離線模式運行（只同步本地和 Git）')

        # 啟動定時任務
        scheduler = BackgroundScheduler()

        # 每 5 分鐘檢查一次 Sheets
        scheduler.add_job(self.sync_sheets_to_local, 'interval', minutes=5, id='sheets_sync')

        # 每 10 分鐘更新一次本地 Registry
        scheduler.add_job(LocalStorage.update_registry_md, 'interval', minutes=10, id='registry_update')

        # 每天晚上 23:00 執行完整同步
        scheduler.add_job(self.full_sync, 'cron', hour=23, minute=0, id='full_sync')

        scheduler.start()

        logger.info('✓ 定時任務已啟動')
        logger.info('  - Sheets → 本地：每 5 分鐘')
        logger.info('  - Registry 更新：每 10 分鐘')
        logger.info('  - 完整同步：每天 23:00')

    def sync_sheets_to_local(self):
        """監聽 Google Sheets，自動導入批准的策略"""
        logger.info('🔄 開始 Sheets → 本地 同步...')

        try:
            if not self.sheets_api.workbook:
                logger.warning('⚠️ Google Sheets 未連接，跳過此同步')
                return

            # 獲取回測候選池
            rows = self.sheets_api.get_backtest_pool()

            for idx, row in enumerate(rows):
                # 檢查狀態是否為「已批准」
                status = row.get('狀態', '').strip()
                strategy_name = row.get('策略名稱', '').strip()
                strategy_id = row.get('ID', '').strip()

                if '已批准' not in status or not strategy_name:
                    continue

                # 避免重複處理
                if strategy_id in self.processed_strategies:
                    continue

                logger.info(f'📥 發現已批准策略: {strategy_name} ({strategy_id})')

                # 查找對應的 Staging 資料夾
                staging_folders = list(DRAFTS_PATH.glob(f'*-{strategy_name}'))
                if not staging_folders:
                    logger.warning(f'⚠️ 未找到 Staging 資料夾: {strategy_name}')
                    continue

                staging_folder = staging_folders[0]

                # 移動到 Strategies
                if LocalStorage.move_from_staging_to_strategies(staging_folder):
                    # 獲取資料夾 ID
                    folder_id = staging_folder.name.split('-')[0]

                    # 讀取 KPI 信息
                    home_files = list(staging_folder.glob('*-Home.md'))
                    if home_files:
                        content = home_files[0].read_text(encoding='utf-8')
                        import re
                        cagr = re.search(r'cagr:\s*([\d.-]+)%', content)
                        sharpe = re.search(r'sharpe:\s*([\d.-]+)', content)
                        mdd = re.search(r'mdd:\s*([\d.-]+)%', content)
                        win_rate = re.search(r'win_rate:\s*([\d.-]+)%', content)

                        # 更新 Google Sheets - LiveStrategies
                        self.sheets_api.append_to_live_strategies({
                            'folder_id': folder_id,
                            'strategy_name': strategy_name,
                            'version': 'v1.0',
                            'upload_date': datetime.now().strftime('%Y-%m-%d'),
                            'cagr': float(cagr.group(1)) if cagr else 0,
                            'sharpe': float(sharpe.group(1)) if sharpe else 0,
                            'mdd': float(mdd.group(1)) if mdd else 0,
                            'win_rate': float(win_rate.group(1)) if win_rate else 0,
                            'trades': 0
                        })

                    # Git 提交
                    commit_msg = f'📊 新策略導入: {folder_id}-{strategy_name}'
                    GitManager.commit_changes(commit_msg)
                    commit_hash = GitManager.get_commit_hash()

                    # 記錄到 Sheets - SyncLog
                    self.sheets_api.append_to_sync_log({
                        'timestamp': datetime.now().isoformat(),
                        'event_type': 'approved_and_imported',
                        'strategy_id': strategy_id,
                        'strategy_name': strategy_name,
                        'status': 'success',
                        'message': f'已導入到 Strategies，Git: {commit_hash}'
                    })

                    # 記錄到本地同步日誌
                    self._log_sync_event({
                        'timestamp': datetime.now().isoformat(),
                        'event_type': 'approved_and_imported',
                        'strategy_id': strategy_id,
                        'strategy_name': strategy_name,
                        'folder_id': folder_id,
                        'status': 'success',
                        'message': f'已導入到 Strategies'
                    })

                    self.processed_strategies.add(strategy_id)

        except Exception as e:
            logger.error(f'✗ Sheets → 本地 同步出錯: {e}')

        logger.info('✓ Sheets → 本地 同步完成\n')

    def sync_local_to_sheets(self):
        """定期將本地 Registry 同步回 Google Sheets"""
        logger.info('🔄 開始 本地 → Sheets 同步...')

        try:
            if not self.sheets_api.workbook:
                logger.warning('⚠️ Google Sheets 未連接，跳過此同步')
                return

            # TODO: 實現 Registry.md → Sheets 的同步邏輯

        except Exception as e:
            logger.error(f'✗ 本地 → Sheets 同步出錯: {e}')

        logger.info('✓ 本地 → Sheets 同步完成\n')

    def full_sync(self):
        """執行完整的三向同步"""
        logger.info('🔄🔄🔄 開始完整三向同步...')

        # 1. Sheets → 本地
        self.sync_sheets_to_local()

        # 2. 本地 → Registry
        LocalStorage.update_registry_md()

        # 3. 本地 → Git
        GitManager.push_to_remote()

        logger.info('✓✓✓ 完整同步完成\n')

    @staticmethod
    def _log_sync_event(event: Dict[str, Any]):
        """記錄同步事件"""
        try:
            with open(SYNC_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            logger.error(f'記錄同步事件失敗: {e}')


# ===== 主程序 =====
if __name__ == '__main__':
    logger.info('=' * 60)
    logger.info('Krystal 策略同步引擎 v1.0')
    logger.info(f'啟動時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('=' * 60)

    engine = SyncEngine()
    engine.start()

    # 保持運行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('\n🛑 同步引擎已停止')
