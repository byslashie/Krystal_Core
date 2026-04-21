#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
複製相關檔案到 dashboard_v8 資料夾
"""

import shutil
import os
from pathlib import Path

def copy_files():
    base_dir = Path(__file__).parent.absolute()
    dashboard_dir = base_dir / "dashboard_v8"

    # 建立 dashboard_v8 如果不存在
    dashboard_dir.mkdir(exist_ok=True)

    # 需要複製的檔案清單
    files_to_copy = [
        "strategy_sync_api.py",
        "sync_engine.py",
        "integrate_strategy_import.py",
        "strategy_import_page.html",
        "modules/strategyupload.py",
        "start_dashboard.py",
    ]

    print("\n" + "="*50)
    print("📁 複製檔案到 dashboard_v8")
    print("="*50 + "\n")

    for file_path in files_to_copy:
        src = base_dir / file_path
        if src.exists():
            # 為檔案建立目錄結構
            dst = dashboard_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(src, dst)
            print(f"✓ 複製: {file_path}")
        else:
            print(f"⚠️ 跳過 (不存在): {file_path}")

    print("\n" + "="*50)
    print("✅ 複製完成！")
    print("="*50 + "\n")

    print("📂 dashboard_v8 現在包含:")
    for item in sorted(dashboard_dir.rglob("*")):
        if item.is_file():
            rel_path = item.relative_to(dashboard_dir)
            print(f"  - {rel_path}")

if __name__ == "__main__":
    copy_files()
