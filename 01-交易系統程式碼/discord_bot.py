"""
discord_bot.py
Krystal Discord Bot — 支援 Slash Commands 查詢交易資訊

指令：
  /庫存   — 查元大最新持倉
  /損益   — 查未實現損益摘要
  /市值   — 查帳戶總市值
  /同步   — 手動觸發元大庫存更新

啟動方式：
  python discord_bot.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

TOKEN     = os.getenv("DISCORD_BOT_TOKEN", "")
SNAPSHOT  = PROJECT_ROOT / "data" / "yuanta_positions_snapshot.json"
UPLOAD_SCRIPT = PROJECT_ROOT / "brokers" / "upload_yuanta_to_sheets.py"
BAT_FILE  = PROJECT_ROOT / "sync_yuanta_09h15.bat"


# ──────────────────────────────────────────────
# Bot 設定
# ──────────────────────────────────────────────

intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"[Bot] 已上線：{client.user}  |  Slash Commands 已同步")


# ──────────────────────────────────────────────
# 讀取 snapshot
# ──────────────────────────────────────────────

def _load_snapshot() -> dict | None:
    if not SNAPSHOT.exists():
        return None
    try:
        return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except Exception:
        return None


# ──────────────────────────────────────────────
# /庫存
# ──────────────────────────────────────────────

@tree.command(name="庫存", description="查詢元大最新持倉")
async def cmd_positions(interaction: discord.Interaction):
    data = _load_snapshot()
    if not data:
        await interaction.response.send_message("找不到庫存資料，請先執行同步。")
        return

    positions = data.get("positions", [])
    ts        = data.get("timestamp", "")
    total_mv  = float(data.get("totalMarketValue", 0))
    total_pnl = float(data.get("totalUnrealizedPnL", 0))

    if not positions:
        await interaction.response.send_message("目前無持倉資料。")
        return

    rows = []
    for p in positions:
        sym  = str(p.get("symbol", ""))
        qty  = int(float(p.get("position", 0)))
        avg  = float(p.get("avgCost", 0))
        mkt  = float(p.get("currentPrice", 0))
        pnl  = float(p.get("unrealizedPnL", 0))
        sign = "+" if pnl >= 0 else ""
        rows.append(f"{sym:<7}{qty:>6}  {avg:>8.2f}  {mkt:>8.2f}  {sign}{pnl:>9.0f}")

    table    = "\n".join(rows)
    emoji    = "📈" if total_pnl >= 0 else "📉"
    pnl_sign = "+" if total_pnl >= 0 else ""

    msg = (
        f"{emoji} **元大持倉** `{ts}`\n"
        f"```\n"
        f"{'代碼':<7}{'股數':>6}  {'均價':>8}  {'現價':>8}  {'未實現':>9}\n"
        f"{'─'*44}\n"
        f"{table}\n"
        f"{'─'*44}\n"
        f"總市值     NT${total_mv:>12,.0f}\n"
        f"未實現損益  {pnl_sign}NT${abs(total_pnl):>11,.0f}\n"
        f"```"
    )
    await interaction.response.send_message(msg)


# ──────────────────────────────────────────────
# /損益
# ──────────────────────────────────────────────

@tree.command(name="損益", description="查詢各持股未實現損益")
async def cmd_pnl(interaction: discord.Interaction):
    data = _load_snapshot()
    if not data:
        await interaction.response.send_message("找不到庫存資料，請先執行同步。")
        return

    positions = data.get("positions", [])
    total_pnl = float(data.get("totalUnrealizedPnL", 0))
    ts        = data.get("timestamp", "")

    rows = []
    for p in sorted(positions, key=lambda x: float(x.get("unrealizedPnL", 0)), reverse=True):
        sym  = str(p.get("symbol", ""))
        avg  = float(p.get("avgCost", 0))
        mkt  = float(p.get("currentPrice", 0))
        pnl  = float(p.get("unrealizedPnL", 0))
        pct  = ((mkt - avg) / avg * 100) if avg > 0 else 0.0
        sign = "+" if pnl >= 0 else ""
        rows.append(f"{sym:<7}  {sign}{pnl:>9,.0f}  ({sign}{pct:.1f}%)")

    emoji    = "📈" if total_pnl >= 0 else "📉"
    pnl_sign = "+" if total_pnl >= 0 else ""

    msg = (
        f"{emoji} **未實現損益** `{ts}`\n"
        f"```\n"
        f"{'代碼':<7}  {'損益(NTD)':>9}  {'報酬率':>8}\n"
        f"{'─'*32}\n"
        f"{chr(10).join(rows)}\n"
        f"{'─'*32}\n"
        f"合計  {pnl_sign}NT${abs(total_pnl):>10,.0f}\n"
        f"```"
    )
    await interaction.response.send_message(msg)


# ──────────────────────────────────────────────
# /市值
# ──────────────────────────────────────────────

@tree.command(name="市值", description="查詢帳戶總市值摘要")
async def cmd_nav(interaction: discord.Interaction):
    data = _load_snapshot()
    if not data:
        await interaction.response.send_message("找不到庫存資料，請先執行同步。")
        return

    positions = data.get("positions", [])
    total_mv  = float(data.get("totalMarketValue", 0))
    total_pnl = float(data.get("totalUnrealizedPnL", 0))
    ts        = data.get("timestamp", "")
    emoji     = "📈" if total_pnl >= 0 else "📉"
    pnl_sign  = "+" if total_pnl >= 0 else ""

    rows = []
    for p in positions:
        sym = str(p.get("symbol", ""))
        mv  = float(p.get("marketValue", 0))
        pct = (mv / total_mv * 100) if total_mv > 0 else 0
        rows.append(f"{sym:<7}  NT${mv:>10,.0f}  ({pct:.1f}%)")

    msg = (
        f"{emoji} **帳戶市值** `{ts}`\n"
        f"```\n"
        f"{'代碼':<7}  {'市值':>12}  {'佔比':>6}\n"
        f"{'─'*34}\n"
        f"{chr(10).join(rows)}\n"
        f"{'─'*34}\n"
        f"總市值  NT${total_mv:>10,.0f}\n"
        f"未實現  {pnl_sign}NT${abs(total_pnl):>10,.0f}\n"
        f"```"
    )
    await interaction.response.send_message(msg)


# ──────────────────────────────────────────────
# /同步
# ──────────────────────────────────────────────

@tree.command(name="同步", description="手動觸發元大庫存同步（約需 1 分鐘）")
async def cmd_sync(interaction: discord.Interaction):
    await interaction.response.send_message("正在同步元大庫存，請稍候約 1 分鐘...")
    try:
        result = subprocess.run(
            ["cmd.exe", "/c", str(BAT_FILE)],
            capture_output=True, text=True, timeout=180,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            data = _load_snapshot()
            total_mv  = float(data.get("totalMarketValue", 0)) if data else 0
            total_pnl = float(data.get("totalUnrealizedPnL", 0)) if data else 0
            pnl_sign  = "+" if total_pnl >= 0 else ""
            await interaction.followup.send(
                f"同步完成！\n"
                f"總市值：NT${total_mv:,.0f}\n"
                f"未實現：{pnl_sign}NT${abs(total_pnl):,.0f}"
            )
        else:
            await interaction.followup.send(f"同步失敗（RC={result.returncode}）")
    except subprocess.TimeoutExpired:
        await interaction.followup.send("同步逾時，請稍後再試。")
    except Exception as e:
        await interaction.followup.send(f"同步錯誤：{e}")


# ──────────────────────────────────────────────
# 啟動
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] DISCORD_BOT_TOKEN 未設定")
        sys.exit(1)
    print("[Bot] 啟動中...")
    client.run(TOKEN)
