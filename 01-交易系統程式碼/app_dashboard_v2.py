#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simplified Flask App for DashboardV2
Stripped of problematic optional dependencies, focusing on core functionality
"""

from flask import Flask, render_template, jsonify, request
import logging
import os
from datetime import datetime, timedelta
import json

# ============================================================================
# Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.cache = None

# ============================================================================
# Routes - Main Pages
# ============================================================================

@app.route('/')
def index():
    """Main dashboard (V1 for backward compatibility)"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Failed to load main dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/v2')
def dashboard_v2():
    """DashboardV2 - New account-centric design"""
    try:
        logger.info("Rendering dashboardV2.html")
        return render_template('dashboardV2.html')
    except Exception as e:
        logger.error(f"Failed to render dashboardV2.html: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'type': 'TemplateError',
            'file': 'dashboardV2.html'
        }), 500

# ============================================================================
# Routes - Navigation Pages (DashboardV2 sub-pages)
# ============================================================================

@app.route('/pages/risk')
def page_risk():
    """Risk Management Page"""
    try:
        return render_template('pages/risk.html')
    except Exception as e:
        logger.error(f"Failed to render risk.html: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/performance')
def page_performance():
    """Performance Analysis Page"""
    try:
        return render_template('pages/performance.html')
    except Exception as e:
        logger.error(f"Failed to render performance.html: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/monitoring')
def page_monitoring():
    """Monitoring Center Page"""
    try:
        return render_template('pages/monitoring.html')
    except Exception as e:
        logger.error(f"Failed to render monitoring.html: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/trading')
def page_trading():
    """Trading Panel Page"""
    try:
        return render_template('pages/trading.html')
    except Exception as e:
        logger.error(f"Failed to render trading.html: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/strategies')
def page_strategies():
    """Strategy Configuration Page"""
    try:
        return render_template('pages/strategies.html')
    except Exception as e:
        logger.error(f"Failed to render strategies.html: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/pages/intel')
def page_intel():
    """Intelligence Information Page"""
    try:
        return render_template('pages/intel.html')
    except Exception as e:
        logger.error(f"Failed to render intel.html: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API Routes - Mock Data Endpoints
# ============================================================================

@app.route('/api/metrics')
def get_metrics():
    """Get key performance metrics"""
    try:
        metrics = {
            'total_value': 871765.89,
            'annual_return': 18.5,
            'sharpe_ratio': 1.45,
            'max_drawdown': -8.2,
            'win_rate': 56.3,
            'daily_change': 2.34,
            'holdings': 12,
            'data_source': 'demo'
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/holdings/by-broker')
def get_holdings_by_broker():
    """Get holdings grouped by broker"""
    try:
        holdings = {
            'IB': {
                'account': 'IB001',
                'balance': 348706.50,
                'positions': [
                    {'symbol': '2330.TW', 'quantity': 100, 'avg_cost': 585.00, 'current_price': 595.50},
                    {'symbol': '3034.TW', 'quantity': 50, 'avg_cost': 120.00, 'current_price': 125.80}
                ]
            },
            'Yuanta': {
                'account': 'YUANTA001',
                'balance': 273983.25,
                'positions': [
                    {'symbol': 'AAPL.US', 'quantity': 40, 'avg_cost': 180.00, 'current_price': 185.20}
                ]
            },
            'Schwab': {
                'account': 'SCHWAB001',
                'balance': 249076.14,
                'positions': [
                    {'symbol': 'NVDA.US', 'quantity': 25, 'avg_cost': 850.00, 'current_price': 875.50}
                ]
            }
        }
        return jsonify(holdings)
    except Exception as e:
        logger.error(f"Failed to get holdings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-performance')
def get_daily_performance():
    """Get daily P&L data"""
    try:
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        dates.reverse()

        performance = {
            'dates': dates,
            'values': [100000 + i * 500 + (i % 2) * 200 for i in range(30)],
            'daily_pnl': [500 + (i % 2) * 200 for i in range(30)]
        }
        return jsonify(performance)
    except Exception as e:
        logger.error(f"Failed to get daily performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies')
def get_strategies():
    """Get active strategies"""
    try:
        strategies = [
            {
                'name': '技術面策略',
                'type': '均線交叉',
                'return': 18.5,
                'win_rate': 55.2,
                'positions': 8,
                'status': '運行中'
            },
            {
                'name': '強勢股優化',
                'type': '動量策略',
                'return': 22.3,
                'win_rate': 58.1,
                'positions': 5,
                'status': '運行中'
            },
            {
                'name': '總經策略',
                'type': '巨集對沖',
                'return': 12.1,
                'win_rate': 51.8,
                'positions': 3,
                'status': '運行中'
            }
        ]
        return jsonify(strategies)
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """System status"""
    try:
        status = {
            'app_version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'templates_ready': True,
            'api_ready': True,
            'data_connected': True
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# Startup
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 DashboardV2 Flask Server")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL:  http://localhost:8888/v2")
    print(f"API:  http://localhost:8888/api/status")
    print("")
    print("Press CTRL+C to stop")
    print("=" * 70)

    # Verify templates
    templates = [
        'templates/dashboardV2.html',
        'templates/pages/risk.html',
        'templates/pages/performance.html',
        'templates/pages/monitoring.html',
        'templates/pages/trading.html',
        'templates/pages/strategies.html',
        'templates/pages/intel.html'
    ]

    print("\nTemplate Check:")
    for template in templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print(f"  ✓ {template} ({size} bytes)")
        else:
            print(f"  ✗ MISSING: {template}")

    print("\nStarting Flask server...\n")

    try:
        app.run(
            host='127.0.0.1',
            port=8888,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)
