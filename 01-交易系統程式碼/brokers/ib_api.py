"""
Interactive Brokers (IB) API 連接模組
使用 ib_insync 連接 IB TWS/Gateway 實時查詢帳戶信息和持倉
"""

import logging
import os
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import threading
import time

load_dotenv()
logger = logging.getLogger(__name__)

try:
    from ib_insync import IB, Contract
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logger.warning("ib_insync 未安裝，IB 功能將禁用")

# ============================
# IB 連接配置
# ============================

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "99"))

_ib_instance: Optional[IB] = None


def get_ib_connection() -> Optional[IB]:
    """取得 IB 連接實例（單例）"""
    global _ib_instance

    if not IB_AVAILABLE:
        logger.error("ib_insync 未可用")
        return None

    if _ib_instance is None:
        try:
            _ib_instance = IB()
            _ib_instance.connect(
                host=IB_HOST,
                port=IB_PORT,
                clientId=IB_CLIENT_ID,
                readonly=True
            )
            logger.info(f"IB 連接成功：{IB_HOST}:{IB_PORT}")
        except Exception as e:
            logger.error(f"IB 連接失敗: {e}")
            _ib_instance = None
            return None

    return _ib_instance


def get_account_summary() -> Dict[str, Any]:
    """取得 IB 帳戶摘要 - 暫時禁用（使用子進程替代）"""
    # ib_insync 在 Flask 多線程環境中有事件循環問題
    # 改為使用 query_ib_positions.py 子進程
    logger.warning("⚠️ get_account_summary() 已禁用，請使用 /api/ib-account-summary 或 query_ib_positions.py")
    return {
        'status': 'error',
        'connected': False,
        'message': 'IB API 暫時禁用，使用 /api/ib-account-summary API'
    }


def get_positions() -> List[Dict[str, Any]]:
    """取得 IB 所有持倉"""
    try:
        ib = get_ib_connection()
        if not ib or not ib.isConnected():
            return []

        positions = ib.positions()
        result = []

        for pos in positions:
            if pos.position == 0:
                continue

            result.append({
                'symbol': pos.contract.symbol,
                'secType': pos.contract.secType,
                'exchange': pos.contract.exchange,
                'currency': pos.contract.currency,
                'position': pos.position,
                'avgCost': pos.avgCost,
                'marketValue': getattr(pos, 'marketValue', 0),
            })

        return result

    except Exception as e:
        logger.error(f"取得 IB 持倉失敗: {e}")
        return []


def disconnect():
    """斷開 IB 連接"""
    global _ib_instance
    if _ib_instance:
        try:
            _ib_instance.disconnect()
            _ib_instance = None
            logger.info("IB 連接已斷開")
        except Exception as e:
            logger.warning(f"斷開 IB 連接時出錯: {e}")
