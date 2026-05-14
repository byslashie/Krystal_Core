"""
discord_bot.py
Krystal Discord Bot — 每日報告 + Claude AI 智能對話

Slash 指令：
  /今日報告  — 立即產生今日持倉報告
  /早報      — 立即產生早報（大盤 + 持倉 + 異動原因）
  /收盤      — 立即產生台股收盤結算報告
  /美股開盤  — 立即產生美股開盤 +5min 監控報告
  /同步      — 立即觸發 IB + Schwab 同步
  /庫存      — 查持倉清單
  /損益      — 查未實現損益
  /問 <問題> — 智能問答（Claude AI）

自動功能：
  - 每天 07:00 自動同步 IB + Schwab 持倉
  - 每天 08:00 自動發送早報（大盤 + 持倉 + 異動標的原因）
  - 每天 13:35 自動發送台股收盤結算（週末跳過）
  - 美股開盤 +5min 自動監控（夏令 21:35 / 冬令 22:35，週末跳過）

環境變數（.env）：
  DISCORD_BOT_TOKEN=
  DISCORD_CHANNEL_ID=   # 報告要發到哪個頻道的 ID
  ANTHROPIC_API_KEY=    # Claude API
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
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
TZ_US      = ZoneInfo("America/New_York")


def _is_us_dst() -> bool:
    """美東現在是否為夏令時間（EDT）。夏令: 3 月第二週日 → 11 月第一週日。"""
    return datetime.now(TZ_US).dst().total_seconds() != 0


def _us_open_taipei_time() -> time:
    """美股開盤對應台北時間：夏令 21:30，冬令 22:30。"""
    return time(21, 30, tzinfo=TZ) if _is_us_dst() else time(22, 30, tzinfo=TZ)


def _us_open_report_taipei_time() -> time:
    """美股開盤後 5 分鐘的台北時間（給 _build_us_open_report 用）：夏令 21:35，冬令 22:35。"""
    return time(21, 35, tzinfo=TZ) if _is_us_dst() else time(22, 35, tzinfo=TZ)

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
intents.message_content = True
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


# ── Broker 同步（07:00 用）──────────────────────────
def _run_sync_script(script_name: str, timeout: int = 180) -> tuple[bool, str]:
    """執行同步腳本，回傳 (成功, 訊息)"""
    script = PROJECT_ROOT / script_name
    if not script.exists():
        return False, f"找不到 {script_name}"
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, encoding="utf-8",
            timeout=timeout, cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return True, "已更新"
        err = (result.stderr or result.stdout or "").strip().splitlines()
        tail = err[-1] if err else "未知錯誤"
        return False, tail[:80]
    except subprocess.TimeoutExpired:
        return False, "逾時"
    except Exception as e:
        return False, str(e)[:80]


async def _run_morning_sync() -> str:
    """07:00 同步 IB + Schwab，回傳結果訊息"""
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    lines = [f"🔄 **早晨同步** `{now}`", "─" * 30]
    loop = asyncio.get_running_loop()

    ib_ok, ib_msg = await loop.run_in_executor(None, _run_sync_script, "sync_ib_to_sheets.py")
    lines.append(f"🇺🇸 IB ............ {'✅' if ib_ok else '❌'} {ib_msg}")

    sch_ok, sch_msg = await loop.run_in_executor(None, _run_sync_script, "sync_schwab_to_sheets.py")
    lines.append(f"🇺🇸 Schwab ........ {'✅' if sch_ok else '❌'} {sch_msg}")

    lines.append("🇹🇼 元大 .......... ⏸️ 跳過（09:15 之後再同步）")
    lines.append("")
    fail = sum(1 for ok in (ib_ok, sch_ok) if not ok)
    if fail:
        lines.append(f"⚠️ {fail} 個 broker 同步失敗，請手動檢查")
    else:
        lines.append("下次：08:00 推送早報")
    return "\n".join(lines)


# ── 大盤指數 ────────────────────────────────────────
INDEX_SYMBOLS = [
    ("🇹🇼 加權指數", "^TWII"),
    ("🇺🇸 S&P 500", "^GSPC"),
    ("🇺🇸 Nasdaq", "^IXIC"),
    ("🇺🇸 道瓊", "^DJI"),
]


# ── 代碼 → 中文名對照表 ─────────────────────────────
SYMBOL_NAMES = {
    # 台股 ETF
    "0050":   "元大台灣50",
    "006208": "富邦台50",
    "00631L": "元大台灣50正2",
    # 台股個股
    "2360": "致茂",
    "2383": "台光電",
    "3037": "欣興",
    "6515": "穎崴",
    "8046": "南電",
    "2330": "台積電",
    "3034": "聯詠",
    # 美股
    "ACWX": "ACWX全球除美ETF",
    "LITE": "Lumentum",
    "SNDK": "SanDisk",
    "NVDA": "輝達",
    "WDC":  "威騰電子",
    "QQQ":  "Nasdaq100",
    "TQQQ": "Nasdaq100三倍",
    "AAPL": "蘋果",
    "TSLA": "特斯拉",
    "MSFT": "微軟",
    "GOOGL": "Google",
    "AMZN": "亞馬遜",
    "META": "Meta",
}


def _name_of(symbol: str, yf_sym: str = "") -> str:
    """查代碼對應的中文名，先試原碼再試 yfinance 補零後的碼"""
    sym = str(symbol).strip().upper()
    if sym in SYMBOL_NAMES:
        return SYMBOL_NAMES[sym]
    # yf_sym 可能是 006208.TW，剝掉 .TW 再查
    if yf_sym:
        bare = yf_sym.replace(".TW", "").upper()
        if bare in SYMBOL_NAMES:
            return SYMBOL_NAMES[bare]
    return ""  # 沒對應就回空字串


def _yf_close_series(sym: str, period: str = "5d"):
    """統一抓單支 symbol 的 Close 序列；新版 yfinance 預設回 MultiIndex，這裡展平"""
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        hist = yf.download(sym, period=period, progress=False, auto_adjust=False, multi_level_index=False)
    except TypeError:
        # 舊版 yfinance 沒有 multi_level_index 參數
        hist = yf.download(sym, period=period, progress=False, auto_adjust=False)
        if hist is not None and hasattr(hist.columns, "nlevels") and hist.columns.nlevels > 1:
            hist.columns = hist.columns.get_level_values(0)
    except Exception:
        return None
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None
    return hist["Close"].dropna()


def _fetch_indices() -> list[dict]:
    """抓大盤指數最新價、漲跌幅"""
    out = []
    for label, sym in INDEX_SYMBOLS:
        close = _yf_close_series(sym)
        if close is None or len(close) < 2:
            continue
        try:
            last = float(close.iloc[-1])
            prev = float(close.iloc[-2])
        except Exception:
            continue
        chg = last - prev
        pct = (chg / prev * 100) if prev else 0.0
        out.append({"label": label, "symbol": sym, "last": last, "chg": chg, "pct": pct})
    return out


# ── 持股漲跌 + 新聞 ─────────────────────────────────
def _safe_float(v, default: float = 0.0) -> float:
    """空字串、None、非數字一律回 default"""
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _to_yf_symbol(symbol: str, broker: str) -> str:
    """把券商代碼轉成 yfinance 代碼。台股補前導 0 + 加 .TW"""
    sym = str(symbol).strip().upper()
    b = str(broker).strip()
    if b == "元大":
        # Sheet 把 0050、006208、00631L 開頭的 0 吃掉了。
        # 純數字：用 _resolve_tw_symbol 試 4 碼/6 碼擇優
        # 含字母（如 "631L"）：補到 6 碼
        if sym.isdigit():
            return _resolve_tw_symbol(sym)
        digits = "".join(c for c in sym if c.isdigit())
        letters = "".join(c for c in sym if c.isalpha())
        if digits and len(digits) + len(letters) < 6:
            sym = digits.zfill(6 - len(letters)) + letters
        return f"{sym}.TW"
    return sym


_tw_resolve_cache: dict[str, str] = {}


def _resolve_tw_symbol(digits: str) -> str:
    """純數字台股代碼 → yfinance 代碼。
    先試 4 碼補零（一般股票），抓不到再試 6 碼補零（ETF/權證）。"""
    if digits in _tw_resolve_cache:
        return _tw_resolve_cache[digits]
    candidates = []
    if len(digits) <= 4:
        candidates.append(digits.zfill(4))
    if len(digits) <= 6 and len(digits) != 4:
        candidates.append(digits.zfill(6))
    elif len(digits) == 4:
        candidates.append(digits.zfill(6))  # fallback: 6208 → 006208
    for c in candidates:
        full = f"{c}.TW"
        close = _yf_close_series(full, period="5d")
        if close is not None and len(close) >= 1:
            _tw_resolve_cache[digits] = full
            return full
    # 都抓不到就用第一個猜測
    fallback = f"{candidates[0] if candidates else digits}.TW"
    _tw_resolve_cache[digits] = fallback
    return fallback


def _fetch_quote_and_news(yf_sym: str, want_news: bool = False) -> dict:
    """抓個股最新收盤、前收、新聞標題（最多 3 條）"""
    info = {"symbol": yf_sym, "last": 0.0, "prev": 0.0, "pct": 0.0, "news": []}
    close = _yf_close_series(yf_sym)
    if close is not None and len(close) >= 2:
        try:
            info["last"] = float(close.iloc[-1])
            info["prev"] = float(close.iloc[-2])
            info["pct"]  = (info["last"] - info["prev"]) / info["prev"] * 100 if info["prev"] else 0.0
        except Exception:
            pass
    if want_news:
        try:
            import yfinance as yf
            t = yf.Ticker(yf_sym)
            raw = getattr(t, "news", None) or []
            titles = []
            for n in raw[:5]:
                title = n.get("title") or n.get("content", {}).get("title")
                if title:
                    titles.append(title)
                if len(titles) >= 3:
                    break
            info["news"] = titles
        except Exception:
            pass
    return info


# ── 免費中文翻譯（Google Translate via deep-translator）─────
_translator = None


def _get_translator():
    """Lazy init Google translator. 失敗回 None。"""
    global _translator
    if _translator is None:
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source="auto", target="zh-TW")
        except Exception as e:
            # 把錯誤詳情寫進 log，方便診斷（例如 module 找不到 / SSL 問題）
            try:
                log_path = PROJECT_ROOT / "logs" / "translate.log"
                log_path.parent.mkdir(exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')} [INIT ERROR {type(e).__name__}] {str(e)[:300]}\n")
            except Exception:
                pass
            _translator = False  # 標記初始化失敗，避免反覆嘗試
    return _translator if _translator is not False else None


def _translate_log(msg: str) -> None:
    """寫翻譯診斷 log 到檔案（pythonw 沒有 stdout）。"""
    try:
        log_path = PROJECT_ROOT / "logs" / "translate.log"
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _translate_to_zh(text: str) -> str:
    """把英文新聞標題翻成繁體中文。失敗或已是中文就回原字串。"""
    if not text:
        return text
    # 簡單判斷：若含 CJK 字元 > 30% 就視為中文，不翻
    cjk_count = sum(1 for c in text if "一" <= c <= "鿿")
    if cjk_count > len(text) * 0.3:
        return text
    t = _get_translator()
    if t is None:
        _translate_log(f"[init failed] {text[:50]}")
        return text
    try:
        result = t.translate(text)
        if result:
            _translate_log(f"[OK] {text[:40]} → {result[:40]}")
            return result
        _translate_log(f"[empty result] {text[:50]}")
        return text
    except Exception as e:
        _translate_log(f"[FAIL {type(e).__name__}] {str(e)[:80]} | {text[:50]}")
        return text


# ── 異動原因解釋（優先 Claude，沒設定就用 Google 翻譯）─────────────
def _explain_mover(symbol: str, name_hint: str, pct: float, headlines: list[str]) -> str:
    """請 Claude 用 2 行解釋為什麼大漲/大跌；沒設定 Claude 則用 Google 翻譯英文標題。"""
    claude = get_claude()

    # ── Claude 路徑（有 API key 才走）──
    if claude:
        direction = "大漲" if pct > 0 else "大跌"
        news_block = "\n".join(f"- {h}" for h in headlines) if headlines else "（無近期新聞）"
        prompt = (
            f"{symbol}（{name_hint}）今日{direction} {pct:+.2f}%。\n"
            f"最近新聞標題（可能是英文）：\n{news_block}\n\n"
            "請**全部用繁體中文**回答，2 行內，每行不超過 35 字。"
            "格式：第一行主因，第二行佐證或延伸。"
            "若新聞是英文請翻譯成中文，不要保留英文原句。"
            "不要開頭寒暄，直接寫原因。"
        )
        try:
            resp = claude.messages.create(
                model="claude-opus-4-6",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except Exception as e:
            # Claude 失敗 → fallback 到 Google 翻譯
            pass

    # ── Google 翻譯路徑（免費 fallback）──
    if not headlines:
        return "（無近期新聞）"
    # 取前 1-2 條標題，翻譯後組合
    top_headlines = headlines[:2]
    translated = []
    for h in top_headlines:
        zh = _translate_to_zh(h)
        translated.append(zh[:80])  # 限制單行長度
    return "\n".join(translated)


# ── 格式化今日報告 ────────────────────────────────
def _build_daily_report() -> str:
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    lines = [f"📊 **Krystal 每日持倉報告** `{now}`", ""]

    try:
        from sheets_utils import read_sheet_data_with_cache
        df = read_sheet_data_with_cache("broker_positions")
        positions = df.to_dict('records') if not df.empty else []
    except Exception as e:
        return f"讀取持倉失敗: {e}"

    if not positions:
        lines.append("⚠️ 目前無持倉資料，請確認同步狀態。")
        return "\n".join(lines)

    usd_rate = 32.0
    
    # 依據 broker 分組
    tw_positions = [p for p in positions if str(p.get("broker", "")).strip() == "元大"]
    ib_positions = [p for p in positions if str(p.get("broker", "")).strip().upper() == "IB"]
    schwab_positions = [p for p in positions if str(p.get("broker", "")).strip().lower() == "schwab"]
    
    # 台股（元大）
    if tw_positions:
        lines.append("🇹🇼 **台股（元大）**")
        lines.append("```")
        lines.append(f"{'代碼':<8} {'股數':>5}  {'均價':>7}  {'現價':>7}  {'損益':>9}  {'報酬率':>7}")
        lines.append("─" * 52)
        tw_total_mv = 0.0
        tw_total_pnl = 0.0
        for p in tw_positions:
            sym  = str(p.get("symbol", ""))
            qty  = int(float(p.get("position", 0)))
            avg  = float(p.get("avgCost", 0))
            mkt  = float(p.get("marketPrice", 0))
            pnl  = float(p.get("unrealizedPNL", 0))
            mv   = float(p.get("marketValue", 0))
            tw_total_mv += mv
            tw_total_pnl += pnl
            pct  = ((mkt - avg) / avg * 100) if avg > 0 else 0
            sign = "+" if pnl >= 0 else ""
            lines.append(f"{sym:<8} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {sign}{pnl:>8,.0f}  {sign}{pct:.1f}%")
        lines.append("─" * 52)
        pnl_sign = "+" if tw_total_pnl >= 0 else ""
        lines.append(f"{'合計':<8} {'':>5}  {'':>7}  {'':>7}  {pnl_sign}{tw_total_pnl:>8,.0f}")
        usd_val = tw_total_mv / usd_rate
        lines.append(f"總市值 NT${tw_total_mv:,.0f} (${usd_val:,.0f})")
        lines.append("```")
        lines.append("")

    # 美股（IB）
    if ib_positions:
        lines.append("🇺🇸 **美股（IB）**")
        lines.append("```")
        lines.append(f"{'代碼':<8} {'股數':>6}  {'均價':>8}  {'市值':>10}")
        lines.append("─" * 40)
        total_ib_mv_usd = 0.0
        for p in ib_positions:
            sym = str(p.get("symbol", ""))
            qty = float(p.get("position", 0))
            avg = float(p.get("avgCost", 0))
            mv  = float(p.get("marketValue", 0))
            total_ib_mv_usd += mv
            lines.append(f"{sym:<8} {qty:>6.0f}  {avg:>8.2f}  ${mv:>9,.2f}")
        lines.append("─" * 40)
        twd_val = total_ib_mv_usd * usd_rate
        lines.append(f"{'總市值':<8} {'':>6}  NT${twd_val:>8,.0f} (${total_ib_mv_usd:,.0f})")
        lines.append("```")
        lines.append("")

    # 美股（Schwab）
    if schwab_positions:
        lines.append("🇺🇸 **美股（Schwab）**")
        lines.append("```")
        lines.append(f"{'代碼':<8} {'股數':>6}  {'均價':>8}  {'市值':>10}")
        lines.append("─" * 40)
        total_schwab_mv_usd = 0.0
        for p in schwab_positions:
            sym = str(p.get("symbol", ""))
            qty = float(p.get("position", 0))
            avg = float(p.get("avgCost", 0))
            mv  = float(p.get("marketValue", 0))
            total_schwab_mv_usd += mv
            lines.append(f"{sym:<8} {qty:>6.0f}  {avg:>8.2f}  ${mv:>9,.2f}")
        lines.append("─" * 40)
        twd_val = total_schwab_mv_usd * usd_rate
        lines.append(f"{'總市值':<8} {'':>6}  NT${twd_val:>8,.0f} (${total_schwab_mv_usd:,.0f})")
        lines.append("```")
        lines.append("")

    # 今日 SOP 提示
    hour = datetime.now(TZ).hour
    if hour < 9:
        lines.append("⏰ 台股 09:00 開盤，請做好開盤前準備。")
    elif hour < 13:
        lines.append("📈 台股交易中，注意盤中異動。")
    elif 21 <= hour:
        lines.append("🌙 美股 21:30 開盤，注意持倉標的動向。")

    return "\n".join(lines)


# ── 08:00 早報（大盤 + 持倉 + 異動原因） ──────────
MOVER_THRESHOLD = 3.0  # 漲跌幅 ±3% 觸發異動解釋


def _build_morning_report() -> str:
    now_dt = datetime.now(TZ)
    weekday = "一二三四五六日"[now_dt.weekday()]
    now = now_dt.strftime("%Y-%m-%d") + f" (週{weekday}) " + now_dt.strftime("%H:%M")
    lines = [f"🌅 **Krystal 早報** `{now}`", ""]

    # ── 大盤 ────────────────────────────────
    indices = _fetch_indices()
    if indices:
        lines.append("═══ 🌐 **大盤** ═══")
        lines.append("```")
        for idx in indices:
            sign = "+" if idx["pct"] >= 0 else ""
            arrow = "🔴" if idx["pct"] >= 0 else "🟢"  # 台股慣例：紅漲綠跌
            lines.append(f"{idx['label']:<14} {idx['last']:>10,.2f}  {arrow}{sign}{idx['pct']:.2f}%  ({sign}{idx['chg']:,.1f})")
        lines.append("```")
        lines.append("")

    # ── 讀持倉 ──────────────────────────────
    try:
        from sheets_utils import read_sheet_data_with_cache
        df = read_sheet_data_with_cache("broker_positions")
        positions = df.to_dict('records') if not df.empty else []
    except Exception as e:
        lines.append(f"⚠️ 讀取持倉失敗：{e}")
        return "\n".join(lines)

    if not positions:
        lines.append("⚠️ 目前無持倉資料。")
        return "\n".join(lines)

    tw_positions     = [p for p in positions if str(p.get("broker", "")).strip() == "元大"]
    ib_positions     = [p for p in positions if str(p.get("broker", "")).strip().upper() == "IB"]
    schwab_positions = [p for p in positions if str(p.get("broker", "")).strip().lower() == "schwab"]

    movers: list[dict] = []  # 收集 ±3% 異動標的供 AI 解釋

    # ── 台股持倉（含當日漲跌）──────────────
    if tw_positions:
        lines.append("═══ 🇹🇼 **台股持倉** ═══")
        lines.append("```")
        lines.append(f"{'代碼':<7} {'名稱':<10} {'股數':>5}  {'均價':>7}  {'現價':>7}  {'今日%':>6}  {'損益':>9}")
        lines.append("─" * 64)
        tw_total_pnl = 0.0
        for p in tw_positions:
            sym = str(p.get("symbol", "")).strip()
            qty = int(_safe_float(p.get("position", 0)))
            avg = _safe_float(p.get("avgCost", 0))
            mkt = _safe_float(p.get("marketPrice", 0))
            pnl = _safe_float(p.get("unrealizedPNL", 0))
            tw_total_pnl += pnl
            yf_sym = _to_yf_symbol(sym, "元大")
            name = _name_of(sym, yf_sym)
            q = _fetch_quote_and_news(yf_sym, want_news=False)
            day_pct = q.get("pct", 0.0)
            tag = " 🚀" if day_pct >= MOVER_THRESHOLD else (" ⚠️" if day_pct <= -MOVER_THRESHOLD else "")
            sign = "+" if pnl >= 0 else ""
            psign = "+" if day_pct >= 0 else ""
            lines.append(f"{sym:<7} {name:<10} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {psign}{day_pct:>5.2f}%  {sign}{pnl:>8,.0f}{tag}")
            if abs(day_pct) >= MOVER_THRESHOLD:
                movers.append({"market": "TW", "symbol": sym, "yf": yf_sym, "name": name or sym, "pct": day_pct})
        lines.append("─" * 64)
        s = "+" if tw_total_pnl >= 0 else ""
        lines.append(f"{'合計':<7} {'':<10} {'':>5}  {'':>7}  {'':>7}  {'':>6}  {s}{tw_total_pnl:>8,.0f}")
        lines.append("```")
        lines.append("")

    # ── 美股（IB + Schwab 合併顯示）─────────
    us_positions = [(p, "IB") for p in ib_positions] + [(p, "Schwab") for p in schwab_positions]
    if us_positions:
        lines.append("═══ 🇺🇸 **美股（IB + Schwab）** ═══")
        lines.append("```")
        lines.append(f"{'代碼':<7} {'名稱':<14} {'券商':<7} {'股數':>5}  {'均價':>7}  {'現價':>7}  {'今日%':>6}  {'損益$':>8}")
        lines.append("─" * 76)
        us_total_pnl = 0.0
        for p, broker in us_positions:
            sym = str(p.get("symbol", "")).strip()
            qty = int(_safe_float(p.get("position", 0)))
            avg = _safe_float(p.get("avgCost", 0))
            mkt = _safe_float(p.get("marketPrice", 0))
            pnl = _safe_float(p.get("unrealizedPNL", 0))
            us_total_pnl += pnl
            yf_sym = _to_yf_symbol(sym, broker)
            name = _name_of(sym, yf_sym)
            q = _fetch_quote_and_news(yf_sym, want_news=False)
            day_pct = q.get("pct", 0.0)
            tag = " 🚀" if day_pct >= MOVER_THRESHOLD else (" ⚠️" if day_pct <= -MOVER_THRESHOLD else "")
            sign = "+" if pnl >= 0 else ""
            psign = "+" if day_pct >= 0 else ""
            lines.append(f"{sym:<7} {name:<14} {broker:<7} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {psign}{day_pct:>5.2f}%  {sign}{pnl:>7,.0f}{tag}")
            if abs(day_pct) >= MOVER_THRESHOLD:
                movers.append({"market": "US", "symbol": sym, "yf": yf_sym, "name": name or sym, "pct": day_pct})
        lines.append("─" * 76)
        s = "+" if us_total_pnl >= 0 else ""
        lines.append(f"{'合計':<7} {'':<14} {'':<7} {'':>5}  {'':>7}  {'':>7}  {'':>6}  {s}{us_total_pnl:>7,.0f}")
        lines.append("```")
        lines.append("")

    # ── 異動標的解釋（±3%）─────────────────
    if movers:
        lines.append("═══ 📰 **異動標的（>±3%）** ═══")
        lines.append("")
        for m in movers:
            q = _fetch_quote_and_news(m["yf"], want_news=True)
            headlines = q.get("news", [])
            emoji = "🚀" if m["pct"] > 0 else "⚠️"
            sign = "+" if m["pct"] >= 0 else ""
            explanation = _explain_mover(m["symbol"], m["name"], m["pct"], headlines)
            name_tag = f" {m['name']}" if m["name"] and m["name"] != m["symbol"] else ""
            lines.append(f"{emoji} **{m['symbol']}**{name_tag} {sign}{m['pct']:.2f}%")
            for ln in explanation.split("\n"):
                if ln.strip():
                    lines.append(f"  {ln.strip()}")
            lines.append("")

    # ── 今日提醒 ────────────────────────────
    us_open = _us_open_taipei_time().strftime("%H:%M")
    dst_tag = "（夏令 EDT）" if _is_us_dst() else "（冬令 EST）"
    lines.append("═══ 📅 **今日提醒** ═══")
    lines.append(f"🇹🇼 09:00 台股開盤  |  13:30 台股收盤  |  🇺🇸 {us_open} 美股開盤 {dst_tag}")

    return "\n".join(lines)


# ── 13:35 台股收盤報告 ─────────────────────────────
def _build_closing_report() -> str:
    """台股收盤後（13:35）的結算報告：今日台股大盤收盤、台股持倉當日 P&L、±3% 異動原因。"""
    now_dt = datetime.now(TZ)
    weekday = "一二三四五六日"[now_dt.weekday()]
    now = now_dt.strftime("%Y-%m-%d") + f" (週{weekday}) " + now_dt.strftime("%H:%M")
    lines = [f"🔔 **Krystal 台股收盤結算** `{now}`", ""]

    # ── 大盤（只看台股）──────────────────────
    indices = _fetch_indices()
    if indices:
        tw_idx = [i for i in indices if "TW" in i.get("symbol", "") or "台" in i.get("label", "")]
        if tw_idx:
            lines.append("═══ 🇹🇼 **台股大盤收盤** ═══")
            lines.append("```")
            for idx in tw_idx:
                sign = "+" if idx["pct"] >= 0 else ""
                arrow = "🔴" if idx["pct"] >= 0 else "🟢"
                lines.append(f"{idx['label']:<14} {idx['last']:>10,.2f}  {arrow}{sign}{idx['pct']:.2f}%  ({sign}{idx['chg']:,.1f})")
            lines.append("```")
            lines.append("")

    # ── 讀持倉 ──────────────────────────────
    try:
        from sheets_utils import read_sheet_data_with_cache
        df = read_sheet_data_with_cache("broker_positions")
        positions = df.to_dict('records') if not df.empty else []
    except Exception as e:
        lines.append(f"⚠️ 讀取持倉失敗：{e}")
        return "\n".join(lines)

    tw_positions = [p for p in positions if str(p.get("broker", "")).strip() == "元大"]
    if not tw_positions:
        lines.append("⚠️ 目前無台股持倉。")
        return "\n".join(lines)

    movers: list[dict] = []

    # ── 台股持倉今日結算 ─────────────────────
    lines.append("═══ 🇹🇼 **台股持倉今日結算** ═══")
    lines.append("```")
    lines.append(f"{'代碼':<7} {'名稱':<10} {'股數':>5}  {'均價':>7}  {'收盤':>7}  {'今日%':>6}  {'損益':>9}")
    lines.append("─" * 64)
    tw_total_pnl = 0.0
    tw_day_change = 0.0
    for p in tw_positions:
        sym = str(p.get("symbol", "")).strip()
        qty = int(_safe_float(p.get("position", 0)))
        avg = _safe_float(p.get("avgCost", 0))
        mkt = _safe_float(p.get("marketPrice", 0))
        pnl = _safe_float(p.get("unrealizedPNL", 0))
        tw_total_pnl += pnl
        yf_sym = _to_yf_symbol(sym, "元大")
        name = _name_of(sym, yf_sym)
        q = _fetch_quote_and_news(yf_sym, want_news=False)
        day_pct = q.get("pct", 0.0)
        day_chg = q.get("chg", 0.0)
        tw_day_change += day_chg * qty
        tag = " 🚀" if day_pct >= MOVER_THRESHOLD else (" ⚠️" if day_pct <= -MOVER_THRESHOLD else "")
        sign = "+" if pnl >= 0 else ""
        psign = "+" if day_pct >= 0 else ""
        lines.append(f"{sym:<7} {name:<10} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {psign}{day_pct:>5.2f}%  {sign}{pnl:>8,.0f}{tag}")
        if abs(day_pct) >= MOVER_THRESHOLD:
            movers.append({"market": "TW", "symbol": sym, "yf": yf_sym, "name": name or sym, "pct": day_pct})
    lines.append("─" * 64)
    s = "+" if tw_total_pnl >= 0 else ""
    ds = "+" if tw_day_change >= 0 else ""
    lines.append(f"{'累計':<7} {'':<10} {'':>5}  {'':>7}  {'':>7}  {'':>6}  {s}{tw_total_pnl:>8,.0f}")
    lines.append(f"{'今日':<7} {'':<10} {'':>5}  {'':>7}  {'':>7}  {'':>6}  {ds}{tw_day_change:>8,.0f}")
    lines.append("```")
    lines.append("")

    # ── 異動標的（±3%）─────────────────────
    if movers:
        lines.append("═══ 📰 **今日異動（>±3%）** ═══")
        lines.append("")
        for m in movers:
            q = _fetch_quote_and_news(m["yf"], want_news=True)
            headlines = q.get("news", [])
            emoji = "🚀" if m["pct"] > 0 else "⚠️"
            sign = "+" if m["pct"] >= 0 else ""
            explanation = _explain_mover(m["symbol"], m["name"], m["pct"], headlines)
            name_tag = f" {m['name']}" if m["name"] and m["name"] != m["symbol"] else ""
            lines.append(f"{emoji} **{m['symbol']}**{name_tag} {sign}{m['pct']:.2f}%")
            for ln in explanation.split("\n"):
                if ln.strip():
                    lines.append(f"  {ln.strip()}")
            lines.append("")

    # ── 接下來 ──────────────────────────────
    us_open = _us_open_taipei_time().strftime("%H:%M")
    lines.append("═══ 📅 **接下來** ═══")
    lines.append(f"🇺🇸 {us_open} 美股開盤  |  收盤後 5 分鐘將推送美股開盤監控")

    return "\n".join(lines)


# ── 美股開盤 +5min 報告 ────────────────────────────
def _build_us_open_report() -> str:
    """美股開盤後 5 分鐘的監控報告：美股大盤盤前/早盤、美股持倉開盤後漲跌、±3% 異動原因。"""
    now_dt = datetime.now(TZ)
    weekday = "一二三四五六日"[now_dt.weekday()]
    dst_tag = "EDT" if _is_us_dst() else "EST"
    now = now_dt.strftime("%Y-%m-%d") + f" (週{weekday}) " + now_dt.strftime("%H:%M") + f" 台北 / 美東 {dst_tag}"
    lines = [f"🌃 **Krystal 美股開盤監控** `{now}`", ""]

    # ── 美股大盤（早盤）──────────────────────
    indices = _fetch_indices()
    if indices:
        us_idx = [i for i in indices if "TW" not in i.get("symbol", "") and "台" not in i.get("label", "")]
        if us_idx:
            lines.append("═══ 🇺🇸 **美股大盤（開盤 +5min）** ═══")
            lines.append("```")
            for idx in us_idx:
                sign = "+" if idx["pct"] >= 0 else ""
                arrow = "🔴" if idx["pct"] >= 0 else "🟢"
                lines.append(f"{idx['label']:<14} {idx['last']:>10,.2f}  {arrow}{sign}{idx['pct']:.2f}%  ({sign}{idx['chg']:,.1f})")
            lines.append("```")
            lines.append("")

    # ── 讀持倉 ──────────────────────────────
    try:
        from sheets_utils import read_sheet_data_with_cache
        df = read_sheet_data_with_cache("broker_positions")
        positions = df.to_dict('records') if not df.empty else []
    except Exception as e:
        lines.append(f"⚠️ 讀取持倉失敗：{e}")
        return "\n".join(lines)

    ib_positions     = [p for p in positions if str(p.get("broker", "")).strip().upper() == "IB"]
    schwab_positions = [p for p in positions if str(p.get("broker", "")).strip().lower() == "schwab"]
    us_positions = [(p, "IB") for p in ib_positions] + [(p, "Schwab") for p in schwab_positions]

    if not us_positions:
        lines.append("⚠️ 目前無美股持倉。")
        return "\n".join(lines)

    movers: list[dict] = []

    # ── 美股持倉開盤後 ───────────────────────
    lines.append("═══ 🇺🇸 **美股持倉（開盤 +5min）** ═══")
    lines.append("```")
    lines.append(f"{'代碼':<7} {'名稱':<14} {'券商':<7} {'股數':>5}  {'均價':>7}  {'現價':>7}  {'今日%':>6}  {'損益$':>8}")
    lines.append("─" * 76)
    us_total_pnl = 0.0
    for p, broker in us_positions:
        sym = str(p.get("symbol", "")).strip()
        qty = int(_safe_float(p.get("position", 0)))
        avg = _safe_float(p.get("avgCost", 0))
        mkt = _safe_float(p.get("marketPrice", 0))
        pnl = _safe_float(p.get("unrealizedPNL", 0))
        us_total_pnl += pnl
        yf_sym = _to_yf_symbol(sym, broker)
        name = _name_of(sym, yf_sym)
        q = _fetch_quote_and_news(yf_sym, want_news=False)
        day_pct = q.get("pct", 0.0)
        tag = " 🚀" if day_pct >= MOVER_THRESHOLD else (" ⚠️" if day_pct <= -MOVER_THRESHOLD else "")
        sign = "+" if pnl >= 0 else ""
        psign = "+" if day_pct >= 0 else ""
        lines.append(f"{sym:<7} {name:<14} {broker:<7} {qty:>5}  {avg:>7.2f}  {mkt:>7.2f}  {psign}{day_pct:>5.2f}%  {sign}{pnl:>7,.0f}{tag}")
        if abs(day_pct) >= MOVER_THRESHOLD:
            movers.append({"market": "US", "symbol": sym, "yf": yf_sym, "name": name or sym, "pct": day_pct})
    lines.append("─" * 76)
    s = "+" if us_total_pnl >= 0 else ""
    lines.append(f"{'累計':<7} {'':<14} {'':<7} {'':>5}  {'':>7}  {'':>7}  {'':>6}  {s}{us_total_pnl:>7,.0f}")
    lines.append("```")
    lines.append("")

    # ── 異動標的（±3%）─────────────────────
    if movers:
        lines.append("═══ 📰 **開盤異動（>±3%）** ═══")
        lines.append("")
        for m in movers:
            q = _fetch_quote_and_news(m["yf"], want_news=True)
            headlines = q.get("news", [])
            emoji = "🚀" if m["pct"] > 0 else "⚠️"
            sign = "+" if m["pct"] >= 0 else ""
            explanation = _explain_mover(m["symbol"], m["name"], m["pct"], headlines)
            name_tag = f" {m['name']}" if m["name"] and m["name"] != m["symbol"] else ""
            lines.append(f"{emoji} **{m['symbol']}**{name_tag} {sign}{m['pct']:.2f}%")
            for ln in explanation.split("\n"):
                if ln.strip():
                    lines.append(f"  {ln.strip()}")
            lines.append("")

    return "\n".join(lines)


# ── 每日 07:00 同步 ───────────────────────────────
@tasks.loop(time=time(7, 0, tzinfo=TZ))
async def morning_sync():
    if CHANNEL_ID == 0:
        return
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    msg = await _run_morning_sync()
    for i in range(0, len(msg), 1900):
        await channel.send(msg[i:i+1900])


# ── 每日 08:00 早報 ───────────────────────────────
@tasks.loop(time=time(8, 0, tzinfo=TZ))
async def morning_report():
    if CHANNEL_ID == 0:
        return
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_morning_report)
    for i in range(0, len(report), 1900):
        await channel.send(report[i:i+1900])


# ── 每日 13:35 台股收盤結算 ────────────────────────
@tasks.loop(time=time(13, 35, tzinfo=TZ))
async def closing_report():
    if CHANNEL_ID == 0:
        return
    # 週六/週日跳過
    if datetime.now(TZ).weekday() >= 5:
        return
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_closing_report)
    for i in range(0, len(report), 1900):
        await channel.send(report[i:i+1900])


# ── 美股開盤 +5min 監控（夏令 21:35 / 冬令 22:35）──
# 兩個 loop 都註冊，每天執行時自己判斷是否該觸發
@tasks.loop(time=time(21, 35, tzinfo=TZ))
async def us_open_report_summer():
    """夏令時間版本（21:35）。若當天是冬令，則跳過。"""
    if not _is_us_dst():
        return
    await _send_us_open_report()


@tasks.loop(time=time(22, 35, tzinfo=TZ))
async def us_open_report_winter():
    """冬令時間版本（22:35）。若當天是夏令，則跳過。"""
    if _is_us_dst():
        return
    await _send_us_open_report()


async def _send_us_open_report():
    if CHANNEL_ID == 0:
        return
    # 美股週末休市：美東週六/週日跳過
    now_us = datetime.now(TZ_US)
    if now_us.weekday() >= 5:
        return
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_us_open_report)
    for i in range(0, len(report), 1900):
        await channel.send(report[i:i+1900])


# ── on_ready ─────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    morning_sync.start()
    morning_report.start()
    closing_report.start()
    us_open_report_summer.start()
    us_open_report_winter.start()
    us_open = _us_open_taipei_time().strftime("%H:%M")
    dst_tag = "EDT" if _is_us_dst() else "EST"
    print(f"[Bot] 上線：{client.user} | 頻道：{CHANNEL_ID}")
    print(f"[Bot] 排程：07:00 同步 / 08:00 早報 / 13:35 台股收盤 / {us_open} 美股開盤+5min ({dst_tag})")


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


# ── Slash: /早報 ──────────────────────────────────
@tree.command(name="早報", description="立即產生早報（大盤 + 持倉 + 異動原因）")
async def cmd_morning(interaction: discord.Interaction):
    await interaction.response.defer()
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_morning_report)
    for i in range(0, len(report), 1900):
        if i == 0:
            await interaction.followup.send(report[i:i+1900])
        else:
            await interaction.channel.send(report[i:i+1900])


# ── Slash: /收盤 ──────────────────────────────────
@tree.command(name="收盤", description="立即產生台股收盤結算報告")
async def cmd_closing(interaction: discord.Interaction):
    await interaction.response.defer()
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_closing_report)
    for i in range(0, len(report), 1900):
        if i == 0:
            await interaction.followup.send(report[i:i+1900])
        else:
            await interaction.channel.send(report[i:i+1900])


# ── Slash: /美股開盤 ──────────────────────────────
@tree.command(name="美股開盤", description="立即產生美股開盤 +5min 監控報告")
async def cmd_us_open(interaction: discord.Interaction):
    await interaction.response.defer()
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, _build_us_open_report)
    for i in range(0, len(report), 1900):
        if i == 0:
            await interaction.followup.send(report[i:i+1900])
        else:
            await interaction.channel.send(report[i:i+1900])


# ── Slash: /同步 ──────────────────────────────────
@tree.command(name="同步", description="立即觸發 IB + Schwab 同步")
async def cmd_sync(interaction: discord.Interaction):
    await interaction.response.defer()
    msg = await _run_morning_sync()
    for i in range(0, len(msg), 1900):
        if i == 0:
            await interaction.followup.send(msg[i:i+1900])
        else:
            await interaction.channel.send(msg[i:i+1900])


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
