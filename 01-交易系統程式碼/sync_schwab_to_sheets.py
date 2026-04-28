#!/usr/bin/env python3
"""
Schwab 持倉同步到 Google Sheets + 本地 DB
可單獨執行，也可由 run_daily_nav.bat 呼叫
前置條件：有效的 secrets/schwab_token.json（透過 init_schwab_oauth.py 取得）
"""
import sys
import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / 'dashboard_v8' / 'broker_positions.db'


def main():
    print("=" * 50)
    print(f"  Schwab 持倉同步  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        from brokers.schwab_api import get_schwab_accounts, load_config_from_env, load_token, has_valid_token, DEFAULT_TOKEN_PATH
    except ImportError as e:
        logger.error(f"❌ 無法匯入 schwab_api: {e}")
        return False

    cfg = load_config_from_env()
    if not cfg.client_id:
        logger.error("❌ SCHWAB_CLIENT_ID 未設定，跳過同步")
        return False

    token = load_token(DEFAULT_TOKEN_PATH)
    if not has_valid_token(token):
        logger.info("Token 已過期，嘗試自動 refresh...")
        from brokers.schwab_api import _force_refresh_token
        new_access = _force_refresh_token(DEFAULT_TOKEN_PATH)
        if not new_access:
            logger.error("❌ Schwab token 無效且 refresh 失敗，請執行 init_schwab_oauth.py 重新授權")
            return False
        logger.info("Token refresh 成功")

    try:
        accounts_resp = get_schwab_accounts()
    except Exception as e:
        logger.error(f"❌ 取得 Schwab 帳戶失敗: {e}")
        return False

    if not accounts_resp:
        logger.error("❌ Schwab API 無回應，token 可能過期")
        return False

    accounts = accounts_resp if isinstance(accounts_resp, list) else accounts_resp.get('accounts', [])
    positions = []
    for acct in accounts:
        sec = acct.get('securitiesAccount', acct)
        for p in sec.get('positions', []):
            inst = p.get('instrument', {})
            sym  = inst.get('symbol', '')
            if not sym:
                continue
            qty  = float(p.get('longQuantity', p.get('quantity', 0)) or 0)
            avg  = float(p.get('averagePrice', 0) or 0)
            mv   = float(p.get('marketValue', qty * avg) or 0)
            pnl  = float(p.get('longOpenProfitLoss', p.get('unrealizedProfitLoss', p.get('currentDayProfitLoss', 0))) or 0)
            mkt  = mv / qty if qty else avg
            positions.append({
                'symbol': sym, 'position': qty, 'avgCost': avg,
                'marketPrice': round(mkt, 4), 'marketValue': mv,
                'unrealizedPNL': pnl, 'currency': 'USD', 'exchange': 'US'
            })

    if not positions:
        logger.info("ℹ️ Schwab 帳戶無持倉")
        return True

    logger.info(f"取得 {len(positions)} 筆 Schwab 持倉")
    for p in positions:
        logger.info(f"   {p['symbol']:<8}  {p['position']}股  均價:{p['avgCost']:.2f}  市值:{p['marketValue']:.2f}  未實現:{p['unrealizedPNL']:+.2f}")

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
            broker_idx = next((header.index(c) for c in ['券商', 'broker', 'Broker'] if c in header), None)
            if broker_idx is not None:
                rows_del = [r_idx for r_idx, r_vals in enumerate(all_vals[1:], start=2)
                            if len(r_vals) > broker_idx and r_vals[broker_idx].lower() in ('schwab', 'charles schwab')]
                for r_idx in reversed(rows_del):
                    sheet.delete_rows(r_idx)
            new_rows = []
            for p in positions:
                row_data = [''] * len(header)
                qty, avg = p['position'], p['avgCost']
                mapping = {
                    '時間': now_str, 'timestamp': now_str,
                    '券商': 'Schwab', 'broker': 'Schwab',
                    'symbol': p['symbol'], 'secType': 'STK',
                    'exchange': 'US', 'currency': 'USD',
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
            logger.info(f"✅ 已寫入 Google Sheets broker_positions: {wrote_sheets} 筆")
    except Exception as e:
        logger.warning(f"⚠️ Schwab → Sheets 寫入失敗: {e}")

    # ── 寫入本地 DB ──
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
                 'Schwab', 'USD', now_str))
            wrote_db += 1
        conn.commit()
        conn.close()
        logger.info(f"✅ 已更新本地 DB broker_positions: {wrote_db} 筆")
    except Exception as e:
        logger.warning(f"⚠️ Schwab → DB 寫入失敗: {e}")

    # 通知
    try:
        from modules.notifier import notify_sync_event
        lines = [f"{p['symbol']:<8} {p['position']}股  現價:{p['marketPrice']:.2f}  未實現:{p['unrealizedPNL']:+.2f}" for p in positions]
        notify_sync_event("Schwab 持倉同步完成", "\n".join(lines), ok=True)
    except Exception as e:
        logger.debug(f"[notifier] {e}")

    logger.info(f"\n✅ Schwab 同步完成：Sheets {wrote_sheets} 筆，DB {wrote_db} 筆")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
