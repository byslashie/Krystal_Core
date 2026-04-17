#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 統一持倉同步模組
功能：
1. 從 IB API 獲取持倉
2. 從元大 API 獲取持倉
3. 合併轉換為統一格式
4. 寫入 Google Sheets 的 broker_positions 分頁
5. 記錄同步日誌到 sync_logs 分頁
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Any, Tuple

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import pandas as pd

# 加載環境配置
load_dotenv()

# ============================================================================
# 日誌配置
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 導入必要的模組
# ============================================================================

try:
    from sheets_utils import get_sheet, append_sheet, overwrite_sheet, read_sheet
    SHEETS_OK = True
except Exception as e:
    logger.error(f"❌ 無法導入 sheets_utils: {e}")
    SHEETS_OK = False

try:
    from brokers.ib_api import get_open_positions, get_account_snapshot
    IB_OK = True
except Exception as e:
    logger.warning(f"⚠️ 無法導入 IB API: {e}")
    IB_OK = False

# 元大 API（可能不在此環境）
YUANTA_OK = False
try:
    from brokers.yuanta_api import yuanta_login, fetch_positions, register_events
    YUANTA_OK = True
except Exception as e:
    logger.warning(f"⚠️ 無法導入元大 API: {e}")

# Schwab API（需要 OAuth 認證）
SCHWAB_OK = False
try:
    from brokers.schwab_api import get_schwab_all_positions, is_schwab_enabled
    SCHWAB_OK = True
except Exception as e:
    logger.warning(f"⚠️ 無法導入 Schwab API: {e}")

# ============================================================================
# 工具函數
# ============================================================================

def _now_ts() -> str:
    """當前時間戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _today() -> str:
    """今天日期"""
    return datetime.now().strftime("%Y-%m-%d")


def _format_position_for_sheets(
    symbol: str,
    direction: str,  # "多" or "空"
    quantity: float,
    avg_price: float,
    current_price: float = None,
    broker: str = "IB",
    market: str = "",  # "NASDAQ", "TWSE", etc.
) -> Dict[str, Any]:
    """
    轉換持倉為 Google Sheets broker_positions 格式

    預期欄位：時間 | 券商 | 市場 | 標的 | 方向 | 數量 | 均價 | 現價 | 帳面損益 | 損益率
    """
    if current_price is None:
        current_price = avg_price

    if quantity == 0:
        pnl = 0
        pnl_pct = 0
    else:
        pnl = (current_price - avg_price) * quantity
        pnl_pct = (current_price / avg_price - 1) * 100 if avg_price != 0 else 0

    return {
        "時間": _now_ts(),
        "券商": broker,
        "市場": market,
        "標的": symbol,
        "方向": direction,
        "數量": int(quantity),
        "均價": round(avg_price, 2),
        "現價": round(current_price, 2),
        "帳面損益": round(pnl, 2),
        "損益率": round(pnl_pct, 2),
    }


# ============================================================================
# IB 持倉同步
# ============================================================================

def sync_ib_positions() -> Tuple[List[Dict[str, Any]], str]:
    """
    從 IB 獲取持倉並轉換為 Sheets 格式
    回傳 (持倉列表, 狀態信息)
    """
    if not IB_OK:
        return [], "IB API 未正常導入"

    try:
        logger.info("🔄 [IB] 開始獲取持倉...")
        positions = get_open_positions()

        if not positions:
            logger.info("✅ [IB] 沒有持倉")
            return [], "沒有持倉"

        formatted_positions = []
        for pos in positions:
            # IB 的 position 欄位為正數表示多頭，負數表示空頭
            qty = abs(pos['position'])
            direction = "多" if pos['position'] > 0 else "空"

            # 判斷市場
            market = ""
            symbol = pos.get('symbol', '')
            if pos.get('exchange') in ['NASDAQ', 'NYSE']:
                market = pos.get('exchange', '')
            elif pos.get('secType') == 'STK':
                market = "TWSE"  # 台灣股票

            formatted = _format_position_for_sheets(
                symbol=symbol,
                direction=direction,
                quantity=qty,
                avg_price=pos.get('avgCost', 0),
                current_price=pos.get('avgCost', 0),  # IB API 沒有即時價格，用均價
                broker="IB",
                market=market,
            )
            formatted_positions.append(formatted)

        logger.info(f"✅ [IB] 成功獲取 {len(formatted_positions)} 筆持倉")
        return formatted_positions, f"成功獲取 {len(formatted_positions)} 筆"

    except Exception as e:
        error_msg = f"IB 同步失敗: {str(e)}"
        logger.error(f"❌ [IB] {error_msg}")
        return [], error_msg


# ============================================================================
# Schwab 持倉同步
# ============================================================================

def sync_schwab_positions() -> Tuple[List[Dict[str, Any]], str]:
    """
    從 Schwab 獲取持倉並轉換為 Sheets 格式
    回傳 (持倉列表, 狀態信息)

    🔑 前置條件：
       1. 設定環境變數：SCHWAB_CLIENT_ID, SCHWAB_CLIENT_SECRET, SCHWAB_REDIRECT_URI
       2. 執行一次 OAuth 認證（會存 token 到 secrets/schwab_token.json）
    """
    if not SCHWAB_OK:
        return [], "Schwab API 未正常導入"

    try:
        # 檢查是否啟用且有有效 token
        if not is_schwab_enabled():
            logger.info("⚠️ [Schwab] 未啟用或無有效 token，跳過同步")
            return [], "未啟用或無有效 token"

        logger.info("🔄 [Schwab] 開始獲取持倉...")
        positions = get_schwab_all_positions()

        if not positions:
            logger.info("✅ [Schwab] 沒有持倉")
            return [], "沒有持倉"

        formatted_positions = []
        for pos in positions:
            # Schwab 持倉結構
            symbol = pos.get("symbol", "")
            if not symbol:
                continue

            # quantity 正數為多頭，負數為空頭
            qty = abs(pos.get("quantity", 0))
            direction = "多" if pos.get("quantity", 0) > 0 else "空"

            # 平均成本和市場價值
            avg_price = float(pos.get("averagePrice", pos.get("costBasis", 0)))
            current_price = float(pos.get("marketValue", 0)) / qty if qty > 0 else avg_price

            # 判斷市場（Schwab 通常需要額外的字段來判斷）
            asset_type = pos.get("assetType", "EQUITY")
            market = "NASDAQ" if asset_type == "EQUITY" else "OTHER"

            formatted = _format_position_for_sheets(
                symbol=symbol,
                direction=direction,
                quantity=qty,
                avg_price=avg_price,
                current_price=current_price,
                broker="Schwab",
                market=market,
            )
            formatted_positions.append(formatted)

        logger.info(f"✅ [Schwab] 成功獲取 {len(formatted_positions)} 筆持倉")
        return formatted_positions, f"成功獲取 {len(formatted_positions)} 筆"

    except Exception as e:
        error_msg = f"Schwab 同步失敗: {str(e)}"
        logger.error(f"❌ [Schwab] {error_msg}")
        return [], error_msg


# ============================================================================
# 元大持倉同步（僅限 Windows + 32-bit Python）
# ============================================================================

def sync_yuanta_positions() -> Tuple[List[Dict[str, Any]], str]:
    """
    從元大獲取持倉並轉換為 Sheets 格式
    回傳 (持倉列表, 狀態信息)
    """
    if not YUANTA_OK:
        return [], "元大 API 未可用"

    try:
        logger.info("🔄 [Yuanta] 開始獲取持倉...")

        api = yuanta_login()
        register_events(api)

        # 等待事件捕獲
        import time
        time.sleep(2)

        positions = fetch_positions(api)

        if not positions:
            logger.info("✅ [Yuanta] 沒有持倉")
            return [], "沒有持倉"

        formatted_positions = []
        for pos in positions:
            # 假設 pos 包含：symbol, qty, avg_price, market 等欄位
            symbol = pos.get('symbol', '')
            qty = abs(pos.get('qty', 0))
            direction = "多" if pos.get('qty', 0) > 0 else "空"

            formatted = _format_position_for_sheets(
                symbol=symbol,
                direction=direction,
                quantity=qty,
                avg_price=pos.get('avg_price', 0),
                current_price=pos.get('current_price', pos.get('avg_price', 0)),
                broker="Yuanta",
                market=pos.get('market', 'TWSE'),
            )
            formatted_positions.append(formatted)

        logger.info(f"✅ [Yuanta] 成功獲取 {len(formatted_positions)} 筆持倉")
        return formatted_positions, f"成功獲取 {len(formatted_positions)} 筆"

    except Exception as e:
        error_msg = f"元大同步失敗: {str(e)}"
        logger.error(f"❌ [Yuanta] {error_msg}")
        return [], error_msg


# ============================================================================
# 主同步邏輯
# ============================================================================

def sync_all_positions() -> Dict[str, Any]:
    """
    同步所有經紀商持倉到 Google Sheets
    """
    print("\n" + "=" * 70)
    print("🔄 持倉同步開始")
    print("=" * 70 + "\n")

    if not SHEETS_OK:
        logger.error("❌ Google Sheets 連接失敗，停止同步")
        return {
            'status': 'failed',
            'error': 'Sheets 連接失敗',
            'timestamp': _now_ts(),
        }

    # 1. 從各經紀商獲取持倉
    all_positions = []
    sync_results = {}

    # IB 同步
    ib_positions, ib_status = sync_ib_positions()
    all_positions.extend(ib_positions)
    sync_results['IB'] = {
        'count': len(ib_positions),
        'status': ib_status,
    }

    # Schwab 同步
    schwab_positions, schwab_status = sync_schwab_positions()
    all_positions.extend(schwab_positions)
    sync_results['Schwab'] = {
        'count': len(schwab_positions),
        'status': schwab_status,
    }

    # 元大同步
    yuanta_positions, yuanta_status = sync_yuanta_positions()
    all_positions.extend(yuanta_positions)
    sync_results['Yuanta'] = {
        'count': len(yuanta_positions),
        'status': yuanta_status,
    }

    # 2. 寫入 Google Sheets
    try:
        sheet = get_sheet("broker_positions")

        if all_positions:
            # 轉換為行列格式
            df = pd.DataFrame(all_positions)

            # 獲取表頭
            header = sheet.row_values(1)
            header_clean = [str(c).replace("欄位：", "").strip() for c in header]

            # 清空現有數據（保留表頭）
            try:
                if len(sheet.get_all_values()) > 1:
                    sheet.delete_rows(2, sheet.row_count)
                    logger.info("✅ 已清空現有持倉數據")
            except Exception:
                pass  # 可能沒有數據或其他錯誤

            # 逐行寫入
            for _, row in df.iterrows():
                row_values = [row.get(col, "") for col in header_clean]
                sheet.append_row(row_values, value_input_option="USER_ENTERED")

            logger.info(f"✅ 成功寫入 {len(all_positions)} 筆持倉到 Google Sheets")
        else:
            logger.warning("⚠️ 沒有持倉數據要寫入")

        # 3. 記錄同步日誌
        try:
            log_sheet = get_sheet("sync_logs")
            for broker, result in sync_results.items():
                log_row = [
                    _now_ts(),
                    "broker_positions",
                    broker,
                    result['count'],
                    "success" if result['count'] > 0 else "no_data",
                    result['status'],
                ]
                log_sheet.append_row(log_row, value_input_option="USER_ENTERED")

            logger.info("✅ 同步日誌已記錄")
        except Exception as e:
            logger.warning(f"⚠️ 記錄同步日誌失敗: {e}")

        print("\n" + "=" * 70)
        print("✅ 持倉同步完成")
        print("=" * 70)
        print(f"\n📊 同步結果：")
        print(f"   • IB: {sync_results['IB']['count']} 筆 ({sync_results['IB']['status']})")
        print(f"   • Schwab: {sync_results['Schwab']['count']} 筆 ({sync_results['Schwab']['status']})")
        print(f"   • Yuanta: {sync_results['Yuanta']['count']} 筆 ({sync_results['Yuanta']['status']})")
        print(f"   • 總計: {len(all_positions)} 筆")
        print()

        return {
            'status': 'success',
            'timestamp': _now_ts(),
            'total_positions': len(all_positions),
            'brokers': sync_results,
        }

    except Exception as e:
        error_msg = f"寫入 Google Sheets 失敗: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            'status': 'failed',
            'error': error_msg,
            'timestamp': _now_ts(),
            'brokers': sync_results,
        }


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    """主函數 - 可以直接執行此腳本進行手動同步"""
    result = sync_all_positions()

    if result['status'] == 'failed':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
