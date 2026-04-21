#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker Positions 表結構驗證和防護
確保 Google Sheets 中的 broker_positions 表永遠保持正確的格式
"""

import sys
import io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sheets_utils import read_sheet_data_with_cache, overwrite_broker_positions

class BrokerPositionsValidator:
    """broker_positions 表驗證器"""

    # 定義正確的表結構（支持中文和英文欄位名）
    REQUIRED_COLUMNS = ['symbol', 'position', 'avgCost', 'currency']
    OPTIONAL_COLUMNS = [
        'currentPrice', 'marketPrice', 'marketValue',
        'unrealizedPnL', 'unrealizedPNL',
        'timestamp', '時間',
        'broker', '券商',
        'secType', 'exchange', 'totalCost', 'sellable', 'limitUp', 'limitDown'
    ]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

    # 定義允許的經紀商
    ALLOWED_BROKERS = ['IB', 'IBKR', '盈透', 'Schwab', 'schwab', '元大', 'Yuanta']

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.data = None

    def validate(self):
        """執行完整驗證"""
        print("[*] 開始驗證 broker_positions 表結構...\n")

        try:
            # 讀取數據
            self.data = read_sheet_data_with_cache('broker_positions')
            if self.data is None or self.data.empty:
                self.errors.append("無法讀取 broker_positions")
                return False

            print(f"✓ 讀取 {len(self.data)} 筆記錄\n")

            # 1. 檢查欄位結構
            self._check_columns()

            # 2. 檢查必要欄位的數據完整性
            self._check_required_fields()

            # 3. 檢查重複的標的
            self._check_duplicates()

            # 4. 檢查數據類型
            self._check_data_types()

            # 5. 檢查垃圾數據
            self._check_garbage_data()

            # 列印報告
            self._print_report()

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"驗證異常：{e}")
            return False

    def _check_columns(self):
        """檢查欄位是否正確"""
        print("📋 檢查欄位結構...")

        actual_cols = set(self.data.columns)

        # 檢查是否有多餘的空欄位或垃圾欄位
        garbage_cols = [c for c in actual_cols if c in ['', '_1', '_2', '_3', '_4', '_5'] or (isinstance(c, str) and c.startswith('_'))]
        if garbage_cols:
            self.errors.append(f"發現垃圾欄位：{garbage_cols}")

        # 檢查必要欄位是否存在
        missing_required = set(self.REQUIRED_COLUMNS) - actual_cols
        if missing_required:
            self.errors.append(f"缺少必要欄位：{missing_required}")

        print(f"  實際欄位：{list(actual_cols)}")
        if not garbage_cols and not missing_required:
            print("  ✓ 欄位結構正確\n")
        else:
            print()

    def _check_required_fields(self):
        """檢查必要欄位的數據完整性"""
        print("📊 檢查必要欄位完整性...")

        for col in self.REQUIRED_COLUMNS:
            if col not in self.data.columns:
                continue

            null_count = self.data[col].isna().sum()
            empty_count = (self.data[col].astype(str).str.strip() == '').sum()

            if null_count + empty_count > 0:
                self.errors.append(f"欄位 '{col}' 有 {null_count + empty_count} 個空值")
                print(f"  ⚠️  {col}: {null_count + empty_count} 個空值")
            else:
                print(f"  ✓ {col}: 完整")
        print()

    def _check_duplicates(self):
        """檢查重複的標的（同一標的+經紀商組合應只有一筆）"""
        print("🔍 檢查重複的標的...")

        if 'symbol' not in self.data.columns:
            return

        # 按 symbol + broker 組合去重
        # 不同經紀商的同一標的是允許的
        if 'broker' in self.data.columns or '券商' in self.data.columns:
            broker_col = 'broker' if 'broker' in self.data.columns else '券商'
            duplicates = self.data.groupby(['symbol', broker_col]).size()
            duplicates = duplicates[duplicates > 1]

            if len(duplicates) > 0:
                self.errors.append(f"發現 {len(duplicates)} 個 symbol+broker 組合有重複記錄")
                print(f"  ⚠️  發現重複（同一標的+經紀商）：")
                for (symbol, broker), count in duplicates.items():
                    print(f"      {symbol} ({broker}): {count} 筆")
            else:
                print("  ✓ 沒有重複（同一標的+經紀商只有一筆）\n")
        else:
            # 如果沒有 broker 欄位，則按 symbol 去重
            symbol_counts = self.data['symbol'].value_counts()
            duplicates = symbol_counts[symbol_counts > 1]

            if len(duplicates) > 0:
                self.errors.append(f"發現 {len(duplicates)} 個標的有重複記錄：{dict(duplicates)}")
                print(f"  ⚠️  發現重複：")
                for symbol, count in duplicates.items():
                    print(f"      {symbol}: {count} 筆")
            else:
                print("  ✓ 沒有重複的標的\n")
        print()

    def _check_data_types(self):
        """檢查數據類型是否正確"""
        print("🔢 檢查數據類型...")

        # symbol 應該是字符串，不能是時間戳
        if 'symbol' in self.data.columns:
            for idx, symbol in enumerate(self.data['symbol']):
                symbol_str = str(symbol).strip()
                # 檢查是否看起來像時間戳（包含空格和冒號）
                if ' ' in symbol_str and ':' in symbol_str:
                    self.errors.append(f"第 {idx+1} 行的 symbol 看起來像時間戳：{symbol}")
                    print(f"  ⚠️  第 {idx+1} 行：{symbol} 看起來像時間戳")

        # position, avgCost 應該是數字
        for col in ['position', 'avgCost', 'marketPrice']:
            if col not in self.data.columns:
                continue

            try:
                pd.to_numeric(self.data[col], errors='coerce')
                print(f"  ✓ {col}: 數據類型正確")
            except:
                self.warnings.append(f"欄位 '{col}' 可能包含非數字數據")
                print(f"  ⚠️  {col}: 包含非數字數據")
        print()

    def _check_garbage_data(self):
        """檢查垃圾數據（如混亂的時間序列）"""
        print("🗑️  檢查垃圾數據...")

        if 'symbol' in self.data.columns:
            suspicious_count = 0
            for idx, symbol in enumerate(self.data['symbol']):
                symbol_str = str(symbol).strip()
                # 檢查是否包含多個空格（通常表示混亂的格式）
                if symbol_str.count(' ') > 1:
                    suspicious_count += 1

            if suspicious_count > 0:
                self.errors.append(f"發現 {suspicious_count} 筆可疑的 symbol 格式")
                print(f"  ⚠️  發現 {suspicious_count} 筆格式異常的記錄")
        print()

    def _print_report(self):
        """列印驗證報告"""
        print("\n" + "="*60)
        print("驗證報告")
        print("="*60)

        if self.errors:
            print(f"\n❌ 發現 {len(self.errors)} 個錯誤：")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        else:
            print("\n✅ 沒有發現錯誤")

        if self.warnings:
            print(f"\n⚠️  發現 {len(self.warnings)} 個警告：")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")

        print("\n" + "="*60)

        # 數據摘要
        if self.data is not None:
            print(f"\n📈 數據摘要：")
            print(f"   總記錄數：{len(self.data)}")
            if 'symbol' in self.data.columns:
                print(f"   唯一標的：{self.data['symbol'].nunique()}")
            if 'broker' in self.data.columns:
                print(f"   經紀商分佈：{dict(self.data['broker'].value_counts())}")


def auto_fix_if_needed(validator):
    """如果發現錯誤，自動修復"""
    if not validator.errors:
        print("\n✅ broker_positions 表結構正確，無需修復\n")
        return True

    print("\n⚠️  發現錯誤，是否自動修復？(y/n)")
    response = input(">>> ").strip().lower()

    if response != 'y':
        print("跳過修復\n")
        return False

    print("[*] 開始自動修復...\n")

    try:
        data = validator.data.copy()

        # 1. 移除垃圾欄位
        garbage_cols = [c for c in data.columns if c in ['', '_1', '_2', '_3', '_4', '_5']]
        if garbage_cols:
            data = data.drop(columns=garbage_cols)
            print(f"✓ 移除垃圾欄位：{garbage_cols}")

        # 2. 移除包含時間戳的行（看起來被污染的行）
        if 'symbol' in data.columns:
            original_len = len(data)
            data = data[~data['symbol'].astype(str).str.contains(':', na=False)]
            removed = original_len - len(data)
            if removed > 0:
                print(f"✓ 移除 {removed} 筆包含時間戳的行")

        # 3. 移除空行
        data = data.dropna(subset=['symbol'])
        data['symbol'] = data['symbol'].astype(str).str.strip()
        data = data[data['symbol'] != '']
        print(f"✓ 移除空行")

        # 4. 去重（每個標的只保留一筆）
        if 'symbol' in data.columns and 'broker' in data.columns:
            data = data.drop_duplicates(subset=['symbol', 'broker'], keep='last')
            print(f"✓ 去重（每個標的+經紀商只保留一筆）")

        # 5. 寫回 Google Sheets
        positions_list = data.to_dict('records')
        success = overwrite_broker_positions(positions_list)

        if success:
            print(f"\n✅ 自動修復成功！\n")
            return True
        else:
            print(f"\n❌ 寫入 Google Sheets 失敗\n")
            return False

    except Exception as e:
        print(f"❌ 自動修復失敗：{e}\n")
        return False


if __name__ == '__main__':
    validator = BrokerPositionsValidator()
    is_valid = validator.validate()

    if not is_valid:
        auto_fix_if_needed(validator)

    sys.exit(0)
