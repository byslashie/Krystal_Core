"""
IB 持倉實時同步到 Google Sheets
- 從 IB TWS/Gateway 抓取最新持倉
- 自動寫入 Google Sheets 的 'broker_positions' 工作表
- 返回同步結果
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets_utils import get_sheet

logger = logging.getLogger(__name__)

# Google Sheets 配置
BROKER_POSITIONS_SHEET = 'broker_positions'
IB_POSITIONS_SHEET = 'ib_positions'  # 專用 IB 持倉表（可選）


class IBPositionSyncer:
    """IB 持倉同步器"""

    def __init__(self):
        self.ib = None
        self.sync_time = None
        self.positions = []

    def connect_ib(self) -> bool:
        """連接 IB（創建新實例以避免事件循環問題）"""
        try:
            from ib_insync import IB

            # 創建新的 IB 實例（不使用全局實例）
            self.ib = IB()
            self.ib.connect(
                host='127.0.0.1',
                port=7496,
                clientId=199,  # 使用不同的 client ID
                readonly=True
            )

            if self.ib and self.ib.isConnected():
                logger.info("✅ IB 連接成功")
                return True
            else:
                logger.error("❌ IB 連接失敗")
                return False
        except Exception as e:
            logger.error(f"❌ IB 連接錯誤: {str(e)}")
            return False

    def fetch_positions(self) -> List[Dict[str, Any]]:
        """從 IB 抓取持倉"""
        try:
            if not self.ib or not self.ib.isConnected():
                logger.warning("⚠️ IB 未連接")
                return []

            portfolio = self.ib.portfolio()
            positions = []

            for item in portfolio:
                try:
                    position = {
                        'symbol': item.contract.symbol,
                        'exchange': item.contract.exchange,
                        'currency': item.contract.currency,
                        'position': float(item.position),
                        'avgCost': float(item.averageCost),
                        'marketPrice': float(item.marketPrice),
                        'marketValue': float(item.marketValue),
                        'unrealizedPNL': float(item.unrealizedPNL),
                        'realizedPNL': float(item.realizedPNL),
                        'account': item.account,
                        'contractId': item.contract.conId,
                        'broker': 'IB',
                        '券商': 'IB',
                        'syncTime': datetime.now().isoformat(),
                    }
                    positions.append(position)
                    logger.info(f"📊 {item.contract.symbol}: {item.position} 股 @ {item.marketPrice}")
                except Exception as e:
                    logger.error(f"❌ 解析持倉失敗: {str(e)}")
                    continue

            self.positions = positions
            self.sync_time = datetime.now()
            logger.info(f"✅ 成功取得 {len(positions)} 筆持倉")
            return positions

        except Exception as e:
            logger.error(f"❌ 抓取持倉失敗: {str(e)}")
            return []

    def sync_to_sheets(self, clear_existing: bool = False) -> Dict[str, Any]:
        """同步持倉到 Google Sheets"""
        try:
            if not self.positions:
                logger.warning("⚠️ 沒有持倉數據可同步")
                return {
                    'status': 'warning',
                    'message': '沒有持倉數據',
                    'count': 0
                }

            # 準備 Google Sheets 的行數據
            rows = []

            # 準備行數據
            for pos in self.positions:
                row = [
                    pos.get('symbol', ''),
                    pos.get('exchange', ''),
                    pos.get('currency', ''),
                    pos.get('position', 0),
                    pos.get('avgCost', 0),
                    pos.get('marketPrice', 0),
                    pos.get('marketValue', 0),
                    pos.get('unrealizedPNL', 0),
                    pos.get('realizedPNL', 0),
                    pos.get('account', ''),
                    pos.get('broker', 'IB'),
                    pos.get('contractId', ''),
                    pos.get('syncTime', ''),
                ]
                rows.append(row)

            # 寫入到 broker_positions（主要持倉表）
            try:
                sheet = get_sheet(BROKER_POSITIONS_SHEET)
                if sheet:
                    sheet.append_rows(rows, value_input_option="USER_ENTERED")
                    logger.info(f"✅ 已寫入 {BROKER_POSITIONS_SHEET} {len(rows)} 筆記錄")
                else:
                    logger.warning(f"⚠️ 無法找到 {BROKER_POSITIONS_SHEET} 工作表")
            except Exception as e:
                logger.warning(f"⚠️ 寫入 broker_positions 失敗: {str(e)}")

            # 也寫入到 ib_positions（IB 專用表，可選）
            try:
                sheet = get_sheet(IB_POSITIONS_SHEET)
                if sheet:
                    sheet.append_rows(rows, value_input_option="USER_ENTERED")
                    logger.info(f"✅ 已寫入 {IB_POSITIONS_SHEET} {len(rows)} 筆記錄")
            except Exception as e:
                logger.warning(f"⚠️ 寫入 IB 專用表失敗: {str(e)}")

            return {
                'status': 'success',
                'message': f'已同步 {len(rows)} 筆持倉到 Google Sheets',
                'count': len(rows),
                'positions': self.positions,
                'syncTime': self.sync_time.isoformat() if self.sync_time else None,
            }

        except Exception as e:
            logger.error(f"❌ 同步到 Sheets 失敗: {str(e)}")
            return {
                'status': 'error',
                'message': f'同步失敗: {str(e)}',
                'count': 0
            }

    def disconnect(self):
        """斷開 IB 連接"""
        try:
            if self.ib and self.ib.isConnected():
                self.ib.disconnect()
                logger.info("🔌 IB 已斷開連接")
        except Exception as e:
            logger.warning(f"⚠️ 斷開連接時出錯: {str(e)}")


def sync_ib_positions_now(clear_existing: bool = False) -> Dict[str, Any]:
    """立即同步 IB 持倉到 Google Sheets（便利函數）"""
    syncer = IBPositionSyncer()

    try:
        # 連接 IB
        if not syncer.connect_ib():
            return {
                'status': 'error',
                'message': '無法連接到 IB TWS/Gateway，請確保應用已啟動且監聽 7496 端口',
                'count': 0
            }

        # 抓取持倉
        positions = syncer.fetch_positions()
        if not positions:
            return {
                'status': 'warning',
                'message': '沒有取得任何持倉',
                'count': 0
            }

        # 同步到 Sheets
        result = syncer.sync_to_sheets(clear_existing=clear_existing)
        return result

    except Exception as e:
        logger.error(f"❌ 同步過程出錯: {str(e)}")
        return {
            'status': 'error',
            'message': f'同步失敗: {str(e)}',
            'count': 0
        }
    finally:
        syncer.disconnect()


if __name__ == '__main__':
    # 測試用
    logging.basicConfig(level=logging.INFO)
    result = sync_ib_positions_now()
    print(f"\n結果: {result}")
