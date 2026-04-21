// ============================================================================
// 多頁面儀表板 JavaScript
// ============================================================================

const API_BASE_URL = '';  // 同源請求
let currentPage = 'dashboard';

// 船舶監測狀態追蹤
let lastShipData = null;
let shipDataChangedTime = null;

// 船旗（國家代碼）到國家名稱和國旗 emoji 的映射
const COUNTRY_FLAGS = {
    'PA': { name: '巴拿馬', flag: '🇵🇦' },
    'LR': { name: '利比里亞', flag: '🇱🇷' },
    'KH': { name: '柬埔寨', flag: '🇰🇭' },
    'MH': { name: '馬紹爾群島', flag: '🇲🇭' },
    'SG': { name: '新加坡', flag: '🇸🇬' },
    'HK': { name: '香港', flag: '🇭🇰' },
    'AE': { name: '阿聯酋', flag: '🇦🇪' },
    'CN': { name: '中國', flag: '🇨🇳' },
    'RU': { name: '俄羅斯', flag: '🇷🇺' },
    'IR': { name: '伊朗', flag: '🇮🇷' },
    'IQ': { name: '伊拉克', flag: '🇮🇶' },
    'KW': { name: '科威特', flag: '🇰🇼' },
    'SA': { name: '沙烏地阿拉伯', flag: '🇸🇦' },
    'QA': { name: '卡達', flag: '🇶🇦' },
    'OM': { name: '阿曼', flag: '🇴🇲' },
    'AO': { name: '安哥拉', flag: '🇦🇴' },
    'GR': { name: '希臘', flag: '🇬🇷' },
    'NL': { name: '荷蘭', flag: '🇳🇱' },
    'NO': { name: '挪威', flag: '🇳🇴' },
    'GB': { name: '英國', flag: '🇬🇧' },
    'DE': { name: '德國', flag: '🇩🇪' },
    'FR': { name: '法國', flag: '🇫🇷' },
    'IT': { name: '義大利', flag: '🇮🇹' },
    'ES': { name: '西班牙', flag: '🇪🇸' },
    'PT': { name: '葡萄牙', flag: '🇵🇹' },
    'MT': { name: '馬爾他', flag: '🇲🇹' },
    'CY': { name: '塞浦路斯', flag: '🇨🇾' },
    'JP': { name: '日本', flag: '🇯🇵' },
    'KR': { name: '韓國', flag: '🇰🇷' },
    'TW': { name: '台灣', flag: '🇹🇼' },
    'TH': { name: '泰國', flag: '🇹🇭' },
    'MY': { name: '馬來西亞', flag: '🇲🇾' },
    'PH': { name: '菲律賓', flag: '🇵🇭' },
    'IN': { name: '印度', flag: '🇮🇳' },
    'BD': { name: '孟加拉', flag: '🇧🇩' },
    'US': { name: '美國', flag: '🇺🇸' },
    'CA': { name: '加拿大', flag: '🇨🇦' },
    'AU': { name: '澳洲', flag: '🇦🇺' },
    'NZ': { name: '紐西蘭', flag: '🇳🇿' },
    'BR': { name: '巴西', flag: '🇧🇷' },
    'MX': { name: '墨西哥', flag: '🇲🇽' },
};

// 根据船旗代码获取国家信息
function getCountryInfo(flagCode) {
    if (!flagCode) return { name: '未知', flag: '🏳️' };
    const code = flagCode.toUpperCase();
    return COUNTRY_FLAGS[code] || { name: flagCode, flag: '🏳️' };
}

// ============================================================================
// Sidebar 收合功能
// ============================================================================

function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const container = document.querySelector('.container');

    if (!toggleBtn || !sidebar) return;

    // 從 localStorage 恢復狀態
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }

    // 點擊收合按鈕
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        sidebar.classList.toggle('collapsed');
        const newCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebar-collapsed', newCollapsed);
    });
}

// 頁面加載後初始化
document.addEventListener('DOMContentLoaded', initSidebarToggle);

// ============================================================================
// 全局工具函數 - Loading / Toast / 錯誤提示
// ============================================================================

/**
 * 顯示 Loading Spinner
 * @param {string} elementId - 目標元素 ID（可選，不指定則全屏遮罩）
 * @param {string} message - 顯示訊息（可選）
 */
function showLoading(elementId, message) {
    if (!elementId) {
        // 全屏 Loading
        let overlay = document.getElementById('global-loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'global-loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"></div>';
            document.body.appendChild(overlay);
        }
        overlay.classList.remove('hidden');
    } else {
        // 元素內 Loading
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="skeleton"></div><div class="skeleton" style="width: 80%;"></div><div class="skeleton" style="width: 60%;"></div>`;
        }
    }
}

/**
 * 隱藏 Loading Spinner
 * @param {string} elementId - 目標元素 ID（可選）
 */
function hideLoading(elementId) {
    if (!elementId) {
        // 隱藏全屏 Loading
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    // 元素內的 loading 會被後續內容替換，無需額外操作
}

/**
 * 顯示 Toast 通知（右上角堆疊）
 * @param {string} message - 通知訊息
 * @param {string} type - 類型: 'success' | 'error' | 'warning' | 'info'
 * @param {number} duration - 顯示時長（毫秒，0 表示不自動關閉）
 */
function showToast(message, type = 'info', duration = 3000) {
    // 確保容器存在
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // 建立 Toast 元素
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove();">×</button>
    `;

    container.appendChild(toast);

    // 自動關閉
    if (duration > 0) {
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

/**
 * 顯示錯誤訊息在指定元素內
 * @param {string} message - 錯誤訊息
 * @param {string} elementId - 目標元素 ID
 */
function showErrorMessage(message, elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="error-message">${message}</div>`;
    }
    showToast(message, 'error');
}

/**
 * 顯示成功訊息
 * @param {string} message - 成功訊息
 * @param {string} elementId - 目標元素 ID（可選）
 */
function showSuccessMessage(message, elementId) {
    if (elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="success-message">${message}</div>`;
        }
    }
    showToast(message, 'success');
}

// ============================================================================
// 頁面導航 - 立即定義（不在 DOMContentLoaded 中）
// ============================================================================

function loadPage(page) {
    console.log('Loading page:', page);

    try {
        // 更新活躍按鈕
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        // 隱藏所有頁面
        const allPages = document.querySelectorAll('.page');
        console.log('Found pages:', allPages.length);
        allPages.forEach(p => {
            p.classList.remove('active');
        });

        // 顯示選定頁面
        const pageElement = document.getElementById(`${page}-page`);
        console.log('Page element found:', !!pageElement, `(ID: ${page}-page)`);

        if (pageElement) {
            pageElement.classList.add('active');
            console.log('Page activated:', page);
        } else {
            console.error('Page element not found:', `${page}-page`);
            return;
        }

        currentPage = page;

        // 加載頁面特定數據
        switch(page) {
            case 'dashboard':
                console.log('Calling loadDashboardPage');
                loadDashboardPage();
                break;
            case 'ship-monitor':
                console.log('Calling loadShipMonitorPage');
                loadShipMonitorPage();
                break;
            case 'trading':
                console.log('Calling loadTradingPage');
                loadTradingPage();
                break;
            case 'strategies':
                console.log('Calling loadStrategiesPage');
                loadStrategiesPage();
                break;
            case 'comparison':
                console.log('Calling loadComparisonPage');
                loadComparisonPage();
                break;
            case 'analysis':
                console.log('Calling loadAnalysisPage');
                loadAnalysisPage();
                loadMacroDashboard();  // 同時加載宏觀儀表板
                break;
            case 'intel':
                console.log('Calling loadIntelPage');
                loadIntelPage();
                break;
            case 'minsky-clock':
                console.log('Calling loadMinskyClockPage');
                loadMinskyClockPage();
                break;
            case 'community-risk':
                console.log('Calling loadCommunityRiskPage');
                loadCommunityRiskPage();
                break;
            case 'risk-control':
                console.log('Calling loadRiskControlPage');
                loadRiskControlPage();
                break;
            case 'allocation':
                console.log('Calling loadAllocationPage');
                loadAllocationPage();
                break;
            case 'performance':
                console.log('Calling loadPerformancePage');
                loadPerformancePage();
                break;
            default:
                console.warn('Unknown page:', page);
        }
    } catch (error) {
        console.error('Error in loadPage:', error);
    }
}

function setupNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const page = e.target.dataset.page;
            loadPage(page);
        });
    });
}

// ============================================================================
// 初始化
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');

    // 頁面導航
    setupNavigation();

    // 共享控制
    setupCommonControls();

    // 加載初始頁面
    loadPage('dashboard');

    // 定時刷新
    setInterval(() => {
        if (currentPage === 'dashboard') {
            updateMetrics();
            updateHoldings();
        }
    }, 30000);

    console.log('Dashboard ready!');
});

// ============================================================================
// 共享控制
// ============================================================================

function setupCommonControls() {
    const periodSelect = document.getElementById('period-select');
    if (periodSelect) {
        periodSelect.addEventListener('change', (e) => {
            console.log('Period changed to:', e.target.value);
            if (currentPage === 'dashboard') {
                loadDashboardPage();
            }
        });
    }

    const riskRadios = document.querySelectorAll('input[name="risk"]');
    riskRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            console.log('Risk level changed to:', e.target.value);
        });
    });

    // 綁定「紀錄今日」按鈕
    const recordBtn = document.getElementById('record-performance-btn');
    if (recordBtn) {
        recordBtn.addEventListener('click', recordTodayPerformance);
    }
}

// ============================================================================
// 儀表板頁面
// ============================================================================

async function loadDashboardPage() {
    await updateMetrics();
    await updateHoldings();
    await renderPriceChart();
    await renderPerformanceTrendChart();
}

async function updateMetrics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/metrics`);
        const result = await response.json();
        const metrics = result.data || result;

        const grid = document.getElementById('metrics-grid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label">💰 總資產</span>
                    <span class="metric-change positive">+${metrics.daily_change || 2.34}%</span>
                </div>
                <div class="metric-value">$${(metrics.total_value || 125345).toLocaleString()}</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label">📈 年度報酬</span>
                    <span class="metric-change positive">+5.12%</span>
                </div>
                <div class="metric-value">${(metrics.annual_return || 15.5).toFixed(2)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label">📊 持倉數</span>
                    <span class="metric-change positive">+1</span>
                </div>
                <div class="metric-value">${metrics.holdings || 4}</div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label">⚡ 風險評分</span>
                    <span class="metric-change neutral">-0.5</span>
                </div>
                <div class="metric-value">${Math.abs(metrics.max_drawdown || 20) > 15 ? '高' : Math.abs(metrics.max_drawdown || 20) > 8 ? '中' : '低'}</div>
            </div>
        `;
    } catch (error) {
        console.error('Error updating metrics:', error);
    }
}

async function updateHoldings() {
    try {
        console.log('[DEBUG] updateHoldings() called');
        // 獲取按券商分類的持倉
        const response = await fetch(`${API_BASE_URL}/api/holdings/by-broker`);
        console.log('[DEBUG] API response status:', response.status);

        const result = await response.json();
        console.log('[DEBUG] API result:', result);

        if (result.status !== 'success') {
            console.warn('Failed to fetch holdings by broker');
            return;
        }

        console.log(`[DEBUG] Calling updateBrokerHoldings for IB with count=${result.ib.count}`);
        // 填充 IB 持倉
        updateBrokerHoldings('ib', result.ib);

        console.log(`[DEBUG] Calling updateBrokerHoldings for Yuanta with count=${result.yuanta.count}`);
        // 填充 Yuanta 持倉
        updateBrokerHoldings('yuanta', result.yuanta);

    } catch (error) {
        console.error('Error updating holdings:', error);
    }
}

function updateBrokerHoldings(broker, brokerData) {
    console.log(`[DEBUG] updateBrokerHoldings called with broker=${broker}`, brokerData);
    const tableId = `${broker}-holdings-table`;
    const countId = `${broker}-count`;
    const tbody = document.querySelector(`#${tableId} tbody`);

    console.log(`[DEBUG] Looking for tbody: #${tableId} tbody`, tbody);
    if (!tbody || !brokerData) {
        console.warn(`[DEBUG] Missing tbody or brokerData for ${broker}`);
        return;
    }

    // 更新計數
    const countElement = document.getElementById(countId);
    if (countElement) {
        countElement.textContent = brokerData.count || 0;
    }

    tbody.innerHTML = '';

    if (!brokerData.positions || brokerData.positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #9ca3af;">無持倉</td></tr>';
        return;
    }

    brokerData.positions.forEach(holding => {
        const row = document.createElement('tr');

        const symbol = holding.symbol || holding.標的 || '-';
        const market = holding.market || holding.exchange || holding.市場 || '-';
        const quantity = holding.position || holding.數量 || 0;
        const avgCost = holding.avgCost || holding.均價 || 0;
        const currency = holding.currency || holding.貨幣 || 'TWD';

        // Convert to numbers in case they're strings from API
        const quantityNum = parseFloat(quantity);
        const quantityStr = quantityNum > 0 ? quantityNum.toString() : '-';
        const costNum = parseFloat(avgCost);
        const costStr = costNum > 0 ? costNum.toFixed(2) : '-';

        row.innerHTML = `
            <td style="font-weight: 600; color: #1f2937;">${symbol}</td>
            <td style="color: #6b7280;">${market}</td>
            <td>${quantityStr}</td>
            <td>${costStr}</td>
            <td>${currency}</td>
        `;
        tbody.appendChild(row);
    });
}

async function renderPriceChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chart-data`);
        const result = await response.json();
        const data = result.data || result;

        if (!data || !data.dates) return;

        const trace = {
            x: data.dates,
            y: data.prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Price',
            line: { color: '#6B21A8', width: 3 },
            fill: 'tozeroy',
            fillcolor: 'rgba(107, 33, 168, 0.1)',
            hovertemplate: '<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: { showgrid: true, gridcolor: '#F0E8FF', showline: true, linecolor: '#E8E0FF' },
            yaxis: { showgrid: true, gridcolor: '#F0E8FF', showline: true, linecolor: '#E8E0FF' },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { l: 50, r: 50, t: 30, b: 50 },
            hovermode: 'x unified',
            font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif', size: 12, color: '#1A1A2E' }
        };

        Plotly.newPlot('price-chart', [trace], layout, { responsive: true, displayModeBar: false });
    } catch (error) {
        console.error('Error rendering price chart:', error);
    }
}

// ============================================================================
// 實盤交易頁面
// ============================================================================

async function loadTradingPage() {
    console.log('loadTradingPage called');

    try {
        // 先加載系統狀態
        const statusContainer = document.getElementById('trades-container');
        if (statusContainer) {
            showLoading(statusContainer);
        }

        const response = await fetch(`${API_BASE_URL}/api/status`);
        if (response.ok) {
            const data = await response.json();
            if (statusContainer) {
                statusContainer.innerHTML = `
                    <div class="info-box">
                        <p><strong>系統狀態:</strong> ${data.app}</p>
                        <p><strong>數據層:</strong> ${data.data_layer ? '✅ 已連接' : '❌ 未連接'}</p>
                        <p><strong>時間戳:</strong> ${data.timestamp}</p>
                    </div>
                    <div class="info-box">
                        <h4>Broker 連接狀態</h4>
                        <ul>
                            <li>IB: ${data.brokers?.ib ? '✅ 已連接' : '⏳ 未配置'}</li>
                            <li>Yuanta: ${data.brokers?.yuanta ? '✅ 已連接' : '⏳ 未配置'}</li>
                            <li>Schwab: ${data.brokers?.schwab ? '✅ 已連接' : '⏳ 未配置'}</li>
                        </ul>
                    </div>
                `;
                hideLoading(statusContainer);
            }
        }

        // 並行加載所有交易數據（當前 + 已實現 + Broker 持倉）
        await Promise.all([
            loadCurrentTrades(),
            loadRealizedTrades(),
            loadBrokerHoldings()
        ]);

    } catch (err) {
        console.error('Error loading trading page:', err);
        showToast(`❌ 加載交易頁面失敗: ${err.message}`, 'error', 3000);
    }

    // 設置 Broker 同步按鈕
    setupBrokerButtons();
}

async function loadHoldingsList() {
    const container = document.getElementById('trades-container');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/holdings`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const holdings = result.data || [];

        // 移除舊的持倉表格（防止重複）
        const oldTable = container.querySelector('h3:last-of-type');
        if (oldTable) {
            oldTable.remove();
            const table = oldTable.nextElementSibling;
            if (table && table.tagName === 'TABLE') {
                table.remove();
            }
        }

        let html = '<h3 style="margin-top: 24px;">📊 當前持倉</h3>';

        if (holdings.length === 0) {
            html += '<p style="color: #9CA3AF;">暫無持倉</p>';
        } else {
            html += '<table style="width: 100%; border-collapse: collapse; margin-top: 12px;">';
            html += `
                <thead>
                    <tr style="border-bottom: 2px solid #E5E7EB;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">代碼</th>
                        <th style="padding: 12px; text-align: left; font-weight: bold;">市場</th>
                        <th style="padding: 12px; text-align: left; font-weight: bold;">數量</th>
                        <th style="padding: 12px; text-align: left; font-weight: bold;">平均成本</th>
                        <th style="padding: 12px; text-align: left; font-weight: bold;">貨幣</th>
                    </tr>
                </thead>
                <tbody>
            `;

            holdings.forEach(holding => {
                const symbol = holding.symbol || holding['標的'] || '-';
                const market = holding.exchange || holding.market || holding['市場'] || '-';
                const position = holding.position || holding['數量'] || '-';
                const avgCost = holding.avgCost || holding['平均成本'] || '-';
                const currency = holding.currency || holding['貨幣'] || 'TWD';

                html += `
                    <tr style="border-bottom: 1px solid #E5E7EB;">
                        <td style="padding: 12px;"><strong>${symbol}</strong></td>
                        <td style="padding: 12px;">${market}</td>
                        <td style="padding: 12px;">${position}</td>
                        <td style="padding: 12px;">${avgCost}</td>
                        <td style="padding: 12px;">${currency}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
        }

        // 替換（不追加）持倉數據
        container.innerHTML += html;

        // 綁定編輯按鈕
        document.querySelectorAll('.edit-trade-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tradeId = e.target.getAttribute('data-id');
                showEditTradeModal(tradeId);
            });
        });

    } catch (error) {
        console.error('Error loading holdings:', error);
        showToast(`❌ 加載持倉失敗: ${error.message}`, 'error', 3000);
        container.innerHTML += '<p style="color: #EF4444;">❌ 加載持倉失敗，請重試</p>';
    }
}

async function loadBrokerHoldings() {
    const container = document.getElementById('trades-container');
    if (!container) return;

    try {
        // 使用含市價的端點
        const response = await fetch(`${API_BASE_URL}/api/holdings/by-broker/with-prices`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        if (result.status !== 'success') throw new Error('無法獲取持倉數據');

        // 移除舊的持倉表格（防止重複）
        // 找到第一個 broker 標題，然後移除它之後的所有內容
        let firstBrokerHeading = null;
        for (let node of container.childNodes) {
            if (node.tagName === 'H3' && (node.textContent.includes('Interactive Brokers') || node.textContent.includes('Yuanta'))) {
                firstBrokerHeading = node;
                break;
            }
        }

        if (firstBrokerHeading) {
            // 移除從第一個 broker 標題開始的所有元素
            let node = firstBrokerHeading;
            while (node) {
                const nextNode = node.nextSibling;
                node.remove();
                node = nextNode;
            }
        }

        let html = '';

        // IB 持倉表格
        html += '<h3 style="margin-top: 24px;">🏦 Interactive Brokers (IB) (' + result.ib.count + ' 筆)</h3>';
        if (result.ib.count === 0) {
            html += '<p style="color: #9CA3AF;">暫無持倉</p>';
        } else {
            html += '<table style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px;"><thead><tr style="border-bottom: 2px solid #E5E7EB; background-color: #F9FAFB;"><th style="padding: 12px; text-align: left; font-weight: bold;">代碼</th><th style="padding: 12px; text-align: left; font-weight: bold;">市場</th><th style="padding: 12px; text-align: right; font-weight: bold;">數量</th><th style="padding: 12px; text-align: right; font-weight: bold;">平均成本</th><th style="padding: 12px; text-align: right; font-weight: bold;">市價</th><th style="padding: 12px; text-align: right; font-weight: bold;">未實現損益</th><th style="padding: 12px; text-align: right; font-weight: bold;">損益%</th><th style="padding: 12px; text-align: left; font-weight: bold;">貨幣</th></tr></thead><tbody>';

            result.ib.positions.forEach(pos => {
                const symbol = pos.symbol || '-';
                const market = pos.exchange || '-';
                const position = pos.position || '-';
                const avgCost = parseFloat(pos.avgCost) > 0 ? parseFloat(pos.avgCost).toFixed(2) : '-';
                const marketPrice = pos.marketPrice !== null ? parseFloat(pos.marketPrice).toFixed(2) : '⏳ 加載中';
                const currency = pos.currency || 'USD';

                let unrealizedPLStr = '-';
                let unrealizedPLPctStr = '-';
                let plColor = '#6B7280';

                if (pos.unrealizedPL !== null && pos.unrealizedPLPct !== null) {
                    const pl = parseFloat(pos.unrealizedPL);
                    const plPct = parseFloat(pos.unrealizedPLPct);
                    unrealizedPLStr = pl >= 0 ? `+${pl.toFixed(2)}` : pl.toFixed(2);
                    unrealizedPLPctStr = plPct >= 0 ? `+${plPct.toFixed(2)}%` : `${plPct.toFixed(2)}%`;
                    plColor = pl >= 0 ? '#10B981' : '#EF4444'; // 綠色漲、紅色跌
                }

                html += `<tr style="border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 12px;"><strong>${symbol}</strong></td>
                    <td style="padding: 12px;">${market}</td>
                    <td style="padding: 12px; text-align: right;">${position}</td>
                    <td style="padding: 12px; text-align: right;">${avgCost}</td>
                    <td style="padding: 12px; text-align: right;"><strong>${marketPrice}</strong></td>
                    <td style="padding: 12px; text-align: right; color: ${plColor}; font-weight: bold;">${unrealizedPLStr}</td>
                    <td style="padding: 12px; text-align: right; color: ${plColor}; font-weight: bold;">${unrealizedPLPctStr}</td>
                    <td style="padding: 12px;">${currency}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }

        // Yuanta 持倉表格
        html += '<h3 style="margin-top: 24px;">🏪 Yuanta Securities (元大) (' + result.yuanta.count + ' 筆)</h3>';
        if (result.yuanta.count === 0) {
            html += '<p style="color: #9CA3AF;">暫無持倉</p>';
        } else {
            html += '<table style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px;"><thead><tr style="border-bottom: 2px solid #E5E7EB; background-color: #F9FAFB;"><th style="padding: 12px; text-align: left; font-weight: bold;">代碼</th><th style="padding: 12px; text-align: left; font-weight: bold;">市場</th><th style="padding: 12px; text-align: right; font-weight: bold;">數量</th><th style="padding: 12px; text-align: right; font-weight: bold;">平均成本</th><th style="padding: 12px; text-align: right; font-weight: bold;">市價</th><th style="padding: 12px; text-align: right; font-weight: bold;">未實現損益</th><th style="padding: 12px; text-align: right; font-weight: bold;">損益%</th><th style="padding: 12px; text-align: left; font-weight: bold;">貨幣</th></tr></thead><tbody>';

            result.yuanta.positions.forEach(pos => {
                const symbol = pos.symbol || '-';
                const market = pos.exchange || '-';
                const position = pos.position || '-';
                const avgCost = parseFloat(pos.avgCost) > 0 ? parseFloat(pos.avgCost).toFixed(2) : '-';
                const marketPrice = pos.marketPrice !== null ? parseFloat(pos.marketPrice).toFixed(2) : '⏳ 加載中';
                const currency = pos.currency || 'TWD';

                let unrealizedPLStr = '-';
                let unrealizedPLPctStr = '-';
                let plColor = '#6B7280';

                if (pos.unrealizedPL !== null && pos.unrealizedPLPct !== null) {
                    const pl = parseFloat(pos.unrealizedPL);
                    const plPct = parseFloat(pos.unrealizedPLPct);
                    unrealizedPLStr = pl >= 0 ? `+${pl.toFixed(2)}` : pl.toFixed(2);
                    unrealizedPLPctStr = plPct >= 0 ? `+${plPct.toFixed(2)}%` : `${plPct.toFixed(2)}%`;
                    plColor = pl >= 0 ? '#10B981' : '#EF4444';
                }

                html += `<tr style="border-bottom: 1px solid #E5E7EB;">
                    <td style="padding: 12px;"><strong>${symbol}</strong></td>
                    <td style="padding: 12px;">${market}</td>
                    <td style="padding: 12px; text-align: right;">${position}</td>
                    <td style="padding: 12px; text-align: right;">${avgCost}</td>
                    <td style="padding: 12px; text-align: right;"><strong>${marketPrice}</strong></td>
                    <td style="padding: 12px; text-align: right; color: ${plColor}; font-weight: bold;">${unrealizedPLStr}</td>
                    <td style="padding: 12px; text-align: right; color: ${plColor}; font-weight: bold;">${unrealizedPLPctStr}</td>
                    <td style="padding: 12px;">${currency}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }

        // 追加持倉表格（使用 insertAdjacentHTML 避免 innerHTML += 問題）
        container.insertAdjacentHTML('beforeend', html);

    } catch (error) {
        console.error('Error loading broker holdings:', error);
        showToast(`❌ 加載持倉失敗: ${error.message}`, 'error', 3000);
        container.innerHTML += '<p style="color: #EF4444;">❌ 加載持倉失敗，請重試</p>';
    }
}

async function showEditTradeModal(tradeId) {
    // 從全域查找交易資料
    const trade = (window.allCurrentTrades || []).find(t => t.id === tradeId) || {};
    const symbol = trade['標的'] || '';
    const currentStrategy = trade['策略'] || '';
    const currentEntryReason = trade['進場原因'] || '';
    const entryPrice = trade['進場價'] || 0;
    const quantity = trade['數量'] || 0;

    // 取得策略列表
    let strategies = [];
    try {
        const res = await fetch(`${API_BASE_URL}/api/strategies`);
        const data = await res.json();
        strategies = (data.data || []).map(s => s['策略名稱'] || s.name || '').filter(Boolean);
    } catch (e) {}

    const strategyOptions = strategies.map(s =>
        `<option value="${s}" ${s === currentStrategy ? 'selected' : ''}>${s}</option>`
    ).join('');

    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.5); display: flex;
        align-items: center; justify-content: center; z-index: 1000;
    `;

    modal.innerHTML = `
        <div style="background: white; padding: 24px; border-radius: 8px; width: 90%; max-width: 500px;">
            <h3>編輯交易記錄</h3>
            <div style="margin: 4px 0 16px; font-size: 13px; color: #6B7280;">標的：<strong>${symbol}</strong></div>

            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold;">所屬策略 *</label>
                <select id="modal-trade-strategy" style="width: 100%; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; font-size: 14px;">
                    <option value="">-- 選擇策略 --</option>
                    ${strategyOptions}
                </select>
            </div>

            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold;">進場原因 *</label>
                <textarea id="modal-entry-reason" style="width: 100%; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; font-family: inherit; font-size: 14px;" rows="3">${currentEntryReason}</textarea>
            </div>

            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold;">備註</label>
                <textarea id="modal-trade-remark" style="width: 100%; padding: 8px; border: 1px solid #E5E7EB; border-radius: 4px; font-family: inherit; font-size: 14px;" rows="2"></textarea>
            </div>

            <div style="display: flex; gap: 12px;">
                <button id="save-trade-btn" style="flex: 1; padding: 12px; background: #5B47D9; color: white; border: none; border-radius: 4px; cursor: pointer;">儲存</button>
                <button id="cancel-trade-btn" style="flex: 1; padding: 12px; background: #E5E7EB; color: #1F2937; border: none; border-radius: 4px; cursor: pointer;">取消</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('save-trade-btn').addEventListener('click', async () => {
        const strategy = document.getElementById('modal-trade-strategy').value;
        const entryReason = document.getElementById('modal-entry-reason').value;
        const remark = document.getElementById('modal-trade-remark').value;

        if (!strategy) { alert('請選擇策略'); return; }
        if (!entryReason) { alert('請填寫進場原因'); return; }

        try {
            const response = await fetch(`${API_BASE_URL}/api/trades/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: tradeId,
                    symbol: symbol,
                    strategy: strategy,
                    entry_reason: entryReason,
                    entry_price: entryPrice,
                    quantity: quantity,
                    remark: remark
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                alert('交易記錄已更新！');
                modal.remove();
                loadTradingPage();
            } else {
                alert(`更新失敗: ${result.message}`);
            }
        } catch (error) {
            alert(`錯誤: ${error.message}`);
        }
    });

    document.getElementById('cancel-trade-btn').addEventListener('click', () => {
        modal.remove();
    });
}

function setupBrokerButtons() {
    const buttons = {
        'sync-ib': { name: 'IB API', endpoint: '/api/sync-broker-positions' },
        'sync-yuanta': { name: 'Yuanta API', endpoint: '/api/sync-broker-positions' },
        'sync-schwab': { name: 'Schwab API', endpoint: '/api/sync-broker-positions' }
    };

    Object.entries(buttons).forEach(([id, config]) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', async () => {
                btn.disabled = true;
                btn.textContent = '同步中...';

                try {
                    const response = await fetch(config.endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const result = await response.json();

                    if (result.status === 'success') {
                        alert(`✅ ${config.name} 同步成功！\n${result.message}`);
                        // 刷新持倉列表
                        await updateHoldings();
                    } else {
                        alert(`⚠️ ${config.name}\n${result.message}`);
                    }
                } catch (error) {
                    alert(`❌ ${config.name} 同步失敗\n${error.message}`);
                } finally {
                    btn.disabled = false;
                    btn.textContent = `同步 ${config.name}`;
                }
            });
        }
    });
}

// ============================================================================
// 策略管理頁面
// ============================================================================

async function loadStrategiesPage() {
    console.log('loadStrategiesPage called');
    try {
        // 設置上傳表單
        setupUploadForm();

        // 加載策略列表
        await loadStrategiesList();
    } catch (err) {
        console.error('Error loading strategies page:', err);
    }
}

function setupUploadForm() {
    const form = document.getElementById('upload-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData();
        const file = document.getElementById('csv-file').files[0];
        const strategyName = document.getElementById('strategy-name').value;
        const initialCapital = document.getElementById('initial-capital').value;

        if (!file) {
            showStatus('請選擇 CSV 檔案', 'error');
            return;
        }

        formData.append('file', file);
        formData.append('strategy_name', strategyName || 'Uploaded Strategy');
        formData.append('initial_capital', initialCapital || 100000);

        try {
            const response = await fetch(`${API_BASE_URL}/api/upload-csv`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.status === 'success') {
                showStatus(`成功！${result.message}`, 'success');
                form.reset();
                await loadStrategiesList();
            } else {
                showStatus(`錯誤：${result.message}`, 'error');
            }
        } catch (error) {
            showStatus(`上傳失敗：${error.message}`, 'error');
        }
    });
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('upload-status');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = type;
    }
}

async function loadStrategiesList() {
    const tbody = document.getElementById('strategies-body');
    if (!tbody) return;

    showLoading(tbody);

    try {
        const response = await fetch(`${API_BASE_URL}/api/strategies`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const strategies = result.strategies || result.data || [];

        tbody.innerHTML = '';

        if (strategies.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#9CA3AF;">暫無策略</td></tr>';
            hideLoading(tbody);
            return;
        }

        strategies.forEach(strategy => {
            const statusColor = strategy['狀態'] === '運行中' ? '#10B981' : '#6B7280';
            const statusBg = strategy['狀態'] === '運行中' ? '#ECFDF5' : '#F3F4F6';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${strategy['策略名稱'] || '-'}</strong></td>
                <td>
                    <span style="padding: 4px 8px; background: ${statusBg}; color: ${statusColor}; border-radius: 4px; font-size: 12px;">
                        ${strategy['狀態'] || '未知'}
                    </span>
                </td>
                <td>${strategy['策略類型'] || '-'}</td>
                <td>${strategy['起始資金'] || '-'}</td>
                <td>${strategy['幣別'] || '-'}</td>
                <td style="color: ${strategy.nav > 1 ? '#10B981' : '#EF4444'}">
                    ${strategy.nav ? (strategy.nav * 100).toFixed(2) + '%' : '-'}
                </td>
                <td>${strategy.trades_count || 0}</td>
                <td>
                    <button class="btn detail-btn" style="padding: 6px 12px; font-size: 12px;" data-strategy="${strategy['策略名稱']}">詳情</button>
                </td>
            `;
            tbody.appendChild(row);
        });

        // 綁定詳情按鈕事件
        document.querySelectorAll('.detail-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const strategyName = e.target.getAttribute('data-strategy');
                showStrategyDetail(strategyName);
            });
        });

        hideLoading(tbody);
    } catch (error) {
        console.error('Error loading strategies:', error);
        showToast(`❌ 加載策略失敗: ${error.message}`, 'error', 3000);
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#EF4444;">加載失敗，請重試</td></tr>';
        hideLoading(tbody);
    }
}

function showStrategyDetail(strategyName) {
    alert(`策略詳情: ${strategyName}\n\n此功能開發中`);
}

// ============================================================================
// 多策略對比頁面
// ============================================================================

async function loadComparisonPage() {
    const comparisonBody = document.getElementById('comparison-body');
    const chartContainer = document.getElementById('comparison-chart');

    if (comparisonBody) showLoading(comparisonBody);
    if (chartContainer) showLoading(chartContainer);

    try {
        const response = await fetch(`${API_BASE_URL}/api/strategies`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const strategies = result.strategies || result.data || [];

        if (comparisonBody) {
            if (strategies.length < 1) {
                comparisonBody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#9CA3AF;">暫無策略數據</td></tr>';
                hideLoading(comparisonBody);
            } else {
                comparisonBody.innerHTML = '';
                strategies.forEach(strategy => {
                    const row = document.createElement('tr');

                    // 簡單的評分計算 (Sharpe 40% + 回報 40% + 勝率 20%)
                    let score = 0;
                    if (strategy.cumret) {
                        score += 0.4 * parseFloat(strategy.cumret);
                    }
                    score = Math.max(0, Math.min(100, score));

                    row.innerHTML = `
                        <td><strong>${strategy['策略名稱'] || '-'}</strong></td>
                        <td>${strategy['策略類型'] || '-'}</td>
                        <td>${strategy.cumret || '-'}</td>
                        <td>${strategy.trades_count || 0}</td>
                        <td>${strategy.holding_count || 0}</td>
                        <td>
                            <div style="width: 100%; background: #E5E7EB; border-radius: 4px; height: 8px;">
                                <div style="width: ${score}%; background: linear-gradient(135deg, #5B47D9, #06B6D4); height: 100%; border-radius: 4px;"></div>
                            </div>
                            <small>${score.toFixed(1)}/100</small>
                        </td>
                    `;
                    comparisonBody.appendChild(row);
                });
                hideLoading(comparisonBody);
            }
        }

        // 加載 NAV 對比圖表
        await renderComparisonChart();

    } catch (error) {
        console.error('Error loading comparison data:', error);
        showToast(`❌ 加載對比數據失敗: ${error.message}`, 'error', 3000);
        if (comparisonBody) hideLoading(comparisonBody);
        if (chartContainer) hideLoading(chartContainer);
    }
}

async function renderComparisonChart() {
    const chartDiv = document.getElementById('comparison-chart');
    if (!chartDiv) return;

    showLoading(chartDiv);

    try {
        const response = await fetch(`${API_BASE_URL}/api/strategies/performance`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const perfData = result.data || {};

        const traces = [];
        const colors = ['#5B47D9', '#06B6D4', '#EC4899', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#14B8A6'];
        let colorIdx = 0;

        for (const [strategyName, navArray] of Object.entries(perfData)) {
            if (Array.isArray(navArray) && navArray.length > 0) {
                traces.push({
                    x: navArray.map(item => item.date),
                    y: navArray.map(item => item.nav),
                    mode: 'lines',
                    name: strategyName,
                    line: { color: colors[colorIdx % colors.length] }
                });
                colorIdx++;
            }
        }

        if (traces.length === 0) {
            chartDiv.innerHTML = '<p style="text-align:center; color:#9CA3AF;">暫無 NAV 數據</p>';
            hideLoading(chartDiv);
            return;
        }

        const layout = {
            title: '多策略 NAV 對比',
            xaxis: { title: '日期' },
            yaxis: { title: 'NAV' },
            hovermode: 'x unified',
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { l: 60, r: 40, t: 40, b: 60 }
        };

        Plotly.newPlot(chartDiv, traces, layout, { responsive: true, displayModeBar: false });
        hideLoading(chartDiv);

    } catch (error) {
        console.error('Error rendering comparison chart:', error);
        showToast(`❌ 加載圖表失敗: ${error.message}`, 'error', 3000);
        chartDiv.innerHTML = '<p style="text-align:center; color:#EF4444;">圖表加載失敗</p>';
        hideLoading(chartDiv);
    }
}

// ============================================================================
// 進階分析頁面
// ============================================================================

async function loadAnalysisPage() {
    const riskMetricsDiv = document.getElementById('risk-metrics');
    const chartDiv = document.getElementById('cumulative-chart');

    if (riskMetricsDiv) showLoading(riskMetricsDiv);
    if (chartDiv) showLoading(chartDiv);

    try {
        await Promise.all([
            renderRiskMetrics(),
            renderCumulativeChart(),
            renderDistributionChart()
        ]);
        generateAISuggestions();

        if (riskMetricsDiv) hideLoading(riskMetricsDiv);
        if (chartDiv) hideLoading(chartDiv);
    } catch (error) {
        console.error('Error loading analysis page:', error);
        showToast(`❌ 加載分析頁面失敗: ${error.message}`, 'error', 3000);
        if (riskMetricsDiv) hideLoading(riskMetricsDiv);
        if (chartDiv) hideLoading(chartDiv);
    }
}

async function renderRiskMetrics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/risk-metrics`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const metrics = result.metrics || {};

        const riskGrid = document.getElementById('risk-metrics');
        if (!riskGrid) return;

        riskGrid.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">Sharpe Ratio</div>
                    <div style="font-size: 24px; font-weight: bold; color: #5B47D9;">${metrics.sharpe_ratio || '-'}</div>
                </div>
                <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">最大回撤</div>
                    <div style="font-size: 24px; font-weight: bold; color: #EF4444;">${metrics.max_drawdown || '-'}</div>
                </div>
                <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">VaR 95%</div>
                    <div style="font-size: 24px; font-weight: bold; color: #F59E0B;">${metrics.var_95 || '-'}</div>
                </div>
                <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">樣本天數</div>
                    <div style="font-size: 24px; font-weight: bold; color: #06B6D4;">${metrics.total_days || '-'}</div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading risk metrics:', error);
        showToast(`❌ 加載風控指標失敗: ${error.message}`, 'error', 3000);
    }
}

async function renderCumulativeChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chart-data`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const data = result.data || result;

        if (!data || !data.dates) {
            const chartDiv = document.getElementById('cumulative-chart');
            if (chartDiv) chartDiv.innerHTML = '<p style="text-align:center; color:#9CA3AF;">暫無圖表數據</p>';
            return;
        }

        const trace = {
            x: data.dates,
            y: data.cumulative_returns,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#10B981', width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(16, 185, 129, 0.1)'
        };

        const layout = {
            title: 'Cumulative Returns',
            xaxis: { showgrid: true, gridcolor: '#F0E8FF' },
            yaxis: { showgrid: true, gridcolor: '#F0E8FF', title: 'Return (%)' },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { l: 50, r: 50, t: 40, b: 50 }
        };

        Plotly.newPlot('cumulative-chart', [trace], layout, { responsive: true, displayModeBar: false });
    } catch (error) {
        console.error('Error rendering cumulative chart:', error);
        showToast(`❌ 加載累積報酬圖失敗: ${error.message}`, 'error', 3000);
        const chartDiv = document.getElementById('cumulative-chart');
        if (chartDiv) chartDiv.innerHTML = '<p style="text-align:center; color:#EF4444;">圖表加載失敗</p>';
    }
}

async function renderDistributionChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chart-data`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const data = result.data || result;

        if (!data || !data.daily_returns) {
            const chartDiv = document.getElementById('distribution-chart');
            if (chartDiv) chartDiv.innerHTML = '<p style="text-align:center; color:#9CA3AF;">暫無分佈數據</p>';
            return;
        }

        const trace = {
            x: data.daily_returns,
            type: 'histogram',
            nbinsx: 40,
            marker: { color: 'rgba(16, 185, 129, 0.6)', line: { color: '#10B981' } }
        };

        const layout = {
            title: 'Daily Returns Distribution',
            xaxis: { title: 'Daily Return (%)' },
            yaxis: { title: 'Frequency' },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { l: 50, r: 50, t: 40, b: 50 }
        };

        Plotly.newPlot('distribution-chart', [trace], layout, { responsive: true, displayModeBar: false });
    } catch (error) {
        console.error('Error rendering distribution chart:', error);
        showToast(`❌ 加載分佈圖失敗: ${error.message}`, 'error', 3000);
        const chartDiv = document.getElementById('distribution-chart');
        if (chartDiv) chartDiv.innerHTML = '<p style="text-align:center; color:#EF4444;">圖表加載失敗</p>';
    }
}

// ============================================================================
// 波斯灣油輪監測頁面
// ============================================================================

async function loadShipMonitorPage() {
    console.log('Loading Ship Monitor Page');

    try {
        // 並行加載所有數據（快速）
        const [statsResponse, alertsResponse, vesselsResponse, waitingResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/ship-monitoring/statistics`),
            fetch(`${API_BASE_URL}/api/ship-monitoring/alerts`),
            fetch(`${API_BASE_URL}/api/ship-monitoring/vessels`),
            fetch(`${API_BASE_URL}/api/ship-monitoring/waiting-vessels?hours=6`)
        ]);

        const statsData = await statsResponse.json();
        const alertsData = await alertsResponse.json();
        const vesselsData = await vesselsResponse.json();
        const waitingData = await waitingResponse.json();

        // 更新統計卡片
        if (statsData.status === 'success') {
            const totalElem = document.getElementById('ship-total');
            const inRegionElem = document.getElementById('ship-in-region');
            const alertsElem = document.getElementById('ship-alerts');

            if (totalElem) totalElem.textContent = statsData.total_vessels;
            if (inRegionElem) inRegionElem.textContent = statsData.in_region;
            if (alertsElem) alertsElem.textContent = statsData.recent_alerts_24h;
        }

        // 更新等待中的船舶統計
        if (waitingData.status === 'success') {
            document.getElementById('ship-waiting').textContent = waitingData.count;
        }

        // 提取數據
        const vessels = vesselsData.status === 'success' ? (vesselsData.vessels || []) : [];
        const alerts = alertsData.status === 'success' ? (alertsData.alerts || []) : [];
        const waitingVessels = waitingData.status === 'success' ? (waitingData.vessels || []) : [];

        // 檢測船舶數據變化
        const currentData = JSON.stringify(vessels);
        if (lastShipData && lastShipData !== currentData) {
            shipDataChangedTime = new Date();
            showShipDataChangeNotification(vessels);
        }
        lastShipData = currentData;

        // 加載各個部分
        await loadShipList(vessels);
        await loadWaitingVessels(waitingVessels);
        await loadShipAlerts(alerts);

        // Ensure Leaflet is loaded before initializing map
        if (typeof L !== 'undefined') {
            initShipMap(vessels, alerts);
        } else {
            console.warn('Leaflet library not available, retrying in 1 second...');
            setTimeout(() => {
                if (typeof L !== 'undefined') {
                    initShipMap(vessels, alerts);
                } else {
                    console.error('Leaflet library failed to load');
                    const mapContainer = document.getElementById('ship-map');
                    if (mapContainer) {
                        mapContainer.innerHTML = '<div style="padding: 2rem; color: #e74c3c; text-align: center;">Leaflet 地圖庫加載失敗</div>';
                    }
                }
            }, 1000);
        }

        // 添加事件監聽
        setupShipMonitorControls();

        console.log('Ship Monitor Page loaded successfully');

    } catch (error) {
        console.error('Error loading ship monitor page:', error);
        const mapElem = document.getElementById('ship-map');
        if (mapElem) {
            mapElem.innerHTML = '<div style="text-align: center; padding: 2rem; color: #e74c3c;">地圖加載失敗: ' + error.message + '</div>';
        }
    }
}

async function loadWaitingVessels(waitingVessels) {
    try {
        const tableBody = document.getElementById('waiting-table-body');
        tableBody.innerHTML = '';

        if (!waitingVessels || waitingVessels.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #888;">目前無船舶等待超過 6 小時</td></tr>';
            return;
        }

        waitingVessels.forEach(vessel => {
            const countryInfo = getCountryInfo(vessel.flag);
            const waitingHours = vessel.waiting_duration_hours;
            const waitingColor = waitingHours > 24 ? '#EF4444' : (waitingHours > 12 ? '#F59E0B' : '#27ae60');

            const row = `
                <tr style="background: rgba(${waitingHours > 24 ? '239, 68, 68' : '245, 158, 11'}, 0.05);">
                    <td><strong>${vessel.vessel_name}</strong></td>
                    <td><code>${vessel.mmsi}</code></td>
                    <td><span style="color: ${waitingColor}; font-weight: bold; font-size: 14px;">${waitingHours} 小時<br><small>${vessel.waiting_duration_minutes} 分鐘</small></span></td>
                    <td><small>${vessel.origin_port || '未知'}</small></td>
                    <td><small>${vessel.destination || '未知'}</small></td>
                    <td><small>${vessel.latitude.toFixed(4)}°, ${vessel.longitude.toFixed(4)}°</small></td>
                    <td><span style="font-size: 18px;">${countryInfo.flag}</span><br><small>${countryInfo.name}</small></td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

        console.log(`Loaded ${waitingVessels.length} waiting vessels`);
    } catch (error) {
        console.error('Error loading waiting vessels:', error);
        document.getElementById('waiting-table-body').innerHTML =
            '<tr><td colspan="7" style="text-align: center; color: #e74c3c;">加載失敗</td></tr>';
    }
}

function getSpeedIndicator(speed) {
    // 判斷速度快慢
    if (speed === 0) return '🛑 停止';
    if (speed < 5) return '🐢 很慢';
    if (speed < 10) return '⚡ 中速';
    return '🚀 快速';
}

async function loadShipList(vessels) {
    try {
        const data = vessels ? { status: 'success', vessels: vessels } : await (await fetch(`${API_BASE_URL}/api/ship-monitoring/vessels`)).json();

        if (data.status === 'success' && data.vessels) {
            const tableBody = document.getElementById('ship-table-body');
            tableBody.innerHTML = '';

            data.vessels.forEach(vessel => {
                const statusIcon = vessel.speed > 1 ? '🟢 移動中' : '🟡 停止';
                const speedIndicator = getSpeedIndicator(vessel.speed);
                const speedColor = vessel.speed > 10 ? '#e74c3c' : (vessel.speed > 5 ? '#f39c12' : '#27ae60');

                // Get heading direction
                const heading = vessel.heading || 0;
                const directions = ['北', '北偏東', '東', '南偏東', '南', '南偏西', '西', '北偏西'];
                const directionIndex = Math.round(heading / 45) % 8;
                const headingText = directions[directionIndex] + '<br><small style="color: #999;">' + heading + '°</small>';

                // Get country flag info
                const countryInfo = getCountryInfo(vessel.flag);

                const row = `
                    <tr>
                        <td><strong>${vessel.vessel_name}</strong></td>
                        <td><code>${vessel.mmsi}</code></td>
                        <td><span style="color: ${speedColor}; font-weight: bold;">${vessel.speed.toFixed(1)} 節 ${speedIndicator}</span></td>
                        <td>${headingText}</td>
                        <td>${vessel.latitude.toFixed(4)}°, ${vessel.longitude.toFixed(4)}°</td>
                        <td>${statusIcon}</td>
                        <td><span style="font-size: 20px;">${countryInfo.flag}</span><br><small>${countryInfo.name}</small></td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });

            console.log(`Loaded ${data.vessels.length} vessels`);
        }
    } catch (error) {
        console.error('Error loading ship list:', error);
        document.getElementById('ship-table-body').innerHTML =
            '<tr><td colspan="7" style="text-align: center; color: #e74c3c;">加載失敗</td></tr>';
    }
}

function getAlertTypeLabel(alertType) {
    // 獲取告警類型標籤
    const labels = {
        'entered_region': '📍 進入監測區域',
        'exited_region': '✅ 離開監測區域',
        'stationary_alert': '🛑 停止不動',
        'speed_change': '⚡ 速度異常',
        'new_vessel_detected': '🆕 新船舶'
    };
    return labels[alertType] || '📢 ' + alertType;
}

async function loadShipAlerts(alerts) {
    try {
        const data = alerts ? { status: 'success', alerts: alerts } : await (await fetch(`${API_BASE_URL}/api/ship-monitoring/alerts`)).json();

        const logContainer = document.getElementById('ship-alerts-log');

        if (data.status === 'success' && data.alerts && data.alerts.length > 0) {
            let html = '';

            // 按時間排序（最新優先）
            const sortedAlerts = [...data.alerts].sort((a, b) =>
                new Date(b.timestamp) - new Date(a.timestamp)
            ).slice(0, 10); // 只顯示最新 10 個

            sortedAlerts.forEach(alert => {
                const severityColor = {
                    'high': '#e74c3c',
                    'medium': '#f39c12',
                    'low': '#27ae60'
                }[alert.severity] || '#95a5a6';

                const severityLabel = {
                    'high': '🔴 高優先級',
                    'medium': '🟡 中優先級',
                    'low': '🟢 低優先級'
                }[alert.severity] || '⚪ 未知';

                const timestamp = new Date(alert.timestamp).toLocaleTimeString('zh-TW');
                const alertTypeLabel = getAlertTypeLabel(alert.alert_type);

                // 添加額外信息
                let extraInfo = '';
                if (alert.duration_minutes) {
                    extraInfo += `<br>⏱️ 停止時間：${alert.duration_minutes.toFixed(0)} 分鐘`;
                }
                if (alert.speed_change_percent) {
                    extraInfo += `<br>📊 速度變化：${alert.speed_change_percent.toFixed(0)}%`;
                }

                html += `
                    <div style="padding: 1rem; border-left: 4px solid ${severityColor}; margin-bottom: 0.8rem; background: rgba(0,0,0,0.15); border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <div style="font-weight: bold; color: ${severityColor};">${alertTypeLabel}</div>
                            <div style="font-size: 11px; color: #888;">${timestamp}</div>
                        </div>
                        <div style="color: #fff; margin-bottom: 0.3rem;">
                            <strong>${alert.vessel_name}</strong> (${alert.mmsi})
                        </div>
                        <div style="font-size: 12px; color: #ccc; margin-bottom: 0.3rem;">
                            ${alert.message}
                        </div>
                        <div style="font-size: 11px; color: #888;">
                            優先級：${severityLabel}${extraInfo}
                        </div>
                    </div>
                `;
            });
            logContainer.innerHTML = html;
        } else {
            logContainer.innerHTML = '<div style="text-align: center; padding: 2rem; color: #888;">✅ 暫無告警</div>';
        }
    } catch (error) {
        console.error('Error loading ship alerts:', error);
        document.getElementById('ship-alerts-log').innerHTML =
            '<div style="text-align: center; color: #e74c3c;">加載失敗</div>';
    }
}

// ============================================================================
// 船舶數據變化通知
// ============================================================================

function showShipDataChangeNotification(vessels) {
    // 顯示數據更新通知

    // 檢查是否已有通知，避免重複
    let existingNotification = document.getElementById('ship-data-change-notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // 創建通知容器
    const notification = document.createElement('div');
    notification.id = 'ship-data-change-notification';
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        max-width: 350px;
        animation: slideIn 0.3s ease-out;
    `;

    const time = new Date().toLocaleTimeString();
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 20px;">🔄</div>
            <div style="flex: 1;">
                <div style="font-weight: 500; margin-bottom: 4px;">📍 波斯灣油輪數據已更新</div>
                <div style="font-size: 12px; opacity: 0.9;">
                    監測 ${vessels.length} 艘油輪 | ${time}
                </div>
                <div style="font-size: 12px; margin-top: 8px;">
                    <a href="https://www.marinetraffic.com/en/ais/home/centerx:56.9/centery:25.6/zoom:9"
                       target="_blank"
                       style="color: white; text-decoration: underline; font-weight: 500;">
                        查看 MarineTraffic 實時地圖 →
                    </a>
                </div>
            </div>
            <button onclick="this.parentElement.parentElement.style.display='none'"
                    style="background: rgba(255,255,255,0.3); border: none; color: white; cursor: pointer; padding: 4px 8px; border-radius: 4px; font-size: 16px;">
                ✕
            </button>
        </div>
    `;

    document.body.appendChild(notification);

    // 3 秒後自動隱藏
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// 添加通知動畫樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

function initShipMap(vessels, alerts) {
    console.log('initShipMap called');

    const mapContainer = document.getElementById('ship-map');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }

    if (typeof L === 'undefined') {
        console.error('Leaflet not loaded');
        mapContainer.innerHTML = '<div style="padding: 2rem; color: #e74c3c;">Leaflet 地圖庫加載失敗</div>';
        return;
    }

    try {
        if (window.shipMap) {
            window.shipMap.remove();
        }

        mapContainer.style.width = '100%';
        mapContainer.style.height = '400px';

        // Initialize marker storage
        const shipMarkers = {};

        const map = L.map('ship-map', {
            center: [27.5, 51.5],
            zoom: 7,
            layers: [L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            })]
        });

        window.shipMap = map;

        L.rectangle([[22, 44], [33, 59]], {
            color: '#06B6D4',
            weight: 3,
            opacity: 0.7,
            fill: true,
            fillColor: '#06B6D4',
            fillOpacity: 0.05,
            dashArray: '5, 5'
        }).addTo(map);

        L.popup({
            autoClose: false,
            closeButton: false
        })
            .setLatLng([27.5, 51.5])
            .setContent('<div style="background: rgba(6,182,212,0.9); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">波斯灣及周邊監測區域</div>')
            .addTo(map);

        if (vessels && vessels.length > 0) {
            vessels.forEach(vessel => {
            // Determine marker color and style based on speed
            const isMoving = vessel.speed > 1;
            const markerColor = isMoving ? '#10B981' : '#F59E0B';
            const heading = vessel.heading || 0;  // Get heading in degrees (0-360)

            // Convert heading to compass direction text
            const getHeadingText = (deg) => {
                const directions = ['北', '北偏東', '東', '南偏東', '南', '南偏西', '西', '北偏西'];
                const index = Math.round(deg / 45) % 8;
                return directions[index] + ' ' + deg + '°';
            };

            // Create arrow SVG marker (rotated based on heading)
            const arrowSVG = `
                <svg width="24" height="24" viewBox="0 0 24 24" style="transform: rotate(${heading}deg); transform-origin: center; filter: drop-shadow(0 0 2px rgba(0,0,0,0.5));">
                    <path d="M 12 2 L 20 16 L 16 16 L 16 22 L 8 22 L 8 16 L 4 16 Z" fill="${markerColor}" stroke="white" stroke-width="1.5"/>
                </svg>
            `;

            const markerIcon = L.divIcon({
                html: arrowSVG,
                iconSize: [24, 24],
                className: 'ship-marker-arrow'
            });

            const marker = L.marker([vessel.latitude, vessel.longitude], { icon: markerIcon }).addTo(map);

            // Create popup content
            const alertInfo = alerts.find(a => a.mmsi === vessel.mmsi);
            const alertHTML = alertInfo ? `
                <div style="color: #EF4444; margin-top: 4px; font-size: 12px;">
                    ⚠️ ${alertInfo.alert_type || '告警'} - ${alertInfo.message || ''}
                </div>
            ` : '';

            // Get country flag info
            const countryInfo = getCountryInfo(vessel.flag);
            const originPort = vessel.origin_port || '未知';
            const destinationPort = vessel.destination || '未知';

            const popupHTML = `
                <div class="ship-popup-content">
                    <div class="ship-popup-header">⚓ ${vessel.vessel_name}</div>
                    <div class="ship-popup-body">
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">MMSI:</span> ${vessel.mmsi}
                        </div>
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">位置:</span> ${vessel.latitude.toFixed(4)}°N, ${vessel.longitude.toFixed(4)}°E
                        </div>
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">速度:</span> ${vessel.speed.toFixed(1)} 節 ${isMoving ? '🚀' : '🛑'}
                        </div>
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">航向:</span> ${getHeadingText(heading)}
                        </div>
                        <div class="ship-popup-row" style="background: rgba(16, 185, 129, 0.1); padding: 8px; border-radius: 4px; margin: 4px 0;">
                            <span class="ship-popup-label">📍 起始港:</span> ${originPort}
                        </div>
                        <div class="ship-popup-row" style="background: rgba(239, 68, 68, 0.1); padding: 8px; border-radius: 4px; margin: 4px 0;">
                            <span class="ship-popup-label">🚩 目的港:</span> ${destinationPort}
                        </div>
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">船旗:</span> <span style="font-size: 20px;">${countryInfo.flag}</span> ${countryInfo.name}
                        </div>
                        <div class="ship-popup-row">
                            <span class="ship-popup-label">船型:</span> ${vessel.vessel_type || '未知'}
                        </div>
                        ${alertHTML}
                    </div>
                </div>
            `;

                marker.bindPopup(popupHTML);
                shipMarkers[vessel.mmsi] = marker;
            });
        }

        if (alerts && alerts.length > 0) {
            alerts.forEach(alert => {
            const vessel = vessels.find(v => v.mmsi === alert.mmsi);
            if (vessel) {
                const alertIcon = L.divIcon({
                    html: `<div style="background: #EF4444; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(239,68,68,0.6);">!</div>`,
                    iconSize: [18, 18],
                    className: 'alert-marker'
                });

                const alertMarker = L.marker([vessel.latitude, vessel.longitude], { icon: alertIcon }).addTo(map);

                // Get country flag info for alert popup
                const alertCountryInfo = getCountryInfo(vessel.flag);

                // Get port info for alert
                const alertOriginPort = vessel.origin_port || '未知';
                const alertDestinationPort = vessel.destination || '未知';

                const alertPopupHTML = `
                    <div class="ship-popup-content">
                        <div class="ship-popup-header" style="background: #EF4444;">🚨 告警: ${vessel.vessel_name}</div>
                        <div class="ship-popup-body">
                            <div class="ship-popup-row">
                                <span class="ship-popup-label">船旗:</span> <span style="font-size: 18px;">${alertCountryInfo.flag}</span> ${alertCountryInfo.name}
                            </div>
                            <div class="ship-popup-row" style="background: rgba(16, 185, 129, 0.1); padding: 8px; border-radius: 4px; margin: 4px 0;">
                                <span class="ship-popup-label">📍 起始港:</span> ${alertOriginPort}
                            </div>
                            <div class="ship-popup-row" style="background: rgba(239, 68, 68, 0.1); padding: 8px; border-radius: 4px; margin: 4px 0;">
                                <span class="ship-popup-label">🚩 目的港:</span> ${alertDestinationPort}
                            </div>
                            <div class="ship-popup-row">
                                <span class="ship-popup-label">事件:</span> ${getAlertTypeLabel(alert.alert_type)}
                            </div>
                            <div class="ship-popup-row">
                                <span class="ship-popup-label">嚴重性:</span> ${alert.severity === 'high' ? '🔴 高' : alert.severity === 'medium' ? '🟡 中' : '🟢 低'}
                            </div>
                            <div class="ship-popup-row">
                                <span class="ship-popup-label">時間:</span> ${new Date(alert.timestamp).toLocaleTimeString()}
                            </div>
                            <div class="ship-popup-row">
                                <span class="ship-popup-label">詳情:</span> ${alert.message || ''}
                            </div>
                        </div>
                    </div>
                `;

                    alertMarker.bindPopup(alertPopupHTML);
                }
            });
        }

        console.log('Map initialized successfully');
    } catch (err) {
        console.error('Map error:', err);
        if (mapContainer) {
            mapContainer.innerHTML = '<div style="padding: 2rem; color: #e74c3c;">地圖初始化失敗</div>';
        }
    }
}

function setupShipMonitorControls() {
    const refreshBtn = document.getElementById('refresh-ships');
    const autoToggleBtn = document.getElementById('auto-refresh-toggle');
    const helpBtn = document.getElementById('help-ships');

    if (refreshBtn) {
        refreshBtn.onclick = () => loadShipMonitorPage();
    }

    if (autoToggleBtn) {
        let autoRefreshInterval = null;
        autoToggleBtn.onclick = () => {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                autoToggleBtn.textContent = '⏱️ 自動刷新 (關)';
                autoToggleBtn.classList.remove('btn-primary');
                autoToggleBtn.classList.add('btn-secondary');
            } else {
                autoRefreshInterval = setInterval(() => loadShipMonitorPage(), 30000);
                autoToggleBtn.textContent = '⏱️ 自動刷新 (開)';
                autoToggleBtn.classList.remove('btn-secondary');
                autoToggleBtn.classList.add('btn-primary');
            }
        };
    }

    if (helpBtn) {
        helpBtn.onclick = () => {
            alert(`🚢 波斯灣油輪監測系統\n\n監測功能：\n• 實時 AIS 數據更新（每 30 秒）\n• 異常移動檢測（進/出區域、停止）\n• Telegram 即時告警\n• Google Sheets 自動同步\n\n與 Project Panopticon 整合：\n• M1 訂閱風險信號\n• S5 自動觸發對沖策略\n• R1 風控審核指令\n\n更多信息：SHIP_MONITORING_QUICK_START.md`);
        };
    }
}

function generateAISuggestions() {
    const container = document.getElementById('ai-suggestions');
    if (!container) return;

    container.innerHTML = `
        <h4 style="margin-bottom: 12px; color: #1A1A2E;">💡 AI 優化建議</h4>
        <p>✓ 建議增加止損設置以控制風險</p>
        <p>✓ 建議在高波動性時期降低倉位</p>
        <p>✓ 建議在市場相關性高時進行組合優化</p>
        <p>✓ 建議定期檢查策略參數是否需要調整</p>
        <p style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color); font-size: 12px; color: var(--text-tertiary);">
            💭 AI 建議基於歷史數據和機器學習模型，僅供參考。
        </p>
    `;
}

// ============================================================================
// 情報中心頁面（Intel Events）
// ============================================================================

async function loadIntelPage() {
    try {
        showLoading('intel-stats-grid', '加載中...');

        // 並行加載所有數據
        await Promise.all([
            loadIntelStats(),
            loadUSGSEarthquakes(),
            loadIntelEventsList(),
            loadRiskIncidentsList()
        ]);
    } catch (error) {
        console.error('Error loading intel page:', error);
        showToast('情報頁面加載失敗: ' + error.message, 'error');
    }
}

async function loadIntelStats() {
    try {
        const [eventsRes, incidentsRes, usgsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/intel/events`),
            fetch(`${API_BASE_URL}/api/risk-incidents`),
            fetch(`${API_BASE_URL}/api/intel/usgs`)
        ]);

        const events = await eventsRes.json();
        const incidents = await incidentsRes.json();
        const usgs = await usgsRes.json();

        const statsGrid = document.getElementById('intel-stats-grid');
        const maxIntelRisk = events.events?.length > 0
            ? Math.max(...events.events.map(e => e.risk_score || 0)).toFixed(2)
            : '0.00';

        statsGrid.innerHTML = `
            <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">今日事件</div>
                <div style="font-size: 24px; font-weight: bold; color: #5B47D9;">${events.events?.length || 0}</div>
            </div>
            <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">最高風險分</div>
                <div style="font-size: 24px; font-weight: bold; color: ${maxIntelRisk > 5 ? '#EF4444' : '#10B981'};">${maxIntelRisk}</div>
            </div>
            <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">地震數量</div>
                <div style="font-size: 24px; font-weight: bold; color: #F59E0B;">${usgs.count || 0}</div>
            </div>
            <div style="padding: 16px; background: #F3F4F6; border-radius: 8px;">
                <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">風控事件</div>
                <div style="font-size: 24px; font-weight: bold; color: #06B6D4;">${incidents.incidents?.length || 0}</div>
            </div>
        `;

        hideLoading('intel-stats-grid');
    } catch (error) {
        console.error('Error loading intel stats:', error);
        showToast('統計加載失敗', 'error');
    }
}

async function loadUSGSEarthquakes() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/intel/usgs`);
        const data = await response.json();

        const tbody = document.getElementById('earthquake-table-body');
        if (!tbody) return;

        if (!data.earthquakes || data.earthquakes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 24px; color: #9CA3AF;">無最近地震記錄</td></tr>';
            return;
        }

        tbody.innerHTML = data.earthquakes.map(eq => `
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 12px;">${new Date(eq.time).toLocaleString('zh-TW')}</td>
                <td style="padding: 12px;"><strong>${eq.location}</strong></td>
                <td style="padding: 12px; color: ${eq.magnitude > 6 ? '#EF4444' : eq.magnitude > 5 ? '#F59E0B' : '#10B981'}; font-weight: bold;">
                    ${eq.magnitude.toFixed(1)} M
                </td>
                <td style="padding: 12px;">${eq.depth_km.toFixed(1)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading USGS earthquakes:', error);
        const tbody = document.getElementById('earthquake-table-body');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px; color: #EF4444;">地震數據加載失敗</td></tr>`;
        }
    }
}

async function loadIntelEventsList() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/intel/events`);
        const data = await response.json();

        const container = document.getElementById('intel-events-log');
        if (!container) return;

        if (!data.events || data.events.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #9CA3AF; padding: 24px;">無情報事件</p>';
            return;
        }

        container.innerHTML = data.events.slice(-10).reverse().map(event => `
            <div style="padding: 12px; background: var(--bg-secondary); border-left: 4px solid #06B6D4; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <strong>${event.event_type}</strong>
                    <span style="font-size: 12px; color: #6B7280;">${new Date(event.date).toLocaleString('zh-TW')}</span>
                </div>
                <div style="font-size: 14px; margin-bottom: 4px;">${event.summary}</div>
                <div style="display: flex; gap: 8px; font-size: 12px;">
                    <span style="padding: 2px 6px; background: #E5E7EB; border-radius: 3px;">${event.location}</span>
                    <span style="padding: 2px 6px; background: #E5E7EB; border-radius: 3px;">風險: ${event.risk_score?.toFixed(2) || '0.00'}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading intel events:', error);
        const container = document.getElementById('intel-events-log');
        if (container) {
            container.innerHTML = `<p style="color: #EF4444;">情報事件加載失敗</p>`;
        }
    }
}

async function loadRiskIncidentsList() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/risk-incidents`);
        const data = await response.json();

        const tbody = document.getElementById('risk-incidents-table-body');
        if (!tbody) return;

        if (!data.incidents || data.incidents.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 24px; color: #9CA3AF;">無風控事件</td></tr>';
            return;
        }

        tbody.innerHTML = data.incidents.slice(-20).reverse().map(incident => {
            const severityColor = incident.severity === '高' ? '#EF4444' : incident.severity === '中' ? '#F59E0B' : '#10B981';
            return `
                <tr style="border-bottom: 1px solid var(--border-color);">
                    <td style="padding: 12px; font-size: 12px;">${incident.time}</td>
                    <td style="padding: 12px;">${incident.event_type}</td>
                    <td style="padding: 12px;">
                        <span style="padding: 2px 8px; background: ${severityColor}20; color: ${severityColor}; border-radius: 3px; font-size: 12px;">
                            ${incident.severity}
                        </span>
                    </td>
                    <td style="padding: 12px; font-size: 12px;">${incident.description || '-'}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading risk incidents:', error);
        const tbody = document.getElementById('risk-incidents-table-body');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px; color: #EF4444;">風控日誌加載失敗</td></tr>`;
        }
    }
}

// ============================================================================
// 宏觀經濟儀表板
// ============================================================================

async function loadMacroDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/macro-state`);
        const data = await response.json();

        const dashboard = document.getElementById('macro-dashboard');
        if (!dashboard) return;

        const macro = data.macro_state || {};
        const riskOnColor = macro.risk_on === 'ON' ? '#10B981' : macro.risk_on === 'NEUTRAL' ? '#F59E0B' : '#EF4444';
        const riskOnText = macro.risk_on === 'ON' ? '風險開啟（買方）' : macro.risk_on === 'NEUTRAL' ? '中立' : '風險關閉（賣方）';

        dashboard.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px; border-left: 4px solid ${riskOnColor};">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">Risk-On 開關</div>
                    <div style="font-size: 20px; font-weight: bold; color: ${riskOnColor};">${riskOnText}</div>
                    <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">更新: ${macro.update_time ? new Date(macro.update_time).toLocaleString('zh-TW') : '未知'}</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px; border-left: 4px solid #06B6D4;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">VIX 水平</div>
                    <div style="font-size: 20px; font-weight: bold; color: #06B6D4;">${macro.vix_level || 'NORMAL'}</div>
                    <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">波動性指標</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px; border-left: 4px solid #F59E0B;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">油價影響</div>
                    <div style="font-size: 20px; font-weight: bold; color: #F59E0B;">${macro.oil_impact || '中性'}</div>
                    <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">能源資產敏感度</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px; border-left: 4px solid #5B47D9;">
                    <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">Intel 風險分</div>
                    <div style="font-size: 20px; font-weight: bold; color: #5B47D9;">${macro.latest_intel_risk?.toFixed(2) || '0.00'}</div>
                    <div style="font-size: 11px; color: #9CA3AF; margin-top: 8px;">24 小時最高</div>
                </div>
            </div>
            <div style="margin-top: 16px; padding: 12px; background: #F9F7FF; border-radius: 6px; border-left: 3px solid #5B47D9;">
                <div style="font-size: 12px; color: #6B7280;">市場信號</div>
                <div style="font-size: 14px; color: #1A1A2E; margin-top: 4px;">${macro.market_signal || '無新信號'}</div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading macro dashboard:', error);
        const dashboard = document.getElementById('macro-dashboard');
        if (dashboard) {
            dashboard.innerHTML = `<div style="padding: 16px; color: #EF4444;">宏觀儀表板加載失敗</div>`;
        }
    }
}

// ============================================================================
// 響應式圖表調整
// ============================================================================

window.addEventListener('resize', () => {
    const charts = ['price-chart', 'cumulative-chart', 'distribution-chart', 'comparison-chart'];
    charts.forEach(chartId => {
        const element = document.getElementById(chartId);
        if (element && element.offsetParent !== null) {
            Plotly.Plots.resize(chartId);
        }
    });
});

console.log('Dashboard.js loaded successfully!');

// ============================================================================
// Broker 數據同步功能
// ============================================================================

async function syncAllBrokers() {
    const btn = document.getElementById('sync-all-btn');
    const statusDiv = document.getElementById('sync-status');
    const statusText = document.getElementById('sync-status-text');

    try {
        btn.disabled = true;
        btn.textContent = '⏳ 同步中...';
        statusDiv.style.display = 'block';
        statusText.textContent = '正在同步所有 Broker...';

        const response = await fetch('/api/brokers/sync-all', { method: 'POST' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        let message = `✅ 同步完成\n`;
        message += `IB: ${data.results.ib.status || '未知'}`;
        if (data.results.ib.added) message += ` (+${data.results.ib.added})`;
        if (data.results.ib.skipped) message += ` (跳過${data.results.ib.skipped})`;
        message += `\n`;
        message += `Yuanta: ${data.results.yuanta.status || '未知'}`;
        if (data.results.yuanta.added) message += ` (+${data.results.yuanta.added})`;
        if (data.results.yuanta.skipped) message += ` (跳過${data.results.yuanta.skipped})`;
        if (data.results.yuanta.message) message += `\n(${data.results.yuanta.message})`;

        statusText.textContent = message;
        console.log('Sync results:', data);

        // 3 秒後刷新持仓数据
        setTimeout(() => location.reload(), 3000);

    } catch (error) {
        statusText.textContent = `⚠️ 同步結果：${error.message}\n請手動點擊個別 Broker 按鈕查看詳情`;
        console.error('Sync error:', error);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 全部同步';
    }
}

async function syncBroker(broker) {
    const btnId = `sync-${broker}-btn`;
    const btn = document.getElementById(btnId);
    const statusDiv = document.getElementById('sync-status');
    const statusText = document.getElementById('sync-status-text');

    try {
        btn.disabled = true;
        btn.textContent = `⏳ 同步中...`;
        statusDiv.style.display = 'block';

        let endpoint = '';
        let brokerName = '';

        switch(broker) {
            case 'ib':
                endpoint = '/api/ib/sync';
                brokerName = 'IB';
                break;
            case 'yuanta':
                endpoint = '/api/yuanta/sync';
                brokerName = 'Yuanta';
                break;
            case 'schwab':
                window.location.href = '/schwab';
                return;
            default:
                throw new Error('未知 Broker');
        }

        const response = await fetch(endpoint, { method: 'POST' });
        const data = await response.json();

        let message = `✅ ${brokerName} 同步完成\n`;
        message += `新增: ${data.added || 0} 筆\n`;
        message += `跳過: ${data.skipped || 0} 筆`;

        statusText.textContent = message;
        console.log(`${brokerName} sync result:`, data);

        // 2 秒後刷新
        setTimeout(() => location.reload(), 2000);

    } catch (error) {
        statusText.textContent = `❌ ${broker} 同步失敗: ${error.message}`;
        console.error(`${broker} sync error:`, error);
    } finally {
        btn.disabled = false;
        const icons = { ib: '🏦', yuanta: '🏪', schwab: '🔐' };
        btn.textContent = `${icons[broker]} ${broker.toUpperCase()}`;
    }
}

// ============================================================================
// 自動檢查持倉變化功能
// ============================================================================

let lastPositionsSnapshot = null;  // 上次的持倉快照

/**
 * 自動檢查持倉變化並同步
 */
async function autoCheckAndSync() {
    console.log('🔄 正在檢查持倉變化...');

    try {
        // 獲取當前持倉
        const response = await fetch('/api/holdings/check-changes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positions: lastPositionsSnapshot || [] })
        });

        const result = await response.json();

        if (result.status !== 'success') {
            console.warn('檢查持倉變化失敗:', result.message);
            return;
        }

        // 更新快照
        lastPositionsSnapshot = result.current_positions;

        // 如果有變化，立即同步
        if (result.has_changes) {
            const changes = result.changes;
            console.log('📊 檢測到持倉變化:', {
                新增: changes.added.length,
                刪除: changes.removed.length,
                修改: changes.modified.length
            });

            // 顯示通知
            showPositionChangeNotification(changes);

            // 立即同步
            if (changes.added.length > 0 || changes.removed.length > 0 || changes.modified.length > 0) {
                console.log('🔄 檢測到變化，立即同步所有 Broker...');
                await triggerAutoSync();
            }
        } else {
            console.log('✅ 無持倉變化');
        }

    } catch (error) {
        console.error('自動檢查與同步時出錯:', error);
    }
}

/**
 * 顯示持倉變化通知
 */
function showPositionChangeNotification(changes) {
    let message = '📊 檢測到持倉變化:\n';

    if (changes.added.length > 0) {
        message += `✨ 新增 ${changes.added.length} 個持倉\n`;
        changes.added.forEach(p => {
            message += `  - ${p.symbol}: ${p.position} 股 @ $${p.avgCost}\n`;
        });
    }

    if (changes.removed.length > 0) {
        message += `🗑️ 刪除 ${changes.removed.length} 個持倉\n`;
        changes.removed.forEach(p => {
            message += `  - ${p.symbol}: 已平倉\n`;
        });
    }

    if (changes.modified.length > 0) {
        message += `📈 修改 ${changes.modified.length} 個持倉\n`;
        changes.modified.forEach(p => {
            message += `  - ${p.symbol}: ${p.previous_position} → ${p.current_position}\n`;
        });
    }

    // 顯示在頁面上
    const notificationArea = document.getElementById('notification-area');
    if (notificationArea) {
        notificationArea.style.display = 'block';
        notificationArea.innerHTML = `
            <div style="background: #e0f7fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #00bcd4;">
                <strong>🔔 持倉變化警報</strong><br>
                ${message.replace(/\n/g, '<br>')}
            </div>
        `;
        setTimeout(() => {
            if (notificationArea) {
                notificationArea.style.display = 'none';
                notificationArea.innerHTML = '';
            }
        }, 10000);  // 10 秒後自動清除
    }
}

/**
 * 自動觸發同步所有 Broker
 */
async function triggerAutoSync() {
    console.log('🔄 自動同步所有 Broker...');

    try {
        // 調用全部同步 API
        const response = await fetch('/api/brokers/sync-all', { method: 'POST' });
        const result = await response.json();

        console.log('✅ 自動同步完成:', result);

        // 更新快照
        const holdingsResponse = await fetch('/api/holdings');
        const holdingsData = await holdingsResponse.json();
        if (holdingsData.status === 'success') {
            lastPositionsSnapshot = holdingsData.data;
        }

    } catch (error) {
        console.error('自動同步失敗:', error);
    }
}

/**
 * 渲染每日損益趨勢圖（雙 Y 軸：IB (USD) 左軸、Yuanta (TWD) 右軸）
 */
async function renderPerformanceTrendChart() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/daily-performance`);
        const result = await response.json();
        const data = result.data || {};

        const chartDiv = document.getElementById('performance-trend-chart');
        if (!chartDiv) return;

        if (!data.dates || data.dates.length === 0) {
            chartDiv.innerHTML = '<p style="color:#9CA3AF; text-align:center; padding:40px;">暫無歷史數據</p>';
            return;
        }

        // 更新指標卡片
        updatePerformanceCards(data);

        // 4 條線：IB 未實現、IB 已實現、Yuanta 未實現、Yuanta 已實現
        // 支持新舊格式：如果沒有新格式，使用舊格式或空數組
        const ib_unrealized_data = data.ib_unrealized || data.unrealized_pl || [];
        const ib_realized_data = data.ib_realized || data.realized_pl || [];
        const yuanta_unrealized_data = data.yuanta_unrealized || [];
        const yuanta_realized_data = data.yuanta_realized || [];

        const traces = [
            {
                x: data.dates,
                y: ib_unrealized_data,
                name: '🏦 IB 未實現 (USD)',
                yaxis: 'y',
                mode: 'lines+markers',
                line: { color: '#3B82F6', width: 3, shape: 'spline' },
                marker: { size: 6, symbol: 'circle' },
                fill: 'tozeroy',
                fillcolor: 'rgba(59,130,246,0.08)'
            },
            {
                x: data.dates,
                y: ib_realized_data,
                name: '🏦 IB 已實現 (USD)',
                yaxis: 'y',
                mode: 'lines+markers',
                line: { color: '#06B6D4', width: 2, dash: 'dash' },
                marker: { size: 5 }
            },
            {
                x: data.dates,
                y: yuanta_unrealized_data,
                name: '🏪 元大 未實現 (TWD)',
                yaxis: 'y2',
                mode: 'lines+markers',
                line: { color: '#F59E0B', width: 3, shape: 'spline' },
                marker: { size: 6, symbol: 'circle' },
                fill: 'tozeroy',
                fillcolor: 'rgba(245,158,11,0.06)'
            },
            {
                x: data.dates,
                y: yuanta_realized_data,
                name: '🏪 元大 已實現 (TWD)',
                yaxis: 'y2',
                mode: 'lines+markers',
                line: { color: '#10B981', width: 2, dash: 'dash' },
                marker: { size: 5 }
            }
        ];

        const layout = {
            xaxis: {
                title: '日期',
                showgrid: true,
                gridcolor: '#F3F4F6',
                rangeslider: { visible: true }
            },
            yaxis: {
                title: 'USD',
                titlefont: { color: '#3B82F6', size: 12 },
                showgrid: true,
                gridcolor: '#EFF6FF',
                zeroline: true,
                zerolinecolor: '#E5E7EB',
                zerolinewidth: 1,
                tickformat: '.0f'
            },
            yaxis2: {
                title: 'TWD',
                titlefont: { color: '#F59E0B', size: 12 },
                overlaying: 'y',
                side: 'right',
                showgrid: false,
                zeroline: false,
                tickformat: '.0f'
            },
            legend: {
                x: 0,
                y: 1.1,
                orientation: 'h',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#E5E7EB',
                borderwidth: 1,
                xanchor: 'left',
                yanchor: 'top'
            },
            hovermode: 'x unified',
            plot_bgcolor: '#FAFAFA',
            paper_bgcolor: 'white',
            margin: { l: 60, r: 60, t: 30, b: 80 },
            shapes: [{
                type: 'line',
                xref: 'paper',
                yref: 'y',
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 0,
                line: { color: '#E5E7EB', width: 1 }
            }]
        };

        Plotly.newPlot('performance-trend-chart', traces, layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
            displaylogo: false
        });
    } catch (error) {
        console.error('Error rendering performance chart:', error);
        const chartDiv = document.getElementById('performance-trend-chart');
        if (chartDiv) {
            chartDiv.innerHTML = `<p style="color:#EF4444;">❌ 加載圖表失敗</p>`;
        }
    }
}

/**
 * 更新指標卡片數值與顏色（支持新舊格式）
 */
function updatePerformanceCards(data) {
    const latestIdx = data.dates ? data.dates.length - 1 : -1;
    if (latestIdx < 0) return;

    const formatUSD = (v) => v !== undefined && v !== null ? (v >= 0 ? `+$${v.toFixed(2)}` : `-$${Math.abs(v).toFixed(2)}`) : '$0.00';
    const formatTWD = (v) => v !== undefined && v !== null ? (v >= 0 ? `+NT$${v.toFixed(0)}` : `-NT$${Math.abs(v).toFixed(0)}`) : 'NT$0';
    const getColor = (v) => v !== undefined && v !== null ? (v >= 0 ? '#10B981' : '#EF4444') : '#9CA3AF';

    // 檢查是否有新格式數據，沒有則使用舊格式或默認值
    const ib_unrealized = data.ib_unrealized ? (data.ib_unrealized[latestIdx] || 0) : (data.unrealized_pl ? data.unrealized_pl[latestIdx] : 0);
    const ib_realized = data.ib_realized ? (data.ib_realized[latestIdx] || 0) : (data.realized_pl ? data.realized_pl[latestIdx] : 0);
    const yuanta_unrealized = data.yuanta_unrealized ? (data.yuanta_unrealized[latestIdx] || 0) : 0;
    const yuanta_realized = data.yuanta_realized ? (data.yuanta_realized[latestIdx] || 0) : 0;

    setCard('card-ib-unrealized', '🏦 IB 未實現', formatUSD(ib_unrealized), 'USD', getColor(ib_unrealized));
    setCard('card-ib-realized', '🏦 IB 已實現', formatUSD(ib_realized), 'USD', getColor(ib_realized));
    setCard('card-yuanta-unrealized', '🏪 元大 未實現', formatTWD(yuanta_unrealized), 'TWD', getColor(yuanta_unrealized));
    setCard('card-yuanta-realized', '🏪 元大 已實現', formatTWD(yuanta_realized), 'TWD', getColor(yuanta_realized));
}

/**
 * 設置單個指標卡片
 */
function setCard(cardId, label, value, currency, color) {
    const card = document.getElementById(cardId);
    if (!card) return;

    const valueDiv = card.querySelector('div:nth-child(2)');
    const currencyDiv = card.querySelector('div:nth-child(3)');

    if (valueDiv) {
        valueDiv.textContent = value;
        valueDiv.style.color = color;
    }
    if (currencyDiv) {
        currencyDiv.textContent = currency;
    }
}

/**
 * 手動記錄今日損益
 */
async function recordTodayPerformance() {
    try {
        const btn = document.getElementById('record-performance-btn');
        if (btn) btn.disabled = true;

        const res = await fetch(`${API_BASE_URL}/api/daily-performance/record`, { method: 'POST' });
        const result = await res.json();

        if (result.status === 'success') {
            showToast(`✅ 已記錄 ${result.date}：未實現=${result.unrealized_pl}, 已實現=${result.realized_pl}`, 'success', 3000);
            // 刷新圖表
            await renderPerformanceTrendChart();
        } else if (result.status === 'skipped') {
            showToast(`⚠️ ${result.message}`, 'info', 2000);
        } else {
            showToast(`❌ 記錄失敗：${result.message}`, 'error', 3000);
        }

        if (btn) btn.disabled = false;
    } catch (error) {
        console.error('Error recording performance:', error);
        showToast(`❌ 記錄失敗：${error.message}`, 'error', 3000);
        const btn = document.getElementById('record-performance-btn');
        if (btn) btn.disabled = false;
    }
}

/**
 * 初始化頁面加載時同步
 */
function initPageLoadSync() {
    console.log('🚀 頁面已加載，開始自動檢查與同步...');

    // 首先獲取初始快照
    fetch('/api/holdings')
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') {
                lastPositionsSnapshot = data.data;
                console.log('✅ 已讀取 ' + data.data.length + ' 個持倉');

                // 然後檢查變化並同步
                autoCheckAndSync();
            }
        })
        .catch(e => console.warn('初始化失敗:', e));
}

// ============================================================================
// 已實現交易相關函數
// ============================================================================

/**
 * 加載已實現交易
 */
async function loadRealizedTrades() {
    const container = document.getElementById('realized-trades-container');
    if (!container) return;

    try {
        container.innerHTML = '<div class="loading">加載已實現交易中...</div>';

        const response = await fetch(`${API_BASE_URL}/api/trades/realized`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();
        const trades = result.data || [];

        // 更新策略篩選選項
        if (trades.length > 0) {
            const strategies = [...new Set(trades.map(t => t['策略']).filter(Boolean))];
            const filterSelect = document.getElementById('realized-trades-strategy-filter');
            if (filterSelect) {
                strategies.forEach(strategy => {
                    const option = document.createElement('option');
                    option.value = strategy;
                    option.textContent = strategy;
                    filterSelect.appendChild(option);
                });

                // 添加篩選事件
                filterSelect.addEventListener('change', () => filterAndDisplayTrades(trades));
            }
        }

        // 初始顯示
        displayRealizedTrades(trades);

        // 添加搜尋事件
        const searchInput = document.getElementById('realized-trades-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => filterAndDisplayTrades(trades));
        }

    } catch (err) {
        console.error('加載已實現交易失敗:', err);
        container.innerHTML = `<p style="color: #EF4444;">❌ 加載失敗: ${err.message}</p>`;
    }
}

/**
 * 篩選和顯示交易
 */
function filterAndDisplayTrades(allTrades) {
    const searchInput = document.getElementById('realized-trades-search');
    const strategyFilter = document.getElementById('realized-trades-strategy-filter');

    let filtered = allTrades;

    // 按策略篩選
    if (strategyFilter && strategyFilter.value) {
        filtered = filtered.filter(t => t['策略'] === strategyFilter.value);
    }

    // 按關鍵字搜尋
    if (searchInput && searchInput.value) {
        const keyword = searchInput.value.toLowerCase();
        filtered = filtered.filter(t =>
            (t['標的'] && t['標的'].toLowerCase().includes(keyword)) ||
            (t['策略'] && t['策略'].toLowerCase().includes(keyword))
        );
    }

    displayRealizedTrades(filtered);
}

/**
 * 顯示已實現交易列表
 */
function displayRealizedTrades(trades) {
    const container = document.getElementById('realized-trades-container');
    if (!container) return;

    if (!trades || trades.length === 0) {
        container.innerHTML = '<p style="padding: 20px; color: #9CA3AF; text-align: center;">暫無已實現交易</p>';
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';

    trades.forEach((trade, idx) => {
        const symbol = trade['標的'] || '-';
        const strategy = trade['策略'] || '-';
        const entryPrice = trade['進場價'] || '-';
        const exitPrice = trade['出場價'] || '-';
        const quantity = trade['數量'] || '-';
        const status = trade['狀態'] || '-';
        const pnl = trade['pnl'] ? parseFloat(trade['pnl']).toFixed(2) : '-';
        const date = trade['日期'] || '-';

        const pnlColor = pnl === '-' ? '#9CA3AF' : (parseFloat(pnl) >= 0 ? '#22C55E' : '#EF4444');

        html += `
            <div class="trade-item" onclick="openTradeDetailModal(${idx}, ${JSON.stringify(trade).replace(/"/g, '&quot;')})"
                 style="
                    padding: 12px;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.2s;
                    background: #F9FAFB;
                 "
                 onmouseover="this.style.background = '#F3F4F6'; this.style.borderColor = '#3B82F6';"
                 onmouseout="this.style.background = '#F9FAFB'; this.style.borderColor = '#E5E7EB';">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 12px; align-items: center;">
                    <div>
                        <strong style="font-size: 16px;">${symbol}</strong>
                        <div style="font-size: 12px; color: #6B7280; margin-top: 4px;">策略: ${strategy} | 日期: ${date}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #6B7280;">進場</div>
                        <div>${entryPrice}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #6B7280;">出場</div>
                        <div>${exitPrice}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: #6B7280;">數量</div>
                        <div>${quantity}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 12px; color: #6B7280;">損益</div>
                        <div style="color: ${pnlColor}; font-weight: bold; font-size: 14px;">${pnl}</div>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * 打開交易詳情模態窗口
 */
function openTradeDetailModal(idx, trade) {
    const modal = document.getElementById('trade-detail-modal');
    const body = document.getElementById('trade-detail-body');
    const title = document.getElementById('trade-detail-title');

    if (!modal || !body) return;

    const symbol = trade['標的'] || '-';
    const strategy = trade['策略'] || '-';
    const date = trade['日期'] || '-';
    const entryPrice = trade['進場價'] || '-';
    const exitPrice = trade['出場價'] || '-';
    const quantity = trade['數量'] || '-';
    const entryReason = trade['進場原因'] || '未記錄';
    const exitReason = trade['出場原因'] || '未記錄';
    const status = trade['狀態'] || '-';
    const pnl = trade['pnl'] ? parseFloat(trade['pnl']).toFixed(2) : '-';
    const notes = trade['備註'] || '無備註';

    title.textContent = `交易詳情 - ${symbol} (${strategy})`;

    const pnlColor = pnl === '-' ? '#9CA3AF' : (parseFloat(pnl) >= 0 ? '#22C55E' : '#EF4444');

    body.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; background: #F3F4F6; border-radius: 8px;">
            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">標的代碼</label>
                <div style="font-size: 20px; font-weight: bold; margin-top: 4px;">${symbol}</div>
            </div>
            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">所屬策略</label>
                <div style="font-size: 18px; font-weight: bold; margin-top: 4px; color: #3B82F6;">${strategy}</div>
            </div>

            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">交易日期</label>
                <div style="font-size: 16px; margin-top: 4px;">${date}</div>
            </div>
            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">交易狀態</label>
                <div style="font-size: 16px; margin-top: 4px;">${status}</div>
            </div>

            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">進場價</label>
                <div style="font-size: 18px; margin-top: 4px;">${entryPrice}</div>
            </div>
            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">出場價</label>
                <div style="font-size: 18px; margin-top: 4px;">${exitPrice}</div>
            </div>

            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">數量</label>
                <div style="font-size: 18px; margin-top: 4px;">${quantity} 股</div>
            </div>
            <div>
                <label style="font-size: 12px; color: #6B7280; text-transform: uppercase; font-weight: 600;">損益</label>
                <div style="font-size: 20px; margin-top: 4px; color: ${pnlColor}; font-weight: bold;">${pnl}</div>
            </div>
        </div>

        <div style="margin-top: 16px;">
            <h4 style="margin-bottom: 8px; color: #1F2937;">進場原因</h4>
            <div style="padding: 12px; background: #E0F2FE; border-left: 4px solid #0284C7; border-radius: 4px; font-size: 14px;">
                ${entryReason}
            </div>
        </div>

        <div style="margin-top: 16px;">
            <h4 style="margin-bottom: 8px; color: #1F2937;">出場原因</h4>
            <div style="padding: 12px; background: #FEE2E2; border-left: 4px solid #DC2626; border-radius: 4px; font-size: 14px;">
                ${exitReason}
            </div>
        </div>

        <div style="margin-top: 16px;">
            <h4 style="margin-bottom: 8px; color: #1F2937;">備註</h4>
            <div style="padding: 12px; background: #ECFDF5; border-left: 4px solid #059669; border-radius: 4px; font-size: 14px;">
                ${notes}
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

/**
 * 關閉交易詳情模態窗口
 */
function closeTradDetailModal() {
    const modal = document.getElementById('trade-detail-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ============================================================================
// 當前交易相關函數
// ============================================================================

/**
 * 加載當前交易
 */
async function loadCurrentTrades() {
    const container = document.getElementById('current-trades-container');
    if (!container) return;

    try {
        container.innerHTML = '<div class="loading">加載當前交易中...</div>';

        // 直接使用已驗證可行的 API：/api/holdings/by-broker
        const response = await fetch(`${API_BASE_URL}/api/holdings/by-broker`);
        if (!response.ok) throw new Error(`API 錯誤: ${response.status}`);

        const result = await response.json();

        // 將 IB 和 Yuanta 的持倉合併為一個陣列
        let trades = [];
        if (result.ib && result.ib.positions) {
            trades = trades.concat(result.ib.positions);
        }
        if (result.yuanta && result.yuanta.positions) {
            trades = trades.concat(result.yuanta.positions);
        }

        // 映射欄位名稱：API 的欄位 → JavaScript 期望的欄位
        trades = trades.map((t, idx) => {
            // 生成正確格式的 ID：pos_{券商}_{標的}_{索引}
            const broker = (t.broker || t.券商 || 'UNKNOWN').toUpperCase();
            const symbol = t.symbol || '-';
            const tradeId = `pos_${broker}_${symbol}_${idx}`;

            return {
                id: tradeId,
                '標的': symbol,
                '數量': parseFloat(t.position) || 0,
                '進場價': parseFloat(t.avgCost) || 0,
                '策略': t.策略 || '',
                '進場原因': t.進場原因 || '',
                '日期': t.時間 || '-',
                '券商': broker,
                ...t  // 保留原始欄位以防萬一
            };
        });

        // 取得所有策略列表
        const allStrategies = await fetch(`${API_BASE_URL}/api/strategies`).then(r => r.json()).then(d => d.data || []).catch(() => []);

        // 更新策略篩選選項
        const filterSelect = document.getElementById('current-trades-strategy-filter');
        if (filterSelect && trades.length > 0) {
            const strategies = [...new Set(trades.map(t => t['策略']).filter(Boolean))];
            strategies.forEach(strategy => {
                if (!filterSelect.querySelector(`option[value="${strategy}"]`)) {
                    const option = document.createElement('option');
                    option.value = strategy;
                    option.textContent = strategy;
                    filterSelect.appendChild(option);
                }
            });

            // 添加篩選事件
            filterSelect.addEventListener('change', () => filterAndDisplayCurrentTrades(trades));
        }

        // 儲存全域供 modal 查詢
        window.allCurrentTrades = trades;

        // 初始顯示
        displayCurrentTrades(trades);

        // 添加搜尋事件
        const searchInput = document.getElementById('current-trades-search');
        if (searchInput) {
            searchInput.addEventListener('input', () => filterAndDisplayCurrentTrades(trades));
        }

        // 儲存策略列表供編輯時使用
        window.allStrategies = allStrategies;

    } catch (err) {
        console.error('加載當前交易失敗:', err);
        container.innerHTML = `<p style="color: #EF4444;">❌ 加載失敗: ${err.message}</p>`;
    }
}

/**
 * 篩選和顯示當前交易
 */
function filterAndDisplayCurrentTrades(allTrades) {
    const searchInput = document.getElementById('current-trades-search');
    const strategyFilter = document.getElementById('current-trades-strategy-filter');

    let filtered = allTrades;

    // 按策略篩選
    if (strategyFilter && strategyFilter.value) {
        filtered = filtered.filter(t => t['策略'] === strategyFilter.value);
    }

    // 按關鍵字搜尋
    if (searchInput && searchInput.value) {
        const keyword = searchInput.value.toLowerCase();
        filtered = filtered.filter(t =>
            (t['標的'] && t['標的'].toLowerCase().includes(keyword)) ||
            (t['策略'] && t['策略'].toLowerCase().includes(keyword))
        );
    }

    displayCurrentTrades(filtered);
}

/**
 * 顯示當前交易列表
 */
function displayCurrentTrades(trades) {
    const container = document.getElementById('current-trades-container');
    if (!container) return;

    if (!trades || trades.length === 0) {
        container.innerHTML = '<p style="padding: 20px; color: #9CA3AF; text-align: center;">暫無進行中的交易</p>';
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';

    trades.forEach((trade, idx) => {
        const symbol = trade['標的'] || '-';
        const strategy = trade['策略'] || '未指定';
        const entryPrice = trade['進場價'] || '-';
        const quantity = trade['數量'] || '-';
        const entryReason = trade['進場原因'] || '(未填寫)';
        const date = trade['日期'] || '-';
        const id = trade['id'] || '';

        const reasonColor = entryReason === '(未填寫)' ? '#EF4444' : '#10B981';

        html += `
            <div class="current-trade-card"
                 style="
                    padding: 14px;
                    border: 2px solid #E5E7EB;
                    border-radius: 8px;
                    background: white;
                    margin-bottom: 4px;
                 ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span style="font-size: 16px; font-weight: 700; color: #1F2937;">${symbol}</span>
                        <span style="margin-left: 8px; font-size: 12px; background: #EDE9FE; color: #5B47D9; padding: 2px 8px; border-radius: 12px;">${strategy}</span>
                    </div>
                    <button onclick="showEditTradeModal('${id}')" style="padding: 4px 12px; font-size: 12px; background: #F3F4F6; border: 1px solid #E5E7EB; border-radius: 4px; cursor: pointer;">✏️ 編輯</button>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; font-size: 13px; color: #6B7280; margin-bottom: 8px;">
                    <div>📅 ${date}</div>
                    <div>💰 進場價: ${entryPrice}</div>
                    <div>📦 數量: ${quantity}</div>
                </div>
                <div style="font-size: 12px; padding: 6px 10px; background: #F9FAFB; border-radius: 4px; border-left: 3px solid ${reasonColor};">
                    <span style="color: #9CA3AF;">進場理由: </span>
                    <span style="color: ${reasonColor};">${entryReason}</span>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// ============================================================================
// Modal 控制函數
// ============================================================================

function closeEditTradeModal() {
    const modal = document.getElementById('edit-trade-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ============================================================================
// Minsky Clock & Economic Cycle Page 加載
// ============================================================================

function loadMinskyClockPage() {
    console.log('Loading Minsky Clock Page');

    // 美林時鐘圖表
    drawMinskyClockChart();

    // 景氣循環追蹤圖表
    drawCycleTrackingChart();

    // 策略績效相關性圖表
    drawStrategyCorrelationChart();
}

function drawMinskyClockChart() {
    const data = [
        {
            x: [0, 0.5, 1, 0.5, 0],
            y: [0, 0.5, 0, 0.5, 0],
            fill: 'toself',
            fillcolor: 'rgba(107, 33, 168, 0.05)',
            line: {color: '#6B21A8', width: 2},
            showlegend: false
        }
    ];

    // 添加四象限標籤和當前位置
    const layout = {
        title: '美林時鐘位置 - 當前階段: 擴張期',
        xaxis: {title: '通膨水平', range: [-0.1, 1.1]},
        yaxis: {title: '經濟增長', range: [-0.1, 1.1]},
        height: 500,
        hovermode: 'closest'
    };

    Plotly.newPlot('minsky-clock-chart', data, layout, {responsive: true});

    // 添加四象限背景和標籤
    const chart = document.getElementById('minsky-clock-chart');
    // 簡化處理 - 實際應該用更複雜的Plotly配置
}

function drawCycleTrackingChart() {
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    const phases = [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 2, 2];
    const phaseNames = ['衰退期', '復甦期', '擴張期', '過熱期'];

    const trace = {
        x: months,
        y: phases,
        mode: 'lines+markers',
        line: {color: '#6B21A8', width: 3},
        marker: {size: 8}
    };

    const layout = {
        title: '景氣循環 12 月追蹤',
        xaxis: {title: '月份'},
        yaxis: {title: '階段', tickvals: [1, 2, 3, 4], ticktext: phaseNames},
        height: 300,
        hovermode: 'x unified'
    };

    Plotly.newPlot('cycle-tracking-chart', [trace], layout, {responsive: true});
}

function drawStrategyCorrelationChart() {
    const strategies = ['強勢股優化', '技術面策略', '總經策略', '季節性策略', '避險策略'];
    const recession = [5, 8, 12, 6, 18];
    const recovery = [15, 12, 10, 14, 8];
    const expansion = [18, 16, 12, 15, 6];
    const overheating = [12, 14, 16, 11, 9];

    const trace1 = {x: strategies, y: recession, name: '衰退期', type: 'bar'};
    const trace2 = {x: strategies, y: recovery, name: '復甦期', type: 'bar'};
    const trace3 = {x: strategies, y: expansion, name: '擴張期', type: 'bar'};
    const trace4 = {x: strategies, y: overheating, name: '過熱期', type: 'bar'};

    const layout = {
        title: '策略績效相關性',
        barmode: 'group',
        xaxis: {title: '策略'},
        yaxis: {title: '相對績效'},
        height: 350
    };

    Plotly.newPlot('strategy-correlation-chart', [trace1, trace2, trace3, trace4], layout, {responsive: true});
}

// ============================================================================
// Community Risk Monitoring Page 加載
// ============================================================================

function loadCommunityRiskPage() {
    console.log('Loading Community Risk Page');

    // 繪製風險趨勢圖
    drawRiskTrendChart();

    // 繪製風險維度分析
    drawRiskDimensionsChart();

    // 填充告警日誌
    populateAlertLog();

    // 填充社群信號表格
    populateTwitterData();
    populateRedditData();
    populateNewsData();
    populateInstitutionData();
}

function drawRiskTrendChart() {
    const dates = Array.from({length: 7}, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - (6 - i));
        return d.toLocaleDateString('zh-TW', {month: '2-digit', day: '2-digit'});
    });

    const riskScores = [35, 38, 32, 28, 35, 30, 28];

    const trace = {
        x: dates,
        y: riskScores,
        mode: 'lines+markers',
        line: {color: '#6B21A8', width: 3},
        fill: 'tozeroy',
        fillcolor: 'rgba(107, 33, 168, 0.1)',
        marker: {size: 8}
    };

    const threshold = {
        type: 'line',
        x0: dates[0],
        y0: 60,
        x1: dates[6],
        y1: 60,
        line: {color: 'red', dash: 'dash'},
    };

    const layout = {
        title: '整體風險評分趨勢',
        xaxis: {title: '日期'},
        yaxis: {title: '風險評分 (0-100)'},
        height: 300,
        hovermode: 'x unified'
    };

    Plotly.newPlot('risk-trend-chart', [trace], layout, {responsive: true});
}

function drawRiskDimensionsChart() {
    const dimensions = ['社群情緒', '交易異常', '機構動向', '新聞事件', '技術面'];
    const scores = [25, 35, 20, 40, 28];
    const colors = scores.map(s => s < 40 ? '#10B981' : s < 60 ? '#F59E0B' : '#EF4444');

    const trace = {
        y: dimensions,
        x: scores,
        orientation: 'h',
        type: 'bar',
        marker: {color: colors}
    };

    const layout = {
        title: '風險維度分析',
        xaxis: {title: '風險指數 (0-100)'},
        height: 300,
        margin: {l: 150}
    };

    Plotly.newPlot('risk-dimensions-chart', [trace], layout, {responsive: true});
}

function populateAlertLog() {
    const alerts = [
        {
            time: '今天 14:32',
            severity: '🟢',
            type: '社群情緒',
            message: 'Tesla 相關推文正面情緒上升 15%，可能推高股價',
            action: '觀察'
        },
        {
            time: '今天 11:15',
            severity: '🟡',
            type: '交易異常',
            message: '美國 10 年期公債成交量異常高，可能預示利率方向改變',
            action: '注意'
        },
        {
            time: '今天 09:45',
            severity: '🟢',
            type: '機構動向',
            message: '高盛減持新興市場持倉 5%，可能影響 EM 資產',
            action: '追蹤'
        }
    ];

    const container = document.getElementById('alert-log');
    let html = '';

    alerts.forEach((alert, index) => {
        const isLastRow = index === alerts.length - 1;
        html += `
            <div style="padding: 15px; border-bottom: ${isLastRow ? 'none' : '1px solid #e5e7eb'}; display: grid; grid-template-columns: 0.8fr 2.5fr 0.7fr; gap: 15px; align-items: start;">
                <div><strong style="font-size: 14px;">${alert.severity}</strong></div>
                <div>
                    <div style="font-weight: 600; font-size: 13px; margin-bottom: 4px;">${alert.type} · <span style="color: #6b7280;">${alert.time}</span></div>
                    <div style="color: #6b7280; font-size: 13px;">${alert.message}</div>
                </div>
                <div style="text-align: right;">
                    <span style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #6b7280;">${alert.action}</span>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function populateTwitterData() {
    const data = [
        {tag: '#Fed', mentions: 1250, positive: 35, trend: '⬇️ 下降'},
        {tag: '#Crypto', mentions: 980, positive: 42, trend: '⬆️ 上升'},
        {tag: '#TechStock', mentions: 1120, positive: 55, trend: '⬆️ 上升'}
    ];

    const tbody = document.getElementById('twitter-table-body');
    tbody.innerHTML = data.map(d => `
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 10px;">${d.tag}</td>
            <td style="padding: 10px; text-align: center;">${d.mentions}</td>
            <td style="padding: 10px; text-align: center;">${d.positive}%</td>
            <td style="padding: 10px; text-align: center;">${d.trend}</td>
        </tr>
    `).join('');
}

function populateRedditData() {
    const data = [
        {name: 'r/investing', discussions: 2400, topic: 'Fed 決議', sentiment: '🟠 謹慎'},
        {name: 'r/stocks', discussions: 2100, topic: 'AI 股票', sentiment: '🟢 樂觀'}
    ];

    const tbody = document.getElementById('reddit-table-body');
    tbody.innerHTML = data.map(d => `
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 10px;">${d.name}</td>
            <td style="padding: 10px; text-align: center;">${d.discussions}</td>
            <td style="padding: 10px; text-align: center;">${d.topic}</td>
            <td style="padding: 10px; text-align: center;">${d.sentiment}</td>
        </tr>
    `).join('');
}

function populateNewsData() {
    const data = [
        {time: '今天 10:30', source: '彭博社', title: 'Fed 官員暗示 2024 年可能降息 3 次', impact: '🔴 高'},
        {time: '今天 08:45', source: '路透社', title: 'S&P 500 創新高，科技股領漲', impact: '🟢 正面'}
    ];

    const tbody = document.getElementById('news-table-body');
    tbody.innerHTML = data.map(d => `
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 10px; white-space: nowrap;">${d.time}</td>
            <td style="padding: 10px; white-space: nowrap;">${d.source}</td>
            <td style="padding: 10px; font-size: 12px;">${d.title}</td>
            <td style="padding: 10px; text-align: center;">${d.impact}</td>
        </tr>
    `).join('');
}

function populateInstitutionData() {
    const data = [
        {name: '高盛', move: '減持新興市場', amount: '$5.2B', impact: '⬇️ EM 資產'},
        {name: '摩根士丹利', move: '增持科技股', amount: '$3.8B', impact: '⬆️ 科技股'}
    ];

    const tbody = document.getElementById('institutions-table-body');
    tbody.innerHTML = data.map(d => `
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 10px;">${d.name}</td>
            <td style="padding: 10px;">${d.move}</td>
            <td style="padding: 10px; text-align: center;">${d.amount}</td>
            <td style="padding: 10px; text-align: center;">${d.impact}</td>
        </tr>
    `).join('');
}

function populateSocialSignals() {
    // Twitter 數據
    const twitterData = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #f3f4f6;">
                <tr>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">標籤</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">提及次數</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">正面比例</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">情緒趨勢</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">#Fed</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">1250</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">35%</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">⬇️ 下降</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">#Crypto</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">980</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">42%</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">⬆️ 上升</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">#TechStock</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">1120</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">55%</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">⬆️ 上升</td></tr>
            </tbody>
        </table>
    `;
    const twitterContainer = document.getElementById('twitter-data');
    if (twitterContainer) twitterContainer.innerHTML = twitterData;

    // Reddit 數據
    const redditData = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #f3f4f6;">
                <tr>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">板塊</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">本週討論數</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">熱門話題</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">情緒</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">r/investing</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">2400</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">Fed 決議</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">🟠 謹慎</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">r/stocks</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">2100</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">AI 股票</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">🟢 樂觀</td></tr>
            </tbody>
        </table>
    `;
    const redditContainer = document.getElementById('reddit-data');
    if (redditContainer) redditContainer.innerHTML = redditData;

    // 新聞數據
    const newsData = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #f3f4f6;">
                <tr>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">時間</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">來源</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">標題</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">今天 10:30</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">彭博社</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">Fed 官員暗示 2024 年可能降息 3 次</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">今天 08:45</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">路透社</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">S&P 500 創新高，科技股領漲</td></tr>
            </tbody>
        </table>
    `;
    const newsContainer = document.getElementById('news-data');
    if (newsContainer) newsContainer.innerHTML = newsData;

    // 機構動向數據
    const institutionData = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #f3f4f6;">
                <tr>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">機構</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">最新動向</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb;">資金規模</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">高盛</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">減持新興市場</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">$5.2B</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">摩根士丹利</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">增持科技股</td><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">$3.8B</td></tr>
            </tbody>
        </table>
    `;
    const institutionContainer = document.getElementById('institutions-data');
    if (institutionContainer) institutionContainer.innerHTML = institutionData;
}

function switchSocialTab(tabName, event) {
    // 隱藏所有 Tab 內容
    document.querySelectorAll('.social-tab-content').forEach(tab => {
        tab.style.display = 'none';
    });

    // 移除所有按鈕的 active 樣式
    document.querySelectorAll('.social-tab-btn').forEach(btn => {
        btn.style.borderBottomColor = 'transparent';
        btn.style.color = 'var(--text-secondary)';
    });

    // 顯示選擇的 Tab
    const tabElement = document.getElementById(tabName + '-tab');
    if (tabElement) {
        tabElement.style.display = 'block';
    }

    // 設置按鈕為 active
    event.target.style.borderBottomColor = 'var(--primary)';
    event.target.style.color = 'var(--primary)';
}

// ============================================================================
// 風控面板頁面加載
// ============================================================================

function loadRiskControlPage() {
    console.log('Loading Risk Control Page');
    populateRiskControlLog();
}

function populateRiskControlLog() {
    const logs = [
        {icon: '⚠️', message: '日損失接近限制 - 當日累計損失 $2,340，已達 47%', time: '今天 14:32'},
        {icon: '⚠️', message: '回撤水位偏高 - 當前回撤 -8.5%，已達 71%', time: '今天 11:15'},
        {icon: '✓', message: '定期風控檢查通過 - 早間 8:30 檢查，所有指標在限內', time: '今天 08:30'}
    ];

    const container = document.getElementById('risk-control-log');
    let html = '';

    logs.forEach((log, index) => {
        const isLastRow = index === logs.length - 1;
        html += `
            <div style="padding: 15px; border-bottom: ${isLastRow ? 'none' : '1px solid #e5e7eb'};">
                <div style="display: flex; gap: 12px;">
                    <div style="font-size: 18px;">${log.icon}</div>
                    <div style="flex: 1;">
                        <div style="font-size: 13px; margin-bottom: 4px;">${log.message}</div>
                        <div style="font-size: 12px; color: #6b7280;">${log.time}</div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ============================================================================
// 資金分配頁面加載
// ============================================================================

function loadAllocationPage() {
    console.log('Loading Allocation Page');
    // 表格數據已在 HTML 中嵌入
}

// ============================================================================
// 績效追蹤頁面加載
// ============================================================================

function loadPerformancePage() {
    console.log('Loading Performance Page');
    // 表格數據已在 HTML 中嵌入
}

console.log('Dashboard.js loaded successfully!');
