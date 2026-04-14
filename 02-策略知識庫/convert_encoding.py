#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XQ 策略導入檔案編碼轉換工具
將 CSV/Excel 從 Big5/GB2312 等編碼轉換為 UTF-8
並驗證數據完整性
"""

import os
import sys
import chardet
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import csv

class EncodingConverter:
    """檔案編碼轉換器"""

    def __init__(self):
        self.supported_encodings = ['utf-8', 'big5', 'gb2312', 'cp1252', 'latin-1']
        self.detected_encoding = None

    def detect_encoding(self, file_path):
        """自動偵測檔案編碼"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(100000)  # 讀前100KB

            result = chardet.detect(raw_data)
            detected = result['encoding']
            confidence = result['confidence']

            print(f"📍 偵測到編碼: {detected} (信心度: {confidence*100:.1f}%)")
            self.detected_encoding = detected
            return detected
        except Exception as e:
            print(f"❌ 偵測失敗: {e}")
            return None

    def convert_csv(self, input_file, output_file=None, input_encoding=None):
        """轉換 CSV 檔案編碼"""
        if output_file is None:
            base = Path(input_file).stem
            output_file = f"{base}_UTF8.csv"

        try:
            print(f"\n📥 處理 CSV: {input_file}")

            # 偵測編碼
            if input_encoding is None:
                detected = self.detect_encoding(input_file)
                if detected:
                    input_encoding = detected
                else:
                    # 嘗試多個編碼
                    for enc in self.supported_encodings:
                        try:
                            df = pd.read_csv(input_file, encoding=enc, nrows=1)
                            input_encoding = enc
                            print(f"✅ 使用編碼: {enc}")
                            break
                        except:
                            continue

            if not input_encoding:
                print("❌ 無法偵測或轉換編碼")
                return None

            # 讀取文件
            print(f"📖 使用編碼 {input_encoding} 讀取...")
            df = pd.read_csv(input_file, encoding=input_encoding)

            # 驗證列數
            print(f"✅ 讀取成功: {len(df)} 行, {len(df.columns)} 列")
            print(f"   列名: {list(df.columns)[:5]}...")

            # 轉換為 UTF-8 並保存
            print(f"💾 轉換並保存為 UTF-8...")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')

            print(f"✅ 轉換完成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 轉換失敗: {e}")
            return None

    def convert_excel(self, input_file, output_file=None):
        """轉換 Excel 檔案編碼"""
        if output_file is None:
            base = Path(input_file).stem
            output_file = f"{base}_UTF8.xlsx"

        try:
            print(f"\n📥 處理 Excel: {input_file}")

            # 讀取 Excel
            print("📖 讀取 Excel 檔案...")
            df = pd.read_excel(input_file, engine='openpyxl')

            # 驗證
            print(f"✅ 讀取成功: {len(df)} 行, {len(df.columns)} 列")
            print(f"   列名: {list(df.columns)[:5]}...")

            # 保存為 UTF-8 編碼的新 Excel
            print(f"💾 轉換並保存為 UTF-8...")
            df.to_excel(output_file, index=False, engine='openpyxl')

            print(f"✅ 轉換完成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 轉換失敗: {e}")
            return None

    def validate_data(self, file_path, file_type='csv'):
        """驗證轉換後的數據完整性"""
        try:
            print(f"\n🔍 驗證數據完整性...")

            if file_type == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)

            # 基本驗證
            print(f"✅ 列數: {len(df.columns)}")
            print(f"✅ 行數: {len(df)}")
            print(f"✅ 無空白列: {not df.isnull().any().any()}")

            # 顯示列名
            print(f"\n📋 列名:")
            for i, col in enumerate(df.columns, 1):
                print(f"   {i:2d}. {col}")

            # 顯示前3行預覽
            print(f"\n📊 數據預覽 (前3行):")
            print(df.head(3).to_string())

            return df

        except Exception as e:
            print(f"❌ 驗證失敗: {e}")
            return None


def main():
    """主函數"""
    converter = EncodingConverter()

    print("=" * 60)
    print("XQ 策略導入 - 編碼轉換工具")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python convert_encoding.py <input_file> [output_file] [encoding]")
        print("\n範例:")
        print("  python convert_encoding.py strategy.csv")
        print("  python convert_encoding.py strategy.xlsx strategy_utf8.xlsx")
        print("  python convert_encoding.py strategy.csv output.csv big5")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    input_encoding = sys.argv[3] if len(sys.argv) > 3 else None

    # 檢查檔案是否存在
    if not os.path.exists(input_file):
        print(f"❌ 檔案不存在: {input_file}")
        return

    # 根據副檔名判斷類型
    if input_file.endswith('.csv'):
        converter.convert_csv(input_file, output_file, input_encoding)
        if output_file is None:
            base = Path(input_file).stem
            output_file = f"{base}_UTF8.csv"
    elif input_file.endswith('.xlsx') or input_file.endswith('.xls'):
        converter.convert_excel(input_file, output_file)
        if output_file is None:
            base = Path(input_file).stem
            output_file = f"{base}_UTF8.xlsx"
    else:
        print("❌ 不支援的檔案格式 (僅支援 .csv 和 .xlsx)")
        return

    # 驗證
    if os.path.exists(output_file):
        file_type = 'csv' if output_file.endswith('.csv') else 'excel'
        converter.validate_data(output_file, file_type)
        print("\n✅ 轉換完成！")
    else:
        print("\n❌ 轉換失敗")


if __name__ == "__main__":
    main()
