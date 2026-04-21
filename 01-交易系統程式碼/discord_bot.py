"""
discord_bot.py
Krystal Discord Bot — 每日報告 + Claude AI 智能對話

Slash 指令：
  /今日報告  — 立即產生今日持倉報告
  /庫存      — 查持倉清單
  /損益      — 查未實現損益
  /問 <問題> — 智能問答（Claude AI）

自動功能：
  - 每天 09:00 自動發送今日報告

環境變數（.env）：
  DISCORD_BOT_TOKEN=
  DISCORD_CHANNEL_ID=   # 報告要發到哪個頻道的 ID
  ANTHROPIC_API_KEY=    # Claude API
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

TOKEN      = os.getenv("DISCORD_BOT_TOKEN", "")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SNAPSHOT   = PROJECT_ROOT / "data" / "yuanta_positions_snapshot.json"
TZ         = ZoneInfo("Asia/Taipei")

# ── Anthropic client（lazy import） ──────────────
_anthropic_client = None

def get_claude():
    global _anthropic_client
    if _anthropic_client is None and CLAUDE_KEY:
        try:
            import anthropic
            _anthropic_client = anthropic.Anthropic(api_key=CLAUDE_KEY)
        except ImportError:
            pass
    return _anthropic_client


# ── Bot 設定 ─────────────────────────────────────
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree   = app_commands.CommandTree(client)


# ── 讀取 snapshot ────────────────────────────────
def _load_snapshot() -> dict | None:
    try:
        if SNAPSHOT.exists():
            return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _load_schwab_positions() -> list[dict]:
    """嘗試從 schwab_api 取最新持倉"""
    try:
        from brokers.schwab_api import get_schwab_all_positions
        return get_schwab_all_positions()
    except Exception:
        return []


# ── 格式化今日報告 ────────────────────────────────
def _build_daily_report() -> str:
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 **Krystal 每日持倉報告** `{now}`", ""]

    # 台股（元大 snapshot）
    tw_data = _load_snapshot()
    tw_positions = tw_data.get("positions", []) if tw_data else []
    tw_total_mv  = float(tw_data.get("totalMarketValue", 0)) if tw_data else 0
    tw_total_pnl = float(tw_data.get("totalUnrealizedPnL", 0)) if tw_data else 0

    if tw_positions:
        lines.append("🇹🇼 **台股（元大）**")
        lines.append("```")
        lines.append(f"{'代碼':<8} {'股數':>5}  {'均價':>7}  {'現價':>7}  {'損益':>9}  {'報酬率':>7}")
        lines.append("─" * 52)
        for p in tw_positions:
            sym  = str(p.get("symbol", ""))
            qty  = int(float(p.get("position", 0)))
            avg  = float(p.get("avgCost", 0))
            mkt  = float(p.get("currentPrice", 0))
            pnl  = float(p.get("unrealizedPnL", 0))
            pct  = ((mkt - avg) / avg * 100) if avg > 0 else 0
            sign = "+" if pnl >= 0 else ""
            lines.append(f"{sym:<8} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {sign}{pnl:>8,.0f}  {sign}{pct:.1f}%")
        lines.append("─" * 52)
        pnl_sign = "+" if tw_total_pnl >= 0 else ""
        lines.append(f"{'合計':<8} {'':>5}  {'':>7}  {'':>7}  {pnl_sign}{tw_total_pnl:>8,.0f}")
        lines.append(f"總市值 NT${tw_total_mv:,.0f}")
        lines.append("```")
        lines.append("")

    # 美股（Schwab）
    us_positions = _load_schwab_positions()
    if us_positions:
        lines.append("🇺🇸 **美股（Schwab）**")
        lines.append("```")
        lines.append(f"{'代碼':<8} {'股數':>6}  {'均價':>8}  {'市值':>10}")
        lines.append("─" * 40)
        total_us_mv = 0.0
        for p in us_positions:
            sym = str(p.get("symbol", p.get("instrument", {}).get("symbol", "")))
            qty = float(p.get("longQuantity", p.get("quantity", 0)))
            avg = float(p.get("averagePrice", 0))
            mv  = float(p.get("marketValue", 0))
            total_us_mv += mv
            lines.append(f"{sym:<8} {qty:>6.0f}  {avg:>8.2f}  ${mv:>9,.2f}")
        lines.append("─" * 40)
        lines.append(f"{'總市值':<8} {'':>6}  {'':>8}  ${total_us_mv:>9,.2f}")
        lines.append("```")
        lines.append("")

    if not tw_positions and not us_positions:
        lines.append("⚠️ 目前無持倉資料，請確認同步狀態。")

    # 今日 SOP 提示
    hour = datetime.now(TZ).hour
    if hour < 9:
        lines.append("⏰ 台股 09:00 開盤，請做好開盤前準備。")
    elif hour < 13:
        lines.append("📈 台股交易中，注意盤中異動。")
    elif 21 <= hour:
        lines.append("🌙 美股 21:30 開盤，注意持倉標的動向。")

    return "\n".join(lines)


# ── 每日 09:00 自動報告 ───────────────────────────
@tasks.loop(time=time(9, 0, tzinfo=TZ))
async def daily_report():
    if CHANNEL_ID == 0:
        return
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    report = _build_daily_report()
    # Discord 訊息上限 2000 字，超過就切段
    for i in range(0, len(report), 1900):
        await channel.send(report[i:i+1900])


# ── on_ready ─────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    daily_report.start()
    print(f"[Bot] 上線：{client.user} | 每日報告頻道：{CHANNEL_ID}")


# ── Slash: /今日報告 ──────────────────────────────
@tree.command(name="今日報告", description="立即產生今日持倉報告")
async def cmd_today(interaction: discord.Interaction):
    await interaction.response.defer()
    report = _build_daily_report()
    for i in range(0, len(report), 1900):
        if i == 0:
            await interaction.followup.send(report[i:i+1900])
        else:
            await interaction.channel.send(report[i:i+1900])


# ── Slash: /庫存 ──────────────────────────────────
@tree.command(name="庫存", description="查詢最新持倉清單")
async def cmd_positions(interaction: discord.Interaction):
    await interaction.response.defer()
    data = _load_snapshot()
    if not data:
        await interaction.followup.send("找不到台股庫存資料，請先同步。")
        return
    positions = data.get("positions", [])
    ts = data.get("timestamp", "")
    rows = []
    for p in positions:
        sym = str(p.get("symbol", ""))
        qty = int(float(p.get("position", 0)))
        avg = float(p.get("avgCost", 0))
        mkt = float(p.get("currentPrice", 0))
        pnl = float(p.get("unrealizedPnL", 0))
        sign = "+" if pnl >= 0 else ""
        rows.append(f"{sym:<7} {qty:>5}  {avg:>8.2f}  {mkt:>8.2f}  {sign}{pnl:>9,.0f}")
    total_pnl = float(data.get("totalUnrealizedPnL", 0))
    total_mv  = float(data.get("totalMarketValue", 0))
    pnl_sign  = "+" if total_pnl >= 0 else ""
    msg = (
        f"📋 **持倉清單** `{ts}`\n"
        f"```\n{'代碼':<7} {'股數':>5}  {'均價':>8}  {'現價':>8}  {'未實現':>9}\n"
        f"{'─'*45}\n{chr(10).join(rows)}\n{'─'*45}\n"
        f"總市值  NT${total_mv:>12,.0f}\n"
        f"未實現  {pnl_sign}NT${abs(total_pnl):>11,.0f}\n```"
    )
    await interaction.followup.send(msg)


# ── Slash: /損益 ──────────────────────────────────
@tree.command(name="損益", description="查詢各持股未實現損益")
async def cmd_pnl(interaction: discord.Interaction):
    await interaction.response.defer()
    data = _load_snapshot()
    if not data:
        await interaction.followup.send("找不到庫存資料。")
        return
    positions = data.get("positions", [])
    total_pnl = float(data.get("totalUnrealizedPnL", 0))
    ts = data.get("timestamp", "")
    rows = []
    for p in sorted(positions, key=lambda x: float(x.get("unrealizedPnL", 0)), reverse=True):
        sym = str(p.get("symbol", ""))
        avg = float(p.get("avgCost", 0))
        mkt = float(p.get("currentPrice", 0))
        pnl = float(p.get("unrealizedPnL", 0))
        pct = ((mkt - avg) / avg * 100) if avg > 0 else 0.0
        sign = "+" if pnl >= 0 else ""
        rows.append(f"{sym:<7}  {sign}{pnl:>9,.0f}  ({sign}{pct:.1f}%)")
    emoji    = "📈" if total_pnl >= 0 else "📉"
    pnl_sign = "+" if total_pnl >= 0 else ""
    msg = (
        f"{emoji} **未實現損益** `{ts}`\n"
        f"```\n{'代碼':<7}  {'損益(NTD)':>9}  {'報酬率':>8}\n"
        f"{'─'*32}\n{chr(10).join(rows)}\n{'─'*32}\n"
        f"合計  {pnl_sign}NT${abs(total_pnl):>10,.0f}\n```"
    )
    await interaction.followup.send(msg)


# ── Slash: /問 ────────────────────────────────────
@tree.command(name="問", description="問 Krystal AI 任何交易問題")
@app_commands.describe(問題="你想問什麼？")
async def cmd_ask(interaction: discord.Interaction, 問題: str):
    await interaction.response.defer()

    claude = get_claude()
    if not claude:
        await interaction.followup.send("⚠️ Claude API 未設定（請在 .env 加入 ANTHROPIC_API_KEY）")
        return

    # 準備當前持倉作為 context
    context_lines = []
    tw_data = _load_snapshot()
    if tw_data:
        positions = tw_data.get("positions", [])
        total_pnl = float(tw_data.get("totalUnrealizedPnL", 0))
        total_mv  = float(tw_data.get("totalMarketValue", 0))
        context_lines.append(f"台股持倉：")
        for p in positions:
            sym = p.get("symbol", "")
            qty = int(float(p.get("position", 0)))
            avg = float(p.get("avgCost", 0))
            mkt = float(p.get("currentPrice", 0))
            pnl = float(p.get("unrealizedPnL", 0))
            pct = ((mkt - avg) / avg * 100) if avg > 0 else 0
            context_lines.append(f"  {sym}: {qty}股，均價{avg:.2f}，現價{mkt:.2f}，損益{pnl:+,.0f}（{pct:+.1f}%）")
        context_lines.append(f"台股總市值：NT${total_mv:,.0f}，未實現損益：NT${total_pnl:+,.0f}")

    context_str = "\n".join(context_lines) if context_lines else "目前無持倉資料"
    today = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

    system_prompt = f"""你是 Krystal 的個人交易助理，名字叫 Krystal AI。
現在時間：{today}（台北時間）

當前持倉狀況：
{context_str}

回答規則：
- 用繁體中文回答
- 簡潔清晰，重點先說
- 涉及具體數字時要精確
- 不要過度樂觀，風險要誠實說明
- 回答長度控制在 300 字以內"""

    try:
        response = claude.messages.create(
            model="claude-opus-4-6",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": 問題}]
        )
        answer = response.content[0].text
        await interaction.followup.send(f"🤖 **Krystal AI**\n{answer}")
    except Exception as e:
        await interaction.followup.send(f"❌ AI 回答失敗：{e}")


# ── 自然語言訊息對話（在頻道裡直接問） ────────────
@client.event
async def on_message(message: discord.Message):
    # 忽略 Bot 自己的訊息
    if message.author.bot:
        return
    # 只在被 @mention 或私訊時回應
    if client.user not in message.mentions and not isinstance(message.channel, discord.DMChannel):
        return

    content = message.content.replace(f"<@{client.user.id}>", "").strip()
    if not content:
        return

    claude = get_claude()
    if not claude:
        await message.reply("⚠️ Claude API 未設定")
        return

    async with message.channel.typing():
        tw_data = _load_snapshot()
        context_lines = []
        if tw_data:
            positions = tw_data.get("positions", [])
            total_pnl = float(tw_data.get("totalUnrealizedPnL", 0))
            total_mv  = float(tw_data.get("totalMarketValue", 0))
            for p in positions:
                sym = p.get("symbol", "")
                qty = int(float(p.get("position", 0)))
                avg = float(p.get("avgCost", 0))
                mkt = float(p.get("currentPrice", 0))
                pnl = float(p.get("unrealizedPnL", 0))
                pct = ((mkt - avg) / avg * 100) if avg > 0 else 0
                context_lines.append(f"  {sym}: {qty}股，均價{avg:.2f}，現價{mkt:.2f}，損益{pnl:+,.0f}（{pct:+.1f}%）")
            context_lines.append(f"台股總市值：NT${total_mv:,.0f}，未實現損益：NT${total_pnl:+,.0f}")

        context_str = "\n".join(context_lines) if context_lines else "目前無持倉資料"
        today = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

        system_prompt = f"""你是 Krystal 的個人交易助理，名字叫 Krystal AI。
現在時間：{today}（台北時間）

當前持倉狀況：
{context_str}

回答規則：
- 用繁體中文回答
- 簡潔清晰，重點先說
- 回答長度控制在 400 字以內"""

        try:
            response = claude.messages.create(
                model="claude-opus-4-6",
                max_tokens=800,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            answer = response.content[0].text
            await message.reply(f"🤖 {answer}")
        except Exception as e:
            await message.reply(f"❌ 回答失敗：{e}")


# ── 啟動 ─────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("[ERROR] 請在 .env 設定 DISCORD_BOT_TOKEN")
        sys.exit(1)
    if CHANNEL_ID == 0:
        print("[WARN] DISCORD_CHANNEL_ID 未設定，每日自動報告不會發送")
    print("[Bot] 啟動中...")
    client.run(TOKEN)
