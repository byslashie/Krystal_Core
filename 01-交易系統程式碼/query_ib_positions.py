#!/usr/bin/env python
"""
獨立的 IB 位置查詢腳本（作為子進程運行）
避免 Flask 多線程環境中的事件循環問題
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Python 3.14 相容：ib_insync 需要 event loop 預先建立
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID = int(os.getenv("IB_QUERY_CLIENT_ID", "198"))

try:
    from ib_insync import IB

    ib = IB()
    ib.connect(host=IB_HOST, port=IB_PORT, clientId=IB_CLIENT_ID, readonly=True)

    if not ib.isConnected():
        print(json.dumps({
            'status': 'error',
            'message': f'無法連接 IB TWS/Gateway ({IB_HOST}:{IB_PORT})'
        }))
        sys.exit(1)

    # 🟢 增加等待時間，確保數據同步
    ib.waitOnUpdate(2)

    # 獲取帳戶和持倉
    managed_accounts = ib.managedAccounts()
    portfolio = ib.portfolio()

    positions = []
    total_market_value = 0
    total_unrealized_pnl = 0

    for item in portfolio:
        avg_cost  = float(item.averageCost)
        mkt_price = float(item.marketPrice)
        qty       = float(item.position)
        unrealized = float(item.unrealizedPNL)
        pct = ((mkt_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
        raw_exch = item.contract.exchange or ''
        primary  = getattr(item.contract, 'primaryExchange', '') or ''
        # SMART 不是真正的交易所，優先用 primaryExchange
        exch = primary if (not raw_exch or raw_exch == 'SMART') else raw_exch
        pos_data = {
            'symbol':        item.contract.symbol,
            'exchange':      exch or 'US',
            'currency':      item.contract.currency,
            'position':      qty,
            'avgCost':       avg_cost,
            'marketPrice':   mkt_price,
            'marketValue':   float(item.marketValue),
            'unrealizedPNL': unrealized,
            'unrealizedPct': round(pct, 2),
            'realizedPNL':   float(item.realizedPNL),
            'account':       item.account
        }
        positions.append(pos_data)
        total_market_value  += pos_data['marketValue']
        total_unrealized_pnl += pos_data['unrealizedPNL']

    # 從帳戶摘要取得真實 NLV 和現金餘額
    real_nlv  = 0.0
    real_cash = 0.0
    try:
        account_id = managed_accounts[0] if managed_accounts else None
        acc_values = ib.accountValues(account_id)
        
        # 優先尋找 NetLiquidation 和 TotalCashValue
        for v in acc_values:
            try:
                val = float(v.value)
            except (ValueError, TypeError):
                continue

            # NLV 邏輯 (優先抓 USD 或 BASE)
            if v.tag in ['NetLiquidation', 'NetLiquidationByCurrency']:
                if v.currency in ['USD', 'BASE']:
                    real_nlv = val if not real_nlv else real_nlv
            
            # Cash 邏輯
            if v.tag == 'TotalCashValue':
                if v.currency in ['USD', 'BASE']:
                    real_cash = val if not real_cash else real_cash
                    
    except Exception as e:
        pass

    if real_nlv == 0:
        real_nlv = total_market_value  # fallback

    # 輸出結果
    result = {
        'status':               'success',
        'connected':            True,
        'account_id':           managed_accounts[0] if managed_accounts else 'Unknown',
        'net_liquidation_value': round(real_nlv, 2),
        'total_cash_value':     round(real_cash, 2),
        'unrealized_pnl':       round(total_unrealized_pnl, 2),
        'positions_count':      len(positions),
        'positions':            positions,
        'timestamp':            datetime.now().isoformat()
    }

    # 使用標準 print，但確保不報編碼錯誤
    print(json.dumps(result, indent=2, ensure_ascii=False))
    ib.disconnect()
    sys.exit(0)

except Exception as e:
    import traceback
    print(json.dumps({
        'status': 'error',
        'message': str(e),
        'traceback': traceback.format_exc()
    }))
    sys.exit(1)
