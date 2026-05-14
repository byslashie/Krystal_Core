"""
tw_macro_scraper.py — 台灣總經指標自動爬取
更新頻率：每月 1 次（景氣燈號/PMI 月度；央行利率季度）

資料來源：
  景氣燈號   → 國家發展委員會 (NDC) 開放資料 API
  台灣 PMI   → 中華經濟研究院 (CIER) 網站
  央行利率   → 中央銀行 (CBC) 網站

整合方式：
  被 macro_data.py 的 _load_sheets_overrides() 呼叫，
  自動取代 Google Sheets 手動輸入的 tw_light / tw_pmi / tw_rate。
"""

import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── 快取設定（24 小時，因為是月度/季度數據）─────────────────────
CACHE_DIR = Path(__file__).parent / "_cache"
TW_CACHE_FILE = CACHE_DIR / "tw_macro.json"
TW_CACHE_TTL_HOURS = 24


# ════════════════════════════════════════════════════════════════
# 快取工具
# ════════════════════════════════════════════════════════════════

def _load_tw_cache() -> Optional[dict]:
    """讀取台灣指標快取（24 小時內有效）"""
    if not TW_CACHE_FILE.exists():
        return None
    try:
        with open(TW_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=TW_CACHE_TTL_HOURS):
            logger.info(f"✅ 使用台灣指標快取（{cached_at.strftime('%m/%d %H:%M')} 更新）")
            return data
        logger.info("⏰ 台灣指標快取已過期，重新爬取")
    except Exception as e:
        logger.warning(f"讀取台灣快取失敗: {e}")
    return None


def _save_tw_cache(data: dict):
    """儲存台灣指標快取"""
    CACHE_DIR.mkdir(exist_ok=True)
    data["cached_at"] = datetime.now().isoformat()
    try:
        with open(TW_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("💾 台灣指標快取已儲存")
    except Exception as e:
        logger.warning(f"儲存台灣快取失敗: {e}")


# ════════════════════════════════════════════════════════════════
# 1. 景氣燈號 — 國家發展委員會 (NDC)
# ════════════════════════════════════════════════════════════════

# 景氣分數 → 燈號對照表
def _score_to_light(score: int) -> tuple[str, str, str]:
    """
    返回 (燈號emoji, 燈號名稱, CSS顏色變數)
    NDC 官方定義：
      ≥ 38  → 紅燈（景氣過熱）
      32-37 → 黃紅燈（景氣活絡）
      23-31 → 綠燈（景氣穩定）
      17-22 → 黃藍燈（景氣趨緩）
      ≤ 16  → 藍燈（景氣衰退）
    """
    if score >= 38:
        return "🔴", "紅燈", "var(--red)"
    elif score >= 32:
        return "🟠", "黃紅燈", "var(--yellow)"
    elif score >= 23:
        return "🟢", "綠燈", "var(--green)"
    elif score >= 17:
        return "🔵", "黃藍燈", "var(--accent)"
    else:
        return "🔵", "藍燈", "var(--accent)"


def _ndc_session_and_csrf(page_path: str) -> tuple:
    """建立 cloudscraper session 並從指定頁面取得 CSRF token。NDC 套了 Cloudflare + Laravel CSRF。"""
    import cloudscraper
    s = cloudscraper.create_scraper()
    r = s.get(f"https://index.ndc.gov.tw{page_path}", timeout=20)
    m = re.search(r'name="csrf-token"\s+content="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("NDC csrf-token 抓不到")
    return s, m.group(1)


def _ndc_post_json(session, csrf: str, endpoint: str, referer_path: str) -> dict:
    """對 NDC JSON endpoint 發 POST（XHR + CSRF）。"""
    r = session.post(
        f"https://index.ndc.gov.tw{endpoint}",
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": csrf,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://index.ndc.gov.tw{referer_path}",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def _ym_to_str(ym: str) -> str:
    """'202603' -> '2026-03'"""
    if isinstance(ym, str) and len(ym) == 6 and ym.isdigit():
        return f"{ym[:4]}-{ym[4:]}"
    return str(ym)


def fetch_ndc_business_light() -> Optional[dict]:
    """
    從 NDC 抓取最新景氣對策信號。
    端點：POST https://index.ndc.gov.tw/n/json/lightscore （需 cloudscraper + CSRF）
    回傳格式：{"line":[{"x":"YYYYMM","y":分數}], "next":"下次更新時間", ...}
    """
    try:
        s, csrf = _ndc_session_and_csrf("/n/zh_tw/lightscore")
        data = _ndc_post_json(s, csrf, "/n/json/lightscore", "/n/zh_tw/lightscore")
        line = data.get("line") or []
        if not line:
            logger.error("❌ NDC lightscore line 空")
            return None
        latest = line[-1]
        score = int(latest["y"])
        date_str = _ym_to_str(latest["x"])
        next_update = data.get("next")  # NDC 直接給「YYYY-MM-DD HH:MM」
        emoji, name, color = _score_to_light(score)
        logger.info(f"✅ NDC 景氣燈號 ({date_str})：{score} 分 → {name}，下次 {next_update}")
        return {
            "score": score,
            "light_name": name,
            "emoji": emoji,
            "color": color,
            "date": date_str,
            "next_update": next_update,
            "source": f"NDC ({date_str})",
        }
    except Exception as e:
        logger.error(f"❌ 景氣燈號爬取失敗: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# 2. 央行利率 — 中央銀行 (CBC)
# ════════════════════════════════════════════════════════════════

def fetch_cbc_rate() -> Optional[dict]:
    """
    從中央銀行網站抓取重貼現率（Discount Rate）。
    CBC 每季召開理監事會議決定利率，通常維持或調整 0.125%。
    頁面上格式：「重貼現率 2024-03-22 2%」
    """
    import cloudscraper
    from bs4 import BeautifulSoup

    try:
        s = cloudscraper.create_scraper()
        url = "https://www.cbc.gov.tw/tw/cp-302-927-CAF14-1.html"
        r = s.get(url, timeout=20)
        if r.status_code != 200:
            logger.warning(f"CBC 頁面 status={r.status_code}")
            return None
        text = BeautifulSoup(r.text, "html.parser").get_text(separator=" ")
        # 抓「重貼現率 YYYY-MM-DD X%」這種格式
        m = re.search(r'重貼現率\s+(\d{4}-\d{2}-\d{2})\s+(\d+(?:\.\d+)?)\s*%', text)
        if not m:
            # fallback：用反向格式 "X% 重貼現率"
            m = re.search(r'(\d+(?:\.\d+)?)\s*%[^0-9]{0,30}重貼現率', text)
            if m:
                rate = float(m.group(1))
                logger.info(f"✅ CBC 重貼現率：{rate}%（無日期）")
                return {
                    "rate": rate,
                    "date": datetime.now().strftime("%Y-%m"),
                    "source": "CBC 中央銀行",
                }
            logger.error("❌ CBC 頁面找不到重貼現率")
            return None
        date_str, rate_str = m.group(1), m.group(2)
        rate = float(rate_str)
        # YYYY-MM-DD -> YYYY-MM
        date_ym = date_str[:7]
        logger.info(f"✅ CBC 重貼現率 ({date_str})：{rate}%")
        return {
            "rate": rate,
            "date": date_ym,
            "source": f"CBC ({date_str} 調整)",
        }
    except Exception as e:
        logger.error(f"❌ CBC 央行利率爬取失敗: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# 3. 台灣製造業 PMI — 中華經濟研究院 (CIER)
# ════════════════════════════════════════════════════════════════

def fetch_tw_pmi() -> Optional[dict]:
    """
    從 NDC 抓取最新台灣製造業 PMI（季調值）。
    端點：POST https://index.ndc.gov.tw/n/json/PMI （需 cloudscraper + CSRF）
    回傳格式：{"right":{"55":{"lang":"製造業PMI(季調值)","d":[{"m":"YYYYMM","n":分數},...]}}}
    """
    try:
        s, csrf = _ndc_session_and_csrf("/n/zh_tw/data/PMI")
        data = _ndc_post_json(s, csrf, "/n/json/PMI", "/n/zh_tw/data/PMI")
        # 找 "製造業PMI(季調值)" 那一條
        right = data.get("right") or {}
        series = None
        for v in right.values():
            if "製造業PMI" in (v.get("lang") or "") and "季調" in v.get("lang", ""):
                series = v
                break
        if not series:
            # fallback：任何 PMI 開頭的
            for v in right.values():
                if "製造業PMI" in (v.get("lang") or ""):
                    series = v
                    break
        if not series or not series.get("d"):
            logger.error("❌ NDC PMI 找不到製造業 PMI 序列")
            return None
        latest = series["d"][-1]
        pmi = float(latest["n"])
        date_str = _ym_to_str(latest["m"])
        next_update = data.get("next")
        logger.info(f"✅ NDC 台灣製造業 PMI ({date_str})：{pmi}，下次 {next_update}")
        return {
            "pmi": pmi,
            "date": date_str,
            "next_update": next_update,
            "source": f"NDC ({date_str})",
        }
    except Exception as e:
        logger.error(f"❌ 台灣 PMI 爬取失敗: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# 主要接口：整合三個指標，回傳 macro_data.py 可直接使用的格式
# ════════════════════════════════════════════════════════════════

def get_tw_indicators(force_refresh: bool = False) -> dict:
    """
    取得台灣三大指標（景氣燈號 / PMI / 央行利率）。
    格式與 macro_data.py 的 MANUAL_OVERRIDES 相同，可直接合併。

    有快取則使用快取（24小時），過期或 force_refresh=True 時重新爬取。
    """
    if not force_refresh:
        cached = _load_tw_cache()
        if cached:
            return cached.get("indicators", {})

    result = {}
    errors = []

    # ── 景氣燈號 ───────────────────────────────────────────────
    light_data = fetch_ndc_business_light()
    if light_data:
        score = light_data["score"]
        emoji = light_data["emoji"]
        name = light_data["light_name"]
        color = light_data["color"]
        date = light_data["date"]
        result["tw_light"] = {
            "value":        f"{emoji} {name}",
            "label":        f"{score}分 → {name}",
            "signal":       f"{score}分 — 景氣{'熱絡' if score >= 32 else ('穩定' if score >= 23 else ('趨緩' if score >= 17 else '低迷'))}",
            "signal_color": color,
            "updated":      date,
            "next_update":  light_data.get("next_update"),
            "source":       light_data["source"],
            "is_scraped":   True,
        }
    else:
        errors.append("tw_light 爬取失敗")

    # ── 央行利率 ────────────────────────────────────────────────
    rate_data = fetch_cbc_rate()
    if rate_data:
        rate = rate_data["rate"]
        result["tw_rate"] = {
            "value":        f"{rate:.2f}%",
            "label":        f"{rate:.2f}% → {'升息' if rate > 2.0 else ('降息' if rate < 2.0 else '維持不變')}",
            "signal":       f"{rate:.2f}% — CBC {'升息' if rate > 2.0 else ('降息' if rate < 2.0 else '維持利率')}",
            "signal_color": "var(--red)" if rate > 2.5 else ("var(--yellow)" if rate >= 2.0 else "var(--green)"),
            "updated":      rate_data["date"],
            "next_update":  "下次理監事會議（季度）",
            "source":       rate_data["source"],
            "is_scraped":   True,
        }
    else:
        errors.append("tw_rate 爬取失敗")

    # ── 台灣 PMI ────────────────────────────────────────────────
    pmi_data = fetch_tw_pmi()
    if pmi_data:
        pmi = pmi_data["pmi"]
        if pmi >= 55:
            signal = f"{pmi:.1f} — 製造業強勁擴張"
            color = "var(--green)"
        elif pmi >= 50:
            signal = f"{pmi:.1f} — 製造業擴張"
            color = "var(--green)"
        elif pmi >= 45:
            signal = f"{pmi:.1f} — 製造業輕微收縮"
            color = "var(--yellow)"
        else:
            signal = f"{pmi:.1f} — 製造業收縮"
            color = "var(--red)"

        result["tw_pmi"] = {
            "value":        f"{pmi:.1f}",
            "label":        f"{pmi:.1f} → {'擴張' if pmi >= 50 else '收縮'}",
            "signal":       signal,
            "signal_color": color,
            "updated":      pmi_data["date"],
            "next_update":  pmi_data.get("next_update"),
            "source":       pmi_data["source"],
            "is_scraped":   True,
        }
    else:
        errors.append("tw_pmi 爬取失敗")

    # ── 儲存快取 ────────────────────────────────────────────────
    cache_data = {
        "indicators": result,
        "errors": errors,
        "scraped_at": datetime.now().isoformat(),
    }
    _save_tw_cache(cache_data)

    if errors:
        logger.warning(f"⚠️ 台灣指標爬取部分失敗: {errors}")

    logger.info(f"✅ 台灣指標爬取完成：{list(result.keys())}")
    return result


# ── 快速測試 ──────────────────────────────────────────────────
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print("\n=== 台灣總經指標爬取測試 ===\n")
    data = get_tw_indicators(force_refresh=True)
    for key, val in data.items():
        print(f"[{key}]")
        print(f"  value : {val.get('value')}")
        print(f"  signal: {val.get('signal')}")
        print(f"  source: {val.get('source')}")
        print()
