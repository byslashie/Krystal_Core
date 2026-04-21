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
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── 快取設定（24 小時，因為是月度/季度數據）─────────────────────
CACHE_DIR = Path(__file__).parent / "_cache"
TW_CACHE_FILE = CACHE_DIR / "tw_macro.json"
TW_CACHE_TTL_HOURS = 24

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


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


def fetch_ndc_business_light() -> Optional[dict]:
    """
    從 NDC 開放資料 API 抓取最新景氣對策信號（景氣燈號）。
    API 文件：https://index.ndc.gov.tw/
    """
    # ── 嘗試 NDC JSON API ────────────────────────────────────────
    api_urls = [
        "https://index.ndc.gov.tw/api/zh_tw/a/7",   # 景氣對策信號
        "https://index.ndc.gov.tw/api/en/a/7",
    ]

    for url in api_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # NDC API 回傳格式：{ "data": [ {"date": "YYYY-MM", "score": 28, ...} ] }
                items = data if isinstance(data, list) else data.get("data", [])
                if items:
                    latest = items[-1]
                    score = latest.get("score") or latest.get("Score") or latest.get("value")
                    date_str = latest.get("date") or latest.get("Date") or latest.get("ym")
                    if score is not None:
                        score = int(score)
                        emoji, name, color = _score_to_light(score)
                        logger.info(f"✅ NDC 景氣燈號：{score} 分 → {name}")
                        return {
                            "score": score,
                            "light_name": name,
                            "emoji": emoji,
                            "color": color,
                            "date": date_str,
                            "source": f"NDC API ({date_str})",
                        }
        except Exception as e:
            logger.warning(f"NDC API ({url}) 失敗: {e}")

    # ── Fallback：爬取 NDC 網站 HTML ────────────────────────────
    try:
        from bs4 import BeautifulSoup
        url = "https://index.ndc.gov.tw/n/zh_tw"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            # 找「景氣對策信號」分數（通常是 2 位數）
            match = re.search(r'對策信號.*?(\d{2})\s*分', text) or \
                    re.search(r'綜合判斷分數.*?(\d{2})', text)
            if match:
                score = int(match.group(1))
                emoji, name, color = _score_to_light(score)
                logger.info(f"✅ NDC 網站爬取：景氣燈號 {score} 分 → {name}")
                month = datetime.now().strftime("%Y-%m")
                return {
                    "score": score,
                    "light_name": name,
                    "emoji": emoji,
                    "color": color,
                    "date": month,
                    "source": f"NDC 網站 (爬取 {month})",
                }
    except Exception as e:
        logger.warning(f"NDC 網站爬取失敗: {e}")

    logger.error("❌ 景氣燈號爬取失敗（所有來源）")
    return None


# ════════════════════════════════════════════════════════════════
# 2. 央行利率 — 中央銀行 (CBC)
# ════════════════════════════════════════════════════════════════

def fetch_cbc_rate() -> Optional[dict]:
    """
    從中央銀行網站抓取重貼現率（Discount Rate）。
    CBC 每季召開理監事會議決定利率，通常維持或調整 0.125%。
    """
    try:
        from bs4 import BeautifulSoup

        # CBC 利率政策頁面
        url = "https://www.cbc.gov.tw/tw/cp-302-927-CAF14-1.html"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ")

            # 搜尋「重貼現率」後面的數字
            match = re.search(
                r'重貼現率[^0-9]*(\d+\.\d+)',
                text
            )
            if match:
                rate = float(match.group(1))
                logger.info(f"✅ CBC 重貼現率：{rate}%")
                return {
                    "rate": rate,
                    "date": datetime.now().strftime("%Y-%m"),
                    "source": "CBC 中央銀行網站",
                }
    except Exception as e:
        logger.warning(f"CBC 網站爬取失敗: {e}")

    # ── Fallback：CBC 新聞稿 RSS ──────────────────────────────────
    try:
        from bs4 import BeautifulSoup
        url = "https://www.cbc.gov.tw/tw/np-1426-1.html"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            match = re.search(r'重貼現率維持[^0-9]*(\d+\.\d+)|重貼現率調整[^0-9]*(\d+\.\d+)', text)
            if match:
                rate = float(match.group(1) or match.group(2))
                logger.info(f"✅ CBC 新聞稿解析：重貼現率 {rate}%")
                return {
                    "rate": rate,
                    "date": datetime.now().strftime("%Y-%m"),
                    "source": "CBC 新聞稿",
                }
    except Exception as e:
        logger.warning(f"CBC 新聞稿爬取失敗: {e}")

    logger.error("❌ 央行利率爬取失敗（所有來源）")
    return None


# ════════════════════════════════════════════════════════════════
# 3. 台灣製造業 PMI — 中華經濟研究院 (CIER)
# ════════════════════════════════════════════════════════════════

def fetch_tw_pmi() -> Optional[dict]:
    """
    從中華經濟研究院抓取台灣製造業採購經理人指數（PMI）。
    每月第一個工作日發布。
    """
    try:
        from bs4 import BeautifulSoup

        # CIER PMI 新聞稿頁面
        url = "https://www.cier.edu.tw/news.aspx?n=168&sms=11476"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ")

            # 搜尋 PMI 數值（兩位數.一位小數）
            match = re.search(
                r'台灣製造業PMI.*?(\d{2}\.\d)|製造業PMI.*?(\d{2}\.\d)|PMI.*?指數.*?(\d{2}\.\d)',
                text[:3000]
            )
            if match:
                pmi = float(match.group(1) or match.group(2) or match.group(3))
                logger.info(f"✅ CIER 台灣製造業 PMI：{pmi}")
                return {
                    "pmi": pmi,
                    "date": datetime.now().strftime("%Y-%m"),
                    "source": "CIER 中華經濟研究院",
                }
    except Exception as e:
        logger.warning(f"CIER 網站爬取失敗: {e}")

    # ── Fallback：NDC 服務業 / 製造業 PMI ───────────────────────
    try:
        from bs4 import BeautifulSoup
        url = "https://index.ndc.gov.tw/n/zh_tw"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            match = re.search(r'製造業.*?PMI.*?(\d{2}\.\d)|PMI.*?(\d{2}\.\d)', text[:5000])
            if match:
                pmi = float(match.group(1) or match.group(2))
                logger.info(f"✅ NDC 台灣製造業 PMI：{pmi}")
                return {
                    "pmi": pmi,
                    "date": datetime.now().strftime("%Y-%m"),
                    "source": "NDC 國家發展委員會",
                }
    except Exception as e:
        logger.warning(f"NDC PMI 爬取失敗: {e}")

    logger.error("❌ 台灣 PMI 爬取失敗（所有來源）")
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
