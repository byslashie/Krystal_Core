"""
macro_data.py - 總經指標數據模組
從 FRED API 和 Yahoo Finance 抓取真實總經數據，並本地快取 6 小時。

支援的指標：
  US: ISM PMI, CPI YoY, NFP, Fed Rate, 10Y TIPS Real Rate, VIX
  TW: USD/TWD, (PMI/景氣燈號/央行利率 暫無免費 API，保留手動覆蓋)
  JP: USD/JPY, 日本 CPI (FRED: JPNCPIALLMINMEI)
  EU: EUR/USD, 歐元區 CPI (FRED: CP0000EZ19M086NEST)
  CN: USD/CNY (CNY=X)
  KR: USD/KRW (KRW=X)
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 快取設定
CACHE_DIR = Path(__file__).parent / "_cache"
CACHE_FILE = CACHE_DIR / "macro_indicators.json"
CACHE_TTL_HOURS = 6

# 本地 fallback：無免費 API 的指標預設值（Google Sheets 讀取失敗時使用）
MANUAL_OVERRIDES = {
    "ism_pmi":  {"value": "52.7", "label": "52.7 → 擴張", "signal": "52.7 — 製造業溫和擴張", "signal_color": "var(--green)", "updated": "2026-03"},
    "tw_pmi":   {"value": "55.4", "label": "55.4 → 強勁", "signal": "55.4 — 製造業強勁擴張", "signal_color": "var(--green)", "updated": "2026-03"},
    "tw_light": {"value": "🔴 紅燈", "label": "39分 → 紅燈", "signal": "39分 — 景氣熱絡 (連四紅)", "signal_color": "var(--red)", "updated": "2026-03"},
    "tw_rate":  {"value": "2.00%", "label": "2.00% → 維持不變", "signal": "2.00% — 央行維持利率", "signal_color": "var(--yellow)", "updated": "2026-03"},
    "jp_tankan": {"value": "14", "label": "14 → 正面", "signal": "14 — 製造業樂觀", "signal_color": "var(--green)", "updated": "2025-Q4"},
    "eu_pmi":    {"value": "48.9", "label": "48.9 → 收縮", "signal": "48.9 — 製造業仍收縮", "signal_color": "var(--red)", "updated": "2026-03"},
    "cn_pmi":    {"value": "50.2", "label": "50.2 → 擴張", "signal": "50.2 — 官方 PMI 持穩", "signal_color": "var(--green)", "updated": "2026-03"},
    "cn_rate":   {"value": "3.10%", "label": "3.10% → 寬鬆", "signal": "3.10% — PBoC 維持", "signal_color": "var(--yellow)", "updated": "2026-02"},
    "kr_export": {"value": "+5.3%", "label": "+5.3% → 成長", "signal": "+5.3% YoY — 出口回溫", "signal_color": "var(--green)", "updated": "2026-03"},
}

# Google Sheets 設定
_SHEET_ID = "1zpehl1bAZitFiQqMg7IcGWsPQxdhnQDhAeNtRvxzwn8"
_SHEET_TAB = "macro_manual"
_CREDS_FILE = Path(__file__).parent / "credentials.json"
_SHEETS_CACHE_FILE = CACHE_DIR / "macro_manual_sheets.json"
_SHEETS_CACHE_TTL_HOURS = 6


def _load_sheets_overrides() -> dict:
    """
    從 Google Sheets macro_manual 讀取手動覆蓋值。
    優先使用本地快取（6 小時），失敗時 fallback 到 MANUAL_OVERRIDES。
    """
    # 先嘗試讀快取
    if _SHEETS_CACHE_FILE.exists():
        try:
            with open(_SHEETS_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cached_at < timedelta(hours=_SHEETS_CACHE_TTL_HOURS):
                logger.info("✅ 使用 Sheets 快取覆蓋值")
                return cached.get("overrides", MANUAL_OVERRIDES)
        except Exception:
            pass

    # 嘗試從 Google Sheets 讀取
    if not _CREDS_FILE.exists():
        logger.warning("⚠️ credentials.json 不存在，使用本地 fallback")
        return MANUAL_OVERRIDES
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_file(
            str(_CREDS_FILE),
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        gc = gspread.authorize(creds)
        ws = gc.open_by_key(_SHEET_ID).worksheet(_SHEET_TAB)
        rows = ws.get_all_records()  # [{key, value, signal, signal_color, updated, note}, ...]

        overrides = {}
        for row in rows:
            key = str(row.get("key", "")).strip()
            if not key:
                continue
            val = str(row.get("value", "")).strip()
            overrides[key] = {
                "value":        val,
                "label":        f"{val}",
                "signal":       str(row.get("signal", val)).strip(),
                "signal_color": str(row.get("signal_color", "var(--text-muted)")).strip(),
                "updated":      str(row.get("updated", "")).strip(),
                "is_manual":    True,
                "source":       f"Google Sheets: macro_manual ({row.get('updated', '')})",
            }

        # 儲存快取
        CACHE_DIR.mkdir(exist_ok=True)
        with open(_SHEETS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "overrides": overrides}, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 從 Google Sheets 讀取 {len(overrides)} 筆手動覆蓋值")
        return overrides

    except Exception as e:
        logger.warning(f"⚠️ Google Sheets 讀取失敗，使用本地 fallback: {e}")
        return MANUAL_OVERRIDES


def _load_cache() -> Optional[dict]:
    """讀取本地快取（6 小時內有效）"""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            logger.info(f"✅ 使用快取數據 (更新於 {cached_at.strftime('%H:%M')})")
            return data
        logger.info("⏰ 快取已過期，重新抓取")
    except Exception as e:
        logger.warning(f"讀取快取失敗: {e}")
    return None


def _save_cache(data: dict):
    """儲存到本地快取"""
    CACHE_DIR.mkdir(exist_ok=True)
    data["cached_at"] = datetime.now().isoformat()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("💾 快取已更新")
    except Exception as e:
        logger.warning(f"儲存快取失敗: {e}")


def _fmt_pct(val, decimals=1) -> str:
    """格式化百分比"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}%"


def _fmt_num(val, decimals=1) -> str:
    """格式化數字"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def _fred_latest(fred, series_id: str, periods: int = 5) -> Optional[float]:
    """抓 FRED 最新非 NaN 值"""
    try:
        s = fred.get_series(series_id, observation_start="2024-01-01")
        s = s.dropna()
        if len(s) == 0:
            return None
        return float(s.iloc[-1])
    except Exception as e:
        logger.warning(f"FRED {series_id} 失敗: {e}")
        return None


def _fred_yoy(fred, series_id: str) -> Optional[float]:
    """計算 FRED 序列的 YoY %"""
    try:
        s = fred.get_series(series_id, observation_start="2023-01-01")
        s = s.dropna()
        if len(s) < 13:
            return None
        latest = float(s.iloc[-1])
        year_ago = float(s.iloc[-13])
        return round((latest - year_ago) / year_ago * 100, 2)
    except Exception as e:
        logger.warning(f"FRED YoY {series_id} 失敗: {e}")
        return None


def _fred_nfp_mom(fred) -> Optional[float]:
    """NFP 月增 (千人)"""
    try:
        s = fred.get_series("PAYEMS", observation_start="2024-01-01")
        s = s.dropna()
        if len(s) < 2:
            return None
        return round((float(s.iloc[-1]) - float(s.iloc[-2])) * 1000, 0)
    except Exception as e:
        logger.warning(f"FRED NFP 失敗: {e}")
        return None


def _yf_latest(ticker: str) -> Optional[float]:
    """Yahoo Finance 最新收盤價 (yfinance >= 1.0 用 download)"""
    try:
        import yfinance as yf
        hist = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1].iloc[0] if hasattr(hist["Close"].iloc[-1], 'iloc') else hist["Close"].iloc[-1])
    except Exception as e:
        logger.warning(f"yfinance {ticker} 失敗: {e}")
        return None


def _signal_ism(val) -> tuple[str, str]:
    if val is None:
        return "N/A", "var(--text-muted)"
    if val >= 55:
        return f"{val:.1f} — 製造業強勁擴張", "var(--green)"
    if val >= 50:
        return f"{val:.1f} — 製造業擴張", "var(--green)"
    if val >= 45:
        return f"{val:.1f} — 製造業輕微收縮", "var(--yellow)"
    return f"{val:.1f} — 製造業收縮", "var(--red)"


def _signal_cpi(val) -> tuple[str, str]:
    if val is None:
        return "N/A", "var(--text-muted)"
    if val <= 2.0:
        return f"{val:.1f}% — 通膨受控", "var(--green)"
    if val <= 3.0:
        return f"{val:.1f}% — 通膨偏高", "var(--yellow)"
    return f"{val:.1f}% — 通膨超標", "var(--red)"


def _signal_vix(val) -> tuple[str, str]:
    if val is None:
        return "N/A", "var(--text-muted)"
    if val < 20:
        return f"{val:.1f} — 市場平靜", "var(--green)"
    if val < 30:
        return f"{val:.1f} — 輕微恐慌", "var(--yellow)"
    return f"{val:.1f} — 高度恐慌", "var(--red)"


def _signal_real_rate(val) -> tuple[str, str]:
    if val is None:
        return "N/A", "var(--text-muted)"
    if val >= 2.0:
        return f"{val:.2f}% — 實質利率偏高，抑制風險資產", "var(--red)"
    if val >= 1.0:
        return f"{val:.2f}% — 實質利率中性偏緊", "var(--yellow)"
    return f"{val:.2f}% — 實質利率寬鬆，有利股市", "var(--green)"


def _signal_fed_rate(val) -> tuple[str, str]:
    if val is None:
        return "N/A", "var(--text-muted)"
    if val >= 5.0:
        return f"{val:.2f}% — 高利率環境", "var(--red)"
    if val >= 3.0:
        return f"{val:.2f}% — 利率正常化", "var(--yellow)"
    return f"{val:.2f}% — 低利率環境", "var(--green)"


def _analysis_fed_rate(val) -> str:
    if val is None:
        return "無法取得 Fed 利率數據。"
    if val >= 5.25:
        return (f"當前 {val:.2f}%，處於本輪緊縮週期高點，Fed 維持高利率。"
                "市場密切關注 FOMC 會議，降息時程取決於通膨與就業數據。"
                "高利率持續壓縮成長股估值，金融股因息差擴大相對受益。")
    if val >= 5.0:
        return (f"當前 {val:.2f}%，仍處於限制性利率水準。"
                "Fed 已暗示升息週期接近尾聲，市場開始預期未來降息，但時程仍不確定。"
                "建議關注 CME FedWatch 工具追蹤市場降息機率。")
    if val >= 4.0:
        return (f"當前 {val:.2f}%，Fed 已啟動降息，利率從高點回落。"
                "降息初期有利成長股和債券，資金面逐步轉鬆。"
                "需觀察降息節奏是否符合市場預期，若低於預期則市場可能修正。")
    if val >= 3.0:
        return (f"當前 {val:.2f}%，利率已正常化至中性水準附近。"
                "資金成本下降，有利股市估值擴張，尤其科技、成長股。"
                "台美利差縮小，有助外資回流台股。")
    return (f"當前 {val:.2f}%，處於低利率環境，資金寬鬆。"
            "股市估值易擴張，但需注意通膨是否因此重燃。"
            "低利率通常有利房地產、高股息股票。")


def _analysis_vix(val) -> str:
    if val is None:
        return "無法取得 VIX 數據。"
    if val < 15:
        return (f"當前 {val:.1f}，市場極度平靜，投資人過度樂觀。"
                "VIX 處於歷史低位，往往是 Black Swan 風險悄悄積累的時期。"
                "建議保持適度避險，勿在此時過度加槓桿。")
    if val < 20:
        return (f"當前 {val:.1f}，處於正常波動區間，市場情緒穩定。"
                "VIX 未出現異常飆升，系統性風險目前受控。"
                "可正常持倉，留意若 VIX 突然從低位飆升 > 25 需減倉應對。")
    if val < 25:
        return (f"當前 {val:.1f}，市場不確定性上升，進入輕度警戒。"
                "投資人開始對沖風險，期權保護需求增加。"
                "建議檢視持倉集中度，高 Beta 部位可適度減少。")
    if val < 35:
        return (f"當前 {val:.1f}，市場恐慌情緒升溫，波動明顯加劇。"
                "此區間需謹慎，可考慮降低整體倉位或使用 VIX call 對沖。"
                "歷史上 VIX > 30 後往往是分批布局的機會，但需確認系統性風險未擴大。")
    return (f"當前 {val:.1f}，市場極度恐慌（金融危機等級）。"
            "這通常是歷史上絕佳的反向分批進場時機，但需分批、控制倉位。"
            "確認事件是否為系統性危機（如 2008/2020）再決定操作力度。")


def _analysis_real_rate(val) -> str:
    if val is None:
        return "無法取得實質利率數據。"
    if val >= 2.5:
        return (f"當前 {val:.2f}%，實質利率顯著偏高，金融條件緊縮。"
                "歷史上此水準對 NASDAQ 成長股、黃金均形成壓力。"
                "等待 Fed 降息或通膨上升才能讓實質利率回落，屆時成長股可望反彈。")
    if val >= 1.5:
        return (f"當前 {val:.2f}%，實質利率偏高，抑制風險資產。"
                "成長股 DCF 折現率高，估值承壓。黃金缺乏多頭催化劑。"
                "若 CPI 持續降溫或 Fed 降息，實質利率下行有利布局成長股。")
    if val >= 0.5:
        return (f"當前 {val:.2f}%，實質利率中性，金融條件不鬆不緊。"
                "股市整體環境尚可，成長股與價值股均可參與。"
                "黃金在此區間多為橫盤整理。")
    return (f"當前 {val:.2f}%，實質利率偏低或為負，資金寬鬆。"
            "有利成長股估值擴張，黃金通常表現強勁。"
            "注意負實質利率環境可能帶來資產泡沫風險。")


def _analysis_us_cpi(val) -> str:
    if val is None:
        return "無法取得 CPI 數據。"
    if val > 5.0:
        return (f"當前 {val:.1f}%，通膨嚴重超標，Fed 將持續升息。"
                "高通膨直接壓縮消費者購買力，企業成本上升，股市承壓。"
                "需等待明確的通膨轉折訊號再考慮加倉。")
    if val > 3.0:
        return (f"當前 {val:.1f}%，高於 Fed 目標 2%，通膨黏著。"
                "服務業通膨（房租、薪資）是主要黏著項目，難以快速降至目標。"
                "Fed 降息時程因此延後，高利率環境持續，成長股估值承壓。")
    if val > 2.0:
        return (f"當前 {val:.1f}%，接近但仍高於 Fed 目標 2%。"
                "通膨趨勢向下，Fed 有條件考慮降息。"
                "市場對降息預期升溫，成長股和債券可逐步布局。")
    return (f"當前 {val:.1f}%，通膨受控，達到 Fed 目標區間。"
            "Fed 有充分空間降息，資金面轉鬆，股市估值易擴張。"
            "此時通常為多頭友善環境，可積極參與。")


def _analysis_nfp(val_k) -> str:
    """val_k 單位為千人"""
    if val_k is None:
        return "無法取得 NFP 數據。"
    if val_k > 250:
        return (f"當前 +{val_k:.0f}K，就業市場極度強勁，遠超預期。"
                "強勁就業 = 消費力強 = 通膨難降 = Fed 降息時程延後。"
                "短期對股市偏負面（Fed 鷹派），但長期反映經濟體質良好。")
    if val_k > 150:
        return (f"當前 +{val_k:.0f}K，就業市場穩健，接近健康增長水準。"
                "就業溫和增長有利消費，Fed 可能在通膨受控後啟動降息。"
                "整體為市場中性偏正面訊號。")
    if val_k > 0:
        return (f"當前 +{val_k:.0f}K，就業增長放緩，低於市場預期水準。"
                "就業轉溫支持 Fed 降息預期，債券和成長股通常受益。"
                "需持續觀察是否進一步惡化為負成長。")
    return (f"當前 {val_k:.0f}K，就業出現負成長，顯示經濟明顯放緩。"
            "Fed 降息壓力大增，但若為衰退預兆，股市整體可能仍承壓。"
            "密切關注後續月份是否持續惡化。")


def _analysis_usd_twd(val) -> str:
    if val is None:
        return "無法取得台幣匯率數據。"
    if val > 33:
        return (f"當前 {val:.2f}，台幣大幅貶值。"
                "出口導向科技股（台積電、聯電等）匯兌收益顯著增加。"
                "外資持有台股角度，台幣弱使美元計價報酬打折，外資減碼動機強。"
                "央行若持續干預，需注意政策風險。")
    if val > 32:
        return (f"當前 {val:.2f}，台幣偏弱，台美利差擴大是主因。"
                "出口商因匯兌利益受惠，進口原物料成本上升。"
                "央行通常在 31.5-32.5 區間進行隱性干預。"
                "若 Fed 降息，利差縮小，台幣將有升值壓力。")
    if val > 31:
        return (f"當前 {val:.2f}，台幣處於中性區間。"
                "匯率對台股影響中性，外資進出主要取決於基本面。"
                "密切追蹤外資買賣超作為台幣走向的先行指標。")
    return (f"當前 {val:.2f}，台幣偏強，有利外資回流台股。"
            "台幣升值環境下，外資持有台股的美元計價報酬改善。"
            "進口商受益，出口科技業匯兌收益減少，但通常基本面更重要。")


def fetch_macro_data(force_refresh: bool = False) -> dict:
    """
    抓取所有總經指標數據。
    優先使用快取，快取過期或 force_refresh=True 時重新抓取。
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    result = {"source": "live", "indicators": {}, "errors": []}

    # ── FRED API ──────────────────────────────────────────────────
    fred_key = os.getenv("FRED_API_KEY", "")
    fred = None
    if fred_key:
        try:
            from fredapi import Fred
            fred = Fred(api_key=fred_key)
            logger.info("✅ FRED API 初始化成功")
        except Exception as e:
            result["errors"].append(f"FRED 初始化失敗: {e}")
            logger.warning(f"FRED 初始化失敗: {e}")
    else:
        result["errors"].append("FRED_API_KEY 未設定，跳過 FRED 指標")
        logger.warning("⚠️ FRED_API_KEY 未設定")

    # ISM PMI — FRED 無此系列，從 Google Sheets macro_manual 讀取
    # 如需更新：直接修改 Google Sheets 的 macro_manual 表單

    # US CPI YoY
    us_cpi = None
    if fred:
        us_cpi = _fred_yoy(fred, "CPIAUCSL")
    cpi_signal, cpi_color = _signal_cpi(us_cpi)

    result["indicators"]["us_cpi"] = {
        "value": _fmt_pct(us_cpi) if us_cpi else "N/A",
        "label": f"{_fmt_pct(us_cpi)} → {'偏高' if us_cpi and us_cpi > 2.5 else '受控'}" if us_cpi else "N/A",
        "signal": cpi_signal,
        "signal_color": cpi_color,
        "source": "FRED: CPIAUCSL",
        "analysis": _analysis_us_cpi(us_cpi),
    }

    # NFP 月增 (千人)
    nfp_val = None
    if fred:
        nfp_val = _fred_nfp_mom(fred)
    nfp_k = round(nfp_val / 1000) if nfp_val else None
    nfp_signal = f"+{nfp_k:.0f}K — 就業強勁" if nfp_k and nfp_k > 150 else (f"+{nfp_k:.0f}K — 就業溫和" if nfp_k and nfp_k > 0 else (f"{nfp_k:.0f}K — 就業轉弱" if nfp_k else "N/A"))
    nfp_color = "var(--green)" if nfp_k and nfp_k > 150 else ("var(--yellow)" if nfp_k and nfp_k > 0 else "var(--red)")

    result["indicators"]["nfp"] = {
        "value": f"+{nfp_k:.0f}K" if nfp_k and nfp_k > 0 else (f"{nfp_k:.0f}K" if nfp_k else "N/A"),
        "label": f"{'+' if nfp_k and nfp_k > 0 else ''}{nfp_k:.0f}K → {'強勁' if nfp_k and nfp_k > 150 else '溫和'}" if nfp_k else "N/A",
        "signal": nfp_signal,
        "signal_color": nfp_color,
        "source": "FRED: PAYEMS (非農就業人數月增)",
        "analysis": _analysis_nfp(nfp_k),
    }

    # Fed Rate (FEDFUNDS = 聯邦基金利率月均)
    fed_val = None
    if fred:
        fed_val = _fred_latest(fred, "FEDFUNDS")
    fed_signal, fed_color = _signal_fed_rate(fed_val)

    result["indicators"]["fed_rate"] = {
        "value": _fmt_pct(fed_val, 2) if fed_val else "N/A",
        "label": f"{_fmt_pct(fed_val, 2)} → 維持" if fed_val else "N/A",
        "signal": fed_signal,
        "signal_color": fed_color,
        "source": "FRED: FEDFUNDS",
        "analysis": _analysis_fed_rate(fed_val),
    }

    # 10Y TIPS Real Rate (DFII10)
    real_rate = None
    if fred:
        real_rate = _fred_latest(fred, "DFII10")
    rr_signal, rr_color = _signal_real_rate(real_rate)

    result["indicators"]["real_rate"] = {
        "value": _fmt_pct(real_rate, 2) if real_rate is not None else "N/A",
        "label": f"{_fmt_pct(real_rate, 2)} → {'偏高' if real_rate and real_rate >= 1.5 else '中性'}" if real_rate is not None else "N/A",
        "signal": rr_signal,
        "signal_color": rr_color,
        "source": "FRED: DFII10 (10年期TIPS實質利率)",
        "analysis": _analysis_real_rate(real_rate),
    }

    # VIX (Yahoo Finance ^VIX)
    vix_val = _yf_latest("^VIX")
    vix_signal, vix_color = _signal_vix(vix_val)

    result["indicators"]["vix"] = {
        "value": _fmt_num(vix_val) if vix_val else "N/A",
        "label": f"{_fmt_num(vix_val)} → {'平靜' if vix_val and vix_val < 20 else '恐慌'}" if vix_val else "N/A",
        "signal": vix_signal,
        "signal_color": vix_color,
        "source": "Yahoo Finance: ^VIX",
        "analysis": _analysis_vix(vix_val),
    }

    # USD/TWD (Yahoo Finance TWD=X)
    usd_twd = _yf_latest("TWD=X")
    result["indicators"]["usd_twd"] = {
        "value": f"{usd_twd:.2f}" if usd_twd else "N/A",
        "label": f"{usd_twd:.2f} TWD/USD" if usd_twd else "N/A",
        "signal": f"{usd_twd:.2f} — {'台幣偏弱' if usd_twd and usd_twd > 32 else '台幣偏強'}" if usd_twd else "N/A",
        "signal_color": "var(--yellow)" if usd_twd and usd_twd > 32 else "var(--green)",
        "source": "Yahoo Finance: TWD=X",
        "analysis": _analysis_usd_twd(usd_twd),
    }

    # ── 日本 ──────────────────────────────────────────────────────
    # USD/JPY
    usd_jpy = _yf_latest("JPY=X")
    result["indicators"]["jp_usdjpy"] = {
        "value": f"{usd_jpy:.1f}" if usd_jpy else "N/A",
        "label": f"{usd_jpy:.1f} JPY/USD" if usd_jpy else "N/A",
        "signal": f"{usd_jpy:.1f} — {'日圓偏弱' if usd_jpy and usd_jpy > 145 else '日圓回穩'}" if usd_jpy else "N/A",
        "signal_color": "var(--yellow)" if usd_jpy and usd_jpy > 145 else "var(--green)",
        "source": "Yahoo Finance: JPY=X"
    }

    # 日本 CPI YoY (FRED: JPNCPIALLMINMEI)
    jp_cpi = None
    if fred:
        jp_cpi = _fred_yoy(fred, "JPNCPIALLMINMEI")
    jp_cpi_signal, jp_cpi_color = _signal_cpi(jp_cpi)

    result["indicators"]["jp_cpi"] = {
        "value": _fmt_pct(jp_cpi) if jp_cpi else "N/A",
        "label": f"{_fmt_pct(jp_cpi)} → {'通膨升溫' if jp_cpi and jp_cpi > 2 else '溫和'}" if jp_cpi else "N/A",
        "signal": jp_cpi_signal,
        "signal_color": jp_cpi_color,
        "source": "FRED: JPNCPIALLMINMEI"
    }

    # 日本央行利率 (FRED: IRSTCB01JPM156N)
    jp_rate = None
    if fred:
        jp_rate = _fred_latest(fred, "IRSTCB01JPM156N")

    result["indicators"]["jp_rate"] = {
        "value": _fmt_pct(jp_rate, 2) if jp_rate is not None else "N/A",
        "label": f"{_fmt_pct(jp_rate, 2)} → {'升息' if jp_rate and jp_rate > 0 else '零利率'}" if jp_rate is not None else "N/A",
        "signal": f"{_fmt_pct(jp_rate, 2)} — {'BOJ 正常化' if jp_rate and jp_rate > 0 else 'BOJ 寬鬆'}" if jp_rate is not None else "N/A",
        "signal_color": "var(--yellow)" if jp_rate and jp_rate > 0 else "var(--green)",
        "source": "FRED: IRSTCB01JPM156N"
    }

    # ── 歐元區 ────────────────────────────────────────────────────
    # EUR/USD
    eur_usd = _yf_latest("EURUSD=X")
    result["indicators"]["eu_eurusd"] = {
        "value": f"{eur_usd:.4f}" if eur_usd else "N/A",
        "label": f"{eur_usd:.4f} EUR/USD" if eur_usd else "N/A",
        "signal": f"{eur_usd:.4f} — {'歐元偏強' if eur_usd and eur_usd > 1.08 else '歐元偏弱'}" if eur_usd else "N/A",
        "signal_color": "var(--green)" if eur_usd and eur_usd > 1.08 else "var(--yellow)",
        "source": "Yahoo Finance: EURUSD=X"
    }

    # 歐元區 CPI YoY (FRED: CP0000EZ19M086NEST)
    eu_cpi = None
    if fred:
        eu_cpi = _fred_yoy(fred, "CP0000EZ19M086NEST")
    eu_cpi_signal, eu_cpi_color = _signal_cpi(eu_cpi)

    result["indicators"]["eu_cpi"] = {
        "value": _fmt_pct(eu_cpi) if eu_cpi else "N/A",
        "label": f"{_fmt_pct(eu_cpi)} → {'偏高' if eu_cpi and eu_cpi > 2.5 else '受控'}" if eu_cpi else "N/A",
        "signal": eu_cpi_signal,
        "signal_color": eu_cpi_color,
        "source": "FRED: CP0000EZ19M086NEST (歐元區CPI)"
    }

    # ECB 利率 (FRED: ECBMLFR 或 IR3TIB01EZM156N)
    ecb_rate = None
    if fred:
        ecb_rate = _fred_latest(fred, "ECBMLFR")
    result["indicators"]["eu_rate"] = {
        "value": _fmt_pct(ecb_rate, 2) if ecb_rate is not None else "N/A",
        "label": f"{_fmt_pct(ecb_rate, 2)} → ECB" if ecb_rate is not None else "N/A",
        "signal": f"{_fmt_pct(ecb_rate, 2)} — {'ECB 緊縮' if ecb_rate and ecb_rate >= 3 else 'ECB 降息'}" if ecb_rate is not None else "N/A",
        "signal_color": "var(--red)" if ecb_rate and ecb_rate >= 3 else "var(--yellow)",
        "source": "FRED: ECBMLFR (ECB主要再融資利率)"
    }

    # ── 中國 ──────────────────────────────────────────────────────
    # USD/CNY
    usd_cny = _yf_latest("CNY=X")
    result["indicators"]["cn_usdcny"] = {
        "value": f"{usd_cny:.4f}" if usd_cny else "N/A",
        "label": f"{usd_cny:.4f} CNY/USD" if usd_cny else "N/A",
        "signal": f"{usd_cny:.4f} — {'人民幣偏弱' if usd_cny and usd_cny > 7.2 else '人民幣穩定'}" if usd_cny else "N/A",
        "signal_color": "var(--yellow)" if usd_cny and usd_cny > 7.2 else "var(--green)",
        "source": "Yahoo Finance: CNY=X"
    }

    # 中國 CPI YoY (FRED: CHNCPIALLMINMEI)
    cn_cpi = None
    if fred:
        cn_cpi = _fred_yoy(fred, "CHNCPIALLMINMEI")

    result["indicators"]["cn_cpi"] = {
        "value": _fmt_pct(cn_cpi) if cn_cpi else "N/A",
        "label": f"{_fmt_pct(cn_cpi)} → {'通縮' if cn_cpi and cn_cpi < 0 else '溫和'}" if cn_cpi else "N/A",
        "signal": f"{_fmt_pct(cn_cpi)} — {'通縮壓力' if cn_cpi is not None and cn_cpi < 0 else '通膨溫和'}" if cn_cpi is not None else "N/A",
        "signal_color": "var(--red)" if cn_cpi is not None and cn_cpi < 0 else "var(--green)",
        "source": "FRED: CHNCPIALLMINMEI"
    }

    # ── 韓國 ──────────────────────────────────────────────────────
    # USD/KRW
    usd_krw = _yf_latest("KRW=X")
    result["indicators"]["kr_usdkrw"] = {
        "value": f"{usd_krw:.0f}" if usd_krw else "N/A",
        "label": f"{usd_krw:.0f} KRW/USD" if usd_krw else "N/A",
        "signal": f"{usd_krw:.0f} — {'韓元偏弱' if usd_krw and usd_krw > 1350 else '韓元回穩'}" if usd_krw else "N/A",
        "signal_color": "var(--yellow)" if usd_krw and usd_krw > 1350 else "var(--green)",
        "source": "Yahoo Finance: KRW=X"
    }

    # 韓國 CPI YoY (FRED: KORCPIALLMINMEI)
    kr_cpi = None
    if fred:
        kr_cpi = _fred_yoy(fred, "KORCPIALLMINMEI")
    kr_cpi_signal, kr_cpi_color = _signal_cpi(kr_cpi)

    result["indicators"]["kr_cpi"] = {
        "value": _fmt_pct(kr_cpi) if kr_cpi else "N/A",
        "label": f"{_fmt_pct(kr_cpi)} → {'偏高' if kr_cpi and kr_cpi > 2.5 else '受控'}" if kr_cpi else "N/A",
        "signal": kr_cpi_signal,
        "signal_color": kr_cpi_color,
        "source": "FRED: KORCPIALLMINMEI"
    }

    # ── 台灣指標自動爬取（tw_light / tw_pmi / tw_rate）──────────
    # 優先使用 tw_macro_scraper 自動爬取；失敗時 fallback 到 Sheets/本地
    try:
        from tw_macro_scraper import get_tw_indicators
        tw_data = get_tw_indicators()
        if tw_data:
            for key, val in tw_data.items():
                result["indicators"][key] = val
            logger.info(f"✅ 台灣指標自動爬取成功: {list(tw_data.keys())}")
    except Exception as e:
        logger.warning(f"⚠️ tw_macro_scraper 失敗，fallback 到 Sheets: {e}")
        tw_data = {}

    # ── 其餘手動覆蓋值（從 Google Sheets 讀取，非台灣三大指標）──
    overrides = _load_sheets_overrides()
    for key, override in overrides.items():
        # 台灣三大指標若已自動爬取成功，不覆蓋
        if key in ("tw_light", "tw_pmi", "tw_rate") and key in result["indicators"]:
            continue
        result["indicators"][key] = {
            "value":        override["value"],
            "label":        override.get("label", override["value"]),
            "signal":       override["signal"],
            "signal_color": override["signal_color"],
            "source":       override.get("source", f"手動更新 ({override.get('updated', '')})"),
            "is_manual":    True
        }

    _save_cache(result)
    return result


def get_indicators(force_refresh: bool = False) -> dict:
    """主要對外接口，回傳所有指標數據"""
    try:
        return fetch_macro_data(force_refresh=force_refresh)
    except Exception as e:
        logger.error(f"fetch_macro_data 失敗: {e}")
        # 嘗試回傳舊快取
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    old = json.load(f)
                old["source"] = "stale_cache"
                old["error"] = str(e)
                return old
            except Exception:
                pass
        return {"source": "error", "indicators": {}, "errors": [str(e)]}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 載入 .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
    data = get_indicators(force_refresh=True)
    print(json.dumps(data, ensure_ascii=False, indent=2))
