"""
上傳回測績效到 Google Sheets
掃描 02-策略知識庫/Strategies/**/Backtests/**/*.md
解析 YAML front matter → 寫入 strategy_performance 分頁

執行方式：
  python upload_backtest_to_sheets.py
  python upload_backtest_to_sheets.py --dry-run   # 只印出，不寫入 Sheets
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── 路徑設定 ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
STRATEGIES_DIR = BASE_DIR.parent / "02-策略知識庫" / "Strategies"

# ── Sheets 欄位定義（allocator.py 會用這些欄位）──────────────
HEADERS = [
    "strategy_id",       # S1, S2, S3...
    "strategy_name",     # 策略名稱（從資料夾名取）
    "version",           # v1.0, v1.10...
    "run_date",          # 回測執行日期
    "start_date",        # 回測起始日期
    "end_date",          # 回測結束日期
    "cagr_pct",          # 年化報酬率 %
    "sharpe",            # Sharpe Ratio
    "sortino",           # Sortino Ratio
    "mdd_pct",           # 最大回撤 %（負值）
    "calmar",            # Calmar Ratio
    "win_rate_pct",      # 勝率 %
    "trades",            # 交易次數
    "avg_profit_pct",    # 平均獲利 %
    "avg_loss_pct",      # 平均損失 %（負值）
    "ev_pct",            # 期望值 EV %
    "kelly_full",        # 凱利係數（全倉）
    "kelly_half",        # 凱利係數（半倉，建議用這個）
    "file_name",         # 來源檔名
    "uploaded_at",       # 上傳時間
]

# ── 策略 ID 對應（資料夾名稱前綴 → ID）────────────────────────
STRATEGY_ID_MAP = {
    "S1": "S1",
    "S2": "S2",
    "S3": "S3",
    "S4": "S4",
    "S5": "S5",
    "S6": "S6",
}


def parse_yaml_frontmatter(filepath: Path) -> dict:
    """從 .md 文件解析 YAML front matter（--- ... ---）"""
    content = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    raw = match.group(1)
    result = {}
    for line in raw.splitlines():
        # 跳過 tags list 的 - 開頭行
        if re.match(r"^\s+-\s", line):
            continue
        m = re.match(r"^(\w+):\s*(.*)", line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip().strip('"').strip("'")
            result[key] = val
    return result


def get_strategy_id(filepath: Path) -> str:
    """從檔案路徑找出策略 ID（S1–S6）"""
    for part in filepath.parts:
        for prefix, sid in STRATEGY_ID_MAP.items():
            if part.startswith(prefix + "-") or part == prefix:
                return sid
    return "S?"


def get_strategy_name(filepath: Path) -> str:
    """從資料夾名稱取策略名稱"""
    for part in filepath.parts:
        for prefix in STRATEGY_ID_MAP:
            if part.startswith(prefix + "-"):
                return part  # 例如 "S1-美股 ETF 輪動"
    return ""


def safe_float(val, default=None):
    """安全轉換為 float"""
    try:
        return round(float(val), 4) if val not in (None, "", "N/A") else default
    except (ValueError, TypeError):
        return default


def build_row(filepath: Path) -> dict:
    """從一個回測 .md 檔建構 Sheets 行資料"""
    fm = parse_yaml_frontmatter(filepath)
    if not fm:
        return {}

    strategy_id   = get_strategy_id(filepath)
    strategy_name = get_strategy_name(filepath)
    kelly_full    = safe_float(fm.get("kelly_full"))
    kelly_half    = round(kelly_full / 2, 4) if kelly_full else None

    return {
        "strategy_id":    strategy_id,
        "strategy_name":  strategy_name,
        "version":        fm.get("version", ""),
        "run_date":       fm.get("run_date", ""),
        "start_date":     fm.get("start_date", ""),
        "end_date":       fm.get("end_date", ""),
        "cagr_pct":       safe_float(fm.get("cagr_pct")),
        "sharpe":         safe_float(fm.get("sharpe")),
        "sortino":        safe_float(fm.get("sortino")),
        "mdd_pct":        safe_float(fm.get("mdd_pct")),
        "calmar":         safe_float(fm.get("calmar")),
        "win_rate_pct":   safe_float(fm.get("win_rate_pct")),
        "trades":         safe_float(fm.get("trades")),
        "avg_profit_pct": safe_float(fm.get("avg_profit_pct")),
        "avg_loss_pct":   safe_float(fm.get("avg_loss_pct")),
        "ev_pct":         safe_float(fm.get("ev_pct")),
        "kelly_full":     kelly_full,
        "kelly_half":     kelly_half,
        "file_name":      filepath.name,
        "uploaded_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def scan_backtest_files() -> list[Path]:
    """掃描所有回測 .md 文件"""
    if not STRATEGIES_DIR.exists():
        print(f"❌ 找不到策略目錄：{STRATEGIES_DIR}")
        return []

    files = []
    for f in STRATEGIES_DIR.rglob("*.md"):
        # 只抓 Backtests 資料夾內的文件
        if "Backtests" in f.parts or "backtests" in f.parts:
            files.append(f)

    return sorted(files)


def upload_to_sheets(rows: list[dict], dry_run: bool = False):
    """寫入 Google Sheets strategy_performance 分頁"""
    if dry_run:
        print("\n📋 [Dry Run] 以下資料將上傳到 strategy_performance：\n")
        for row in rows:
            print(f"  [{row['strategy_id']}] {row['strategy_name']} | {row['file_name']}")
            print(f"    CAGR={row['cagr_pct']}% | Sharpe={row['sharpe']} | MDD={row['mdd_pct']}% | 勝率={row['win_rate_pct']}% | Kelly½={row['kelly_half']}")
        return True

    try:
        sys.path.insert(0, str(BASE_DIR))
        import gspread
        from sheets_utils import get_workbook
        from dotenv import load_dotenv
        load_dotenv()

        wb = get_workbook()
        if wb is None:
            print("❌ 無法取得 Google Sheets 試算表")
            return False

        # 嘗試取得分頁，不存在則自動建立
        try:
            sheet = wb.worksheet("strategy_performance")
        except gspread.WorksheetNotFound:
            sheet = wb.add_worksheet(title="strategy_performance", rows=200, cols=len(HEADERS))
            print("📋 已自動建立 strategy_performance 分頁")

    except Exception as e:
        print(f"❌ 無法連接 Google Sheets：{e}")
        return False

    try:
        # 清空並重寫（含標題列）
        sheet.clear()
        header_row = HEADERS
        data_rows = [[row.get(h, "") for h in HEADERS] for row in rows]

        all_rows = [header_row] + data_rows
        sheet.update(all_rows, value_input_option="USER_ENTERED")

        print(f"✅ 成功上傳 {len(rows)} 筆回測績效到 strategy_performance 分頁")
        return True

    except Exception as e:
        print(f"❌ 上傳失敗：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="上傳回測績效到 Google Sheets")
    parser.add_argument("--dry-run", action="store_true", help="只印出，不寫入 Sheets")
    args = parser.parse_args()

    print(f"🔍 掃描目錄：{STRATEGIES_DIR}")
    files = scan_backtest_files()

    if not files:
        print("⚠️ 未找到任何回測文件（Backtests/**/*.md）")
        return

    print(f"📂 找到 {len(files)} 個回測文件：")
    rows = []
    for f in files:
        row = build_row(f)
        if row and row.get("cagr_pct") is not None:
            rows.append(row)
            print(f"  ✓ {row['strategy_id']} | {f.name}")
        else:
            print(f"  ⚠ 跳過（無有效 YAML）：{f.name}")

    if not rows:
        print("❌ 沒有可上傳的資料")
        return

    print(f"\n共 {len(rows)} 筆有效回測資料")
    upload_to_sheets(rows, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
