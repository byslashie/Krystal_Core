"""
modules/notifier.py
Krystal 統一 Discord 通知模組

用法：
    from modules.notifier import notify_yuanta_update, notify_daily_nav, notify_error

環境變數（.env）：
    DISCORD_WEBHOOK_YUANTA  — 主通知頻道 webhook URL
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    import urllib.request
    import json as _json  # noqa: F401

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_YUANTA", "")


# ──────────────────────────────────────────────
# 底層發送
# ──────────────────────────────────────────────

def _send(payload: dict[str, Any]) -> bool:
    if not WEBHOOK_URL:
        print("[notifier] DISCORD_WEBHOOK_YUANTA 未設定，跳過通知")
        return False
    try:
        if _HAS_REQUESTS:
            r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            ok = r.status_code in (200, 204)
        else:
            import json as _j
            data = _j.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                WEBHOOK_URL, data=data,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok = resp.status in (200, 204)
        if ok:
            print("[notifier] Discord OK")
        return ok
    except Exception as e:
        print(f"[notifier] 發送失敗：{e}")
        return False


# ──────────────────────────────────────────────
# 元大庫存更新通知
# ──────────────────────────────────────────────

def notify_yuanta_update(positions: list[dict], total_mv: float,
                         total_pnl: float, ts: str) -> bool:
    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    pnl_sign  = "+" if total_pnl >= 0 else ""

    rows = []
    for p in positions:
        sym  = str(p.get("symbol", ""))
        qty  = int(float(p.get("position", 0)))
        avg  = float(p.get("avgCost", 0))
        mkt  = float(p.get("currentPrice", 0))
        pnl  = float(p.get("unrealizedPnL", 0))
        sign = "+" if pnl >= 0 else ""
        rows.append(f"{sym:<7}{qty:>6}  {avg:>8.2f}  {mkt:>8.2f}  {sign}{pnl:>9.0f}")

    table = "\n".join(rows)
    content = (
        f"{pnl_emoji} **元大庫存更新** `{ts}`\n"
        f"```\n"
        f"{'代碼':<7}{'股數':>6}  {'均價':>8}  {'現價':>8}  {'未實現':>9}\n"
        f"{'─'*44}\n"
        f"{table}\n"
        f"{'─'*44}\n"
        f"總市值     NT${total_mv:>12,.0f}\n"
        f"未實現損益  {pnl_sign}NT${abs(total_pnl):>11,.0f}\n"
        f"```"
    )
    return _send({"content": content})


# ──────────────────────────────────────────────
# 每日 NAV 摘要通知
# ──────────────────────────────────────────────

def notify_daily_nav(date_str: str, yuanta_mv: float, yuanta_pnl: float,
                     ib_mv: float, ib_pnl: float,
                     schwab_mv: float = 0.0, schwab_pnl: float = 0.0,
                     usd_twd: float = 32.0) -> bool:
    total_mv_twd  = yuanta_mv + (ib_mv + schwab_mv) * usd_twd
    total_pnl_twd = yuanta_pnl + (ib_pnl + schwab_pnl) * usd_twd
    pnl_emoji = "📈" if total_pnl_twd >= 0 else "📉"

    def fmt_pnl(v): return f"{'+' if v>=0 else ''}{v:,.0f}"
    def fmt_usd(v): return f"{'+' if v>=0 else ''}{v:,.2f}"

    content = (
        f"{pnl_emoji} **每日市值記錄** `{date_str}`\n"
        f"```\n"
        f"券商     市值 (TWD)          未實現 (TWD)\n"
        f"{'─'*44}\n"
        f"元大     NT${yuanta_mv:>12,.0f}   {fmt_pnl(yuanta_pnl):>12}\n"
        f"IB       ${ib_mv:>9,.2f} USD        {fmt_usd(ib_pnl):>9} USD\n"
        f"         NT${ib_mv*usd_twd:>12,.0f}\n"
        f"Schwab   ${schwab_mv:>9,.2f} USD        {fmt_usd(schwab_pnl):>9} USD\n"
        f"         NT${schwab_mv*usd_twd:>12,.0f}\n"
        f"{'─'*44}\n"
        f"合計     NT${total_mv_twd:>12,.0f}   {fmt_pnl(total_pnl_twd):>12}\n"
        f"```"
    )
    return _send({"content": content})


# ──────────────────────────────────────────────
# 錯誤告警通知
# ──────────────────────────────────────────────

def notify_error(module: str, message: str) -> bool:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = (
        f"🚨 **系統錯誤** `{ts}`\n"
        f"```\n"
        f"模組：{module}\n"
        f"錯誤：{message}\n"
        f"```"
    )
    return _send({"content": content})


# ──────────────────────────────────────────────
# 排程事件通知（Step 1 完成、排程失敗等）
# ──────────────────────────────────────────────

def notify_sync_event(event: str, detail: str = "", ok: bool = True) -> bool:
    """
    排程同步事件通知
    event: 事件名稱，如 'Step1 snapshot 完成', '排程失敗'
    detail: 附加資訊
    ok: True=成功(✅), False=失敗(❌)
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = "✅" if ok else "❌"
    lines = [f"{emoji} **{event}** `{ts}`"]
    if detail:
        lines.append(f"```\n{detail}\n```")
    return _send({"content": "\n".join(lines)})


# ──────────────────────────────────────────────
# 風控告警通知
# ──────────────────────────────────────────────

def notify_risk_alert(rule: str, detail: str) -> bool:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = (
        f"⚠️ **風控觸發** `{ts}`\n"
        f"```\n"
        f"規則：{rule}\n"
        f"詳情：{detail}\n"
        f"```"
    )
    return _send({"content": content})


# ──────────────────────────────────────────────
# 策略訊號通知
# ──────────────────────────────────────────────

def notify_signal(strategy: str, action: str, symbol: str,
                  price: float, reason: str = "") -> bool:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = "🟢" if action.upper() in ("BUY", "買") else "🔴"
    content = (
        f"{emoji} **策略訊號** `{ts}`\n"
        f"```\n"
        f"策略：{strategy}\n"
        f"方向：{action}\n"
        f"標的：{symbol}  價格：{price:.2f}\n"
        f"{('原因：' + reason) if reason else ''}\n"
        f"```"
    )
    return _send({"content": content})
