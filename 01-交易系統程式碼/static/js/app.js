// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL = '';  // Use relative paths for Flask app

// ============================================================================
// Data Fetching Functions
// ============================================================================

async function fetchMetrics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/metrics`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const result = await response.json();
        return result.data || result;  // 處理兩種格式
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return null;
    }
}

async function fetchChartData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chart-data`);
        if (!response.ok) throw new Error('Failed to fetch chart data');
        const result = await response.json();
        return result.data || result;  // 處理兩種格式
    } catch (error) {
        console.error('Error fetching chart data:', error);
        return null;
    }
}

async function fetchHoldings() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/holdings`);
        if (!response.ok) throw new Error('Failed to fetch holdings');
        const result = await response.json();
        return result.data || result;  // 處理兩種格式
    } catch (error) {
        console.error('Error fetching holdings:', error);
        return null;
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatNumber(num, decimals = 2) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatCurrency(num) {
    return `$${formatNumber(num, 2)}`;
}

function formatPercent(num) {
    return `${formatNumber(num, 2)}%`;
}

// ============================================================================
// Chart Rendering Functions
// ============================================================================

async function renderPriceChart() {
    const data = await fetchChartData();
    if (!data) {
        console.error('No chart data available');
        return;
    }

    const trace = {
        x: data.dates,
        y: data.prices,
        type: 'scatter',
        mode: 'lines',
        name: 'Price',
        line: {
            color: '#6B21A8',
            width: 3
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(107, 33, 168, 0.1)',
        hovertemplate: '<b>%{x|%b %d}</b><br>$%{y:,.2f}<extra></extra>'
    };

    const layout = {
        title: '',
        xaxis: {
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false
        },
        yaxis: {
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { l: 50, r: 50, t: 30, b: 50 },
        hovermode: 'x unified',
        font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
            size: 12,
            color: '#1A1A2E'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('price-chart', [trace], layout, config);
}

async function renderCumulativeChart() {
    const data = await fetchChartData();
    if (!data) {
        console.error('No chart data available');
        return;
    }

    const trace = {
        x: data.dates,
        y: data.cumulative_returns,
        type: 'scatter',
        mode: 'lines',
        name: 'Cumulative Return',
        line: {
            color: '#10B981',
            width: 2
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(16, 185, 129, 0.1)',
        hovertemplate: '<b>%{x|%b %d}</b><br>%{y:.2f}%<extra></extra>'
    };

    const layout = {
        title: 'Cumulative Returns',
        xaxis: {
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false
        },
        yaxis: {
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false,
            title: 'Return (%)'
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { l: 50, r: 50, t: 40, b: 50 },
        hovermode: 'x unified',
        font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
            size: 12,
            color: '#1A1A2E'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('cumulative-chart', [trace], layout, config);
}

async function renderDistributionChart() {
    const data = await fetchChartData();
    if (!data) {
        console.error('No chart data available');
        return;
    }

    const trace = {
        x: data.daily_returns,
        type: 'histogram',
        nbinsx: 40,
        name: 'Distribution',
        marker: {
            color: 'rgba(16, 185, 129, 0.6)',
            line: {
                color: '#10B981',
                width: 1
            }
        },
        hovertemplate: 'Return Rate: %{x:.2f}%<br>Frequency: %{y}<extra></extra>'
    };

    const layout = {
        title: 'Daily Returns Distribution',
        xaxis: {
            title: 'Daily Return (%)',
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false
        },
        yaxis: {
            title: 'Frequency',
            showgrid: true,
            gridwidth: 1,
            gridcolor: '#F0E8FF',
            showline: true,
            linewidth: 1,
            linecolor: '#E8E0FF',
            zeroline: false
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { l: 50, r: 50, t: 40, b: 50 },
        hovermode: 'closest',
        font: {
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
            size: 12,
            color: '#1A1A2E'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('distribution-chart', [trace], layout, config);
}

// ============================================================================
// DOM Updating Functions
// ============================================================================

async function updateMetrics() {
    const metrics = await fetchMetrics();
    if (!metrics) {
        console.warn('無法更新指標，使用默認值');
        return;
    }

    // Update metric cards
    const totalValue = document.getElementById('total-value');
    const annualReturn = document.getElementById('annual-return');
    const holdingsCount = document.getElementById('holdings-count');
    const riskScore = document.getElementById('risk-score');

    if (totalValue) totalValue.textContent = formatCurrency(metrics.total_value);
    if (annualReturn) annualReturn.textContent = formatPercent(metrics.annual_return);
    if (holdingsCount) holdingsCount.textContent = metrics.holdings;
    if (riskScore) {
        const maxDrawdown = Math.abs(metrics.max_drawdown);
        riskScore.textContent = maxDrawdown > 15 ? '高' : maxDrawdown > 8 ? '中' : '低';
    }
}

async function updateHoldings() {
    const holdings = await fetchHoldings();
    if (!holdings) {
        console.warn('無法更新持倉');
        return;
    }

    const tbody = document.getElementById('holdings-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    // 確保 holdings 是數組
    const holdingsArray = Array.isArray(holdings) ? holdings : [];

    holdingsArray.forEach(holding => {
        const row = document.createElement('tr');
        const changeStr = holding.change || '0%';
        const changeClass = changeStr.startsWith('+') ? 'positive' : 'negative';

        row.innerHTML = `
            <td>${holding.symbol || '-'}</td>
            <td>${holding.price || '-'}</td>
            <td>${holding.quantity || '-'}</td>
            <td>${holding.value || '-'}</td>
            <td><span class="metric-change ${changeClass}">${changeStr}</span></td>
        `;

        tbody.appendChild(row);
    });
}

// ============================================================================
// Event Listeners
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    const periodSelect = document.getElementById('period-select');
    if (periodSelect) {
        periodSelect.addEventListener('change', (e) => {
            console.log('Period changed to:', e.target.value);
            // 重新加載數據
            renderPriceChart();
            renderCumulativeChart();
            renderDistributionChart();
        });
    }

    const riskRadios = document.querySelectorAll('input[name="risk"]');
    riskRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            console.log('Risk level changed to:', e.target.value);
        });
    });
});

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Dashboard initializing...');

    // Load all data
    try {
        await Promise.all([
            updateMetrics(),
            updateHoldings(),
            renderPriceChart(),
            renderCumulativeChart(),
            renderDistributionChart()
        ]);

        console.log('Dashboard loaded successfully!');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }

    // Optional: Set up auto-refresh every 30 seconds
    setInterval(() => {
        updateMetrics();
        updateHoldings();
    }, 30000);
});

// ============================================================================
// Window Resize Handler (for chart responsiveness)
// ============================================================================

window.addEventListener('resize', () => {
    const charts = ['price-chart', 'cumulative-chart', 'distribution-chart'];
    charts.forEach(chartId => {
        const element = document.getElementById(chartId);
        if (element) {
            Plotly.Plots.resize(chartId);
        }
    });
});
