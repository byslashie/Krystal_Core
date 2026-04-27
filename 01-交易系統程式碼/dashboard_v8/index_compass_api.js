/* ════════════════════════════════════════════════════════════════
   宏觀羅盤 API 集成 - 調用 /api/macro-compass
   ════════════════════════════════════════════════════════════════ */

async function loadCompassData() {
  try {
    console.log('[Compass] 正在加載宏觀指標 API...');
    
    const API_BASE = window.API_BASE || 'http://localhost:8888';
    const response = await fetch(`${API_BASE}/api/macro-compass`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      console.warn(`[Compass] API 返回 ${response.status}`);
      return;
    }

    const data = await response.json();
    console.log('[Compass] API 響應:', data);

    if (data.status !== 'success' && data.status !== 'partial_error') {
      console.warn('[Compass] API 狀態異常:', data.status);
      return;
    }

    const currentQuadrant = data.data?.current_quadrant || 'recovery';
    console.log('[Compass] ✅ 當前象限:', currentQuadrant);

    // 🔴 核心：自動更新前端 UI
    updateCompassUI(currentQuadrant);

  } catch (error) {
    console.error('[Compass] API 調用失敗:', error);
  }
}

/**
 * 更新前端羅盤 UI - 根據 API 返回的象限實時改變顯示
 */
function updateCompassUI(quadrant) {
  try {
    // 移除所有象限的 active-quadrant 類
    document.querySelectorAll('.compass-cell').forEach(cell => {
      cell.classList.remove('active-quadrant');
    });

    // 設定當前象限為 active (id = q-recession, q-expansion 等)
    const quadrantId = `q-${quadrant}`;
    const quadrantElement = document.getElementById(quadrantId);

    if (quadrantElement) {
      quadrantElement.classList.add('active-quadrant');
      console.log('[Compass] ✅ UI 已更新象限:', quadrantId);
    } else {
      console.warn('[Compass] 找不到象限元素:', quadrantId);
    }

    // 呼叫既有的 setQuadrant 函數更新說明框
    if (typeof setQuadrant === 'function') {
      setQuadrant(quadrant);
      console.log('[Compass] ✅ 說明框已更新');
    }

  } catch (error) {
    console.error('[Compass] UI 更新失敗:', error);
  }
}

// 頁面加載時自動調用
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadCompassData);
} else {
  loadCompassData();
}

// 定時刷新（每 5 分鐘）
setInterval(loadCompassData, 5 * 60 * 1000);

/* ════════════════════════════════════════════════════════════════
   台灣總經指標 - 景氣燈號動態更新
   ════════════════════════════════════════════════════════════════ */

async function loadTwIndicators() {
  try {
    const API_BASE = window.API_BASE || 'http://localhost:8888';
    const resp = await fetch(`${API_BASE}/api/tw-indicators`, {
      headers: { 'Accept': 'application/json' }
    });
    if (!resp.ok) return;

    const json = await resp.json();
    if (json.status !== 'success' || !json.data) return;

    const light = json.data.tw_light;
    if (light) {
      const valEl    = document.getElementById('tw-light-val');
      const trendEl  = document.getElementById('tw-light-trend');
      const fillEl   = document.getElementById('tw-light-fill');
      const pctEl    = document.getElementById('tw-light-pct');
      const updEl    = document.getElementById('tw-light-updated');

      const color = light.signal_color || 'var(--text-primary)';
      const pct   = light.pct != null ? light.pct : Math.min(100, Math.round((light.score || 39) / 45 * 100));

      if (valEl)   { valEl.textContent = light.value;   valEl.style.color = color; }
      if (trendEl) { trendEl.textContent = light.signal; trendEl.style.color = color; }
      if (fillEl)  { fillEl.style.width = pct + '%';    fillEl.style.background = color; }
      if (pctEl)   { pctEl.textContent = pct + '% 熱絡區間'; pctEl.style.color = color; }
      if (updEl && light.updated) { updEl.textContent = light.updated; }

      // 同步更新 INDICATOR_DATA（彈出視窗用）
      if (window.INDICATOR_DATA && window.INDICATOR_DATA.tw_light) {
        window.INDICATOR_DATA.tw_light.value  = light.value;
        window.INDICATOR_DATA.tw_light.signal = light.signal;
        window.INDICATOR_DATA.tw_light.signalColor = color;
        if (light.source) window.INDICATOR_DATA.tw_light.analysis =
          `【${light.updated || ''}】${light.signal}｜來源：${light.source}`;
      }

      console.log('[TW] 景氣燈號已更新:', light.value, light.signal);
    }
  } catch (e) {
    console.warn('[TW] 台灣指標載入失敗:', e);
  }
}

/**
 * 快速更新景氣燈號分數（由頁面彈出視窗呼叫）
 * @param {number} score - NDC 分數 (0~45)
 */
async function updateTwLight(score) {
  const API_BASE = window.API_BASE || 'http://localhost:8889';
  try {
    const resp = await fetch(`${API_BASE}/api/tw-indicators/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'tw_light', value: String(score) })
    });
    const json = await resp.json();
    if (json.status === 'success') {
      await loadTwIndicators();
      return true;
    } else {
      console.error('[TW] 更新失敗:', json.message);
      return false;
    }
  } catch (e) {
    console.error('[TW] 更新請求失敗:', e);
    return false;
  }
}

// 頁面載入時同步台灣指標
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadTwIndicators);
} else {
  loadTwIndicators();
}

// 每小時刷新一次（月度數據不需要頻繁）
setInterval(loadTwIndicators, 60 * 60 * 1000);
