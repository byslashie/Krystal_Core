"""
總經羅盤 - 實時經濟指標整合
基於 Fed、統計局、Yahoo Finance 的實時數據
自動判斷市場象限（擴張/趨緩/衰退/復甦）
"""

import asyncio
import aiohttp
from typing import Dict, List, Any
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ════════════════════════════════════════
# 經濟指標 API 端點
# ════════════════════════════════════════

class MacroCompassAPI:
    """實時經濟指標獲取"""

    FRED_API_KEY = os.getenv("FRED_API_KEY", "")  # 從 .env 讀取，若無則為空

    # 關鍵經濟指標代碼（美國聯邦準備局 FRED）
    INDICATORS = {
        "GDP": "A191RL1Q225SBEA",           # GDP 增長率
        "UNEMPLOYMENT": "UNRATE",           # 失業率
        "INFLATION": "CPIAUCSL",            # 消費者物價指數
        "FED_RATE": "FEDFUNDS",             # 聯邦基金利率
        "10Y_YIELD": "DGS10",               # 10 年期公債殖利率
        "VIX": "VIXCLS",                    # 波動率指數
    }

    # 市場指數代碼（Yahoo Finance）
    INDICES = {
        "SP500": "^GSPC",
        "NASDAQ": "^IXIC",
        "RUSSELL2000": "^RUT",
        "TSE": "^TWII",                     # 台灣加權指數
        "NIKKEI": "^N225",
        "DAX": "^GDAXI",
        "SENSEX": "^BSESN",
        "SHANGHAI": "000001.SS",
    }

    async def get_fred_indicator(self, indicator_code: str) -> Dict[str, Any]:
        """取得 FRED 經濟指標"""
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={indicator_code}&api_key={self.FRED_API_KEY}&file_type=json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        observations = data.get('observations', [])
                        if observations:
                            latest = observations[-1]
                            return {
                                'code': indicator_code,
                                'value': float(latest.get('value', 0)),
                                'date': latest.get('date'),
                                'unit': '單位待補',
                                'status': 'success'
                            }
        except Exception as e:
            logger.error(f"FRED API 錯誤 ({indicator_code}): {e}")

        return {'status': 'error', 'code': indicator_code}

    async def get_index_data(self, symbol: str) -> Dict[str, Any]:
        """取得指數數據（Yahoo Finance）"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5y&interval=1d"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get('chart', {}).get('result', [{}])[0]

                        if not result:
                            return {'status': 'error', 'symbol': symbol}

                        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])

                        if closes:
                            current = closes[-1]
                            max_5y = max(c for c in closes if c is not None)
                            min_5y = min(c for c in closes if c is not None)
                            percentile = (current - min_5y) / (max_5y - min_5y) * 100 if max_5y > min_5y else 50

                            return {
                                'symbol': symbol,
                                'current': current,
                                'max_5y': max_5y,
                                'min_5y': min_5y,
                                'percentile_52w': percentile,
                                'status': 'success'
                            }
        except Exception as e:
            logger.error(f"Yahoo Finance 錯誤 ({symbol}): {e}")

        return {'status': 'error', 'symbol': symbol}

    @staticmethod
    def _classify_quadrant(cpi: float, nfp_k: float, vix: float, ism_pmi: float) -> tuple[str, dict]:
        """
        用真實數據計算景氣象限（美林時鐘框架）

        兩個軸：
          growth_score  = 成長動能（NFP + ISM PMI）
          inflation     = 通膨水準（CPI）

        象限定義：
          擴張 expansion  = 成長強 + 通膨合理 (<3.5%)
          趨緩 slowdown   = 成長弱 + 通膨偏高 (≥2.5%)
          衰退 recession  = 成長負 + 市場恐慌 (VIX高)
          復甦 recovery   = 成長轉正 + 通膨受控
        """
        # ── 成長動能評分 (0-100) ───────────────────────────────
        # NFP: -100K→0分, 0K→30分, 150K→60分, 300K+→100分
        if nfp_k is None:
            nfp_score = 50
        elif nfp_k >= 300:
            nfp_score = 100
        elif nfp_k >= 150:
            nfp_score = 60 + (nfp_k - 150) / 150 * 40
        elif nfp_k >= 0:
            nfp_score = 30 + nfp_k / 150 * 30
        else:
            nfp_score = max(0, 30 + nfp_k / 100 * 30)  # 負值往下扣

        # ISM PMI: <45→0分, 50→50分, 55+→100分
        if ism_pmi is None:
            pmi_score = 50
        elif ism_pmi >= 55:
            pmi_score = 100
        elif ism_pmi >= 50:
            pmi_score = 50 + (ism_pmi - 50) / 5 * 50
        elif ism_pmi >= 45:
            pmi_score = (ism_pmi - 45) / 5 * 50
        else:
            pmi_score = 0

        growth_score = nfp_score * 0.6 + pmi_score * 0.4

        # ── 通膨水準 ──────────────────────────────────────────
        inflation_high = cpi >= 2.5 if cpi is not None else False
        inflation_very_high = cpi >= 4.0 if cpi is not None else False

        # ── VIX 恐慌程度 ──────────────────────────────────────
        fear_high = vix >= 28 if vix is not None else False

        # ── 象限判斷矩陣 ──────────────────────────────────────
        if growth_score >= 55 and not inflation_very_high:
            quadrant = "expansion"   # 成長強 + 通膨合理 → 擴張
        elif growth_score >= 40 and inflation_high:
            quadrant = "slowdown"    # 成長中等 + 通膨偏高 → 趨緩
        elif growth_score < 35 and fear_high:
            quadrant = "recession"   # 成長弱 + 市場恐慌 → 衰退
        elif growth_score < 50 and not inflation_high:
            quadrant = "recovery"    # 成長偏弱 + 通膨受控 → 復甦
        else:
            quadrant = "slowdown"    # 其他情況偏向趨緩

        detail = {
            "growth_score": round(growth_score, 1),
            "nfp_score": round(nfp_score, 1),
            "pmi_score": round(pmi_score, 1),
            "inflation_high": inflation_high,
            "fear_high": fear_high,
            "inputs": {
                "cpi": cpi,
                "nfp_k": nfp_k,
                "vix": vix,
                "ism_pmi": ism_pmi,
            }
        }
        return quadrant, detail

    async def get_compass_data(self) -> Dict[str, Any]:
        """取得完整羅盤數據 — 使用 macro_data 真實指標計算象限"""
        try:
            # ── 從 macro_data 取得已快取的真實指標 ───────────────
            from macro_data import get_indicators
            ind_data = get_indicators()
            inds = ind_data.get("indicators", {})

            def _num(key: str) -> float | None:
                """安全取值，解析 '2.7%' → 2.7、'-92K' → -92 等"""
                raw = inds.get(key, {}).get("value", None)
                if raw is None or raw == "N/A":
                    return None
                try:
                    s = str(raw).replace("%", "").replace("K", "").replace("+", "").strip()
                    return float(s)
                except (ValueError, TypeError):
                    return None

            cpi     = _num("us_cpi")
            nfp_k   = _num("nfp")      # 單位已是 K（千人），例如 -92
            vix     = _num("vix")
            ism_pmi = _num("ism_pmi")

            quadrant, detail = self._classify_quadrant(cpi, nfp_k, vix, ism_pmi)

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "current_quadrant": quadrant,
                "classification_detail": detail,
                "indicators": {
                    "us_cpi":  inds.get("us_cpi", {}),
                    "nfp":     inds.get("nfp", {}),
                    "vix":     inds.get("vix", {}),
                    "ism_pmi": inds.get("ism_pmi", {}),
                    "fed_rate": inds.get("fed_rate", {}),
                },
                "data_source": ind_data.get("source", "unknown"),
            }

        except Exception as e:
            logger.error(f"Compass API 錯誤: {e}")
            return {
                "status": "partial_error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "current_quadrant": "recovery",
            }


# 快速測試
if __name__ == "__main__":
    compass = MacroCompassAPI()

    # 同步執行（用於測試）
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(compass.get_compass_data())

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
