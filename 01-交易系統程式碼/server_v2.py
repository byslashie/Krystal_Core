#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple HTTP server for DashboardV2 - no Flask"""

import http.server
import socketserver
import os
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 設定
PORT = 8888
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for DashboardV2"""

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path

        # Parse the URL
        if path == '/v2':
            self.serve_file('templates/dashboardV2.html')
        elif path == '/pages/risk':
            self.serve_file('templates/pages/risk.html')
        elif path == '/pages/performance':
            self.serve_file('templates/pages/performance.html')
        elif path == '/pages/monitoring':
            self.serve_file('templates/pages/monitoring.html')
        elif path == '/pages/trading':
            self.serve_file('templates/pages/trading.html')
        elif path == '/pages/strategies':
            self.serve_file('templates/pages/strategies.html')
        elif path == '/pages/intel':
            self.serve_file('templates/pages/intel.html')
        elif path.startswith('/api/'):
            self.serve_api(path)
        elif path == '/':
            self.serve_file('templates/dashboard.html')
        else:
            self.send_error(404, 'Not Found')

    def serve_file(self, file_path):
        """Serve an HTML file"""
        full_path = BASE_DIR / file_path

        if not full_path.exists():
            self.send_error(404, f'File not found: {file_path}')
            return

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f'Error reading file: {str(e)}')

    def serve_api(self, path):
        """Serve API endpoints"""
        # Parse API path
        if path == '/api/metrics':
            data = {
                'total_value': 871765.89,
                'annual_return': 18.5,
                'sharpe_ratio': 1.45,
                'max_drawdown': -8.2,
                'win_rate': 56.3,
                'daily_change': 2.34,
                'holdings': 12
            }
        elif path == '/api/holdings/by-broker':
            data = {
                'IB': {'balance': 348706.50, 'positions': 2},
                'Yuanta': {'balance': 273983.25, 'positions': 1},
                'Schwab': {'balance': 249076.14, 'positions': 1}
            }
        elif path == '/api/strategies':
            data = [
                {'name': '技術面策略', 'type': '均線交叉', 'return': 18.5, 'status': '運行中'},
                {'name': '強勢股優化', 'type': '動量策略', 'return': 22.3, 'status': '運行中'},
                {'name': '總經策略', 'type': '巨集對沖', 'return': 12.1, 'status': '運行中'}
            ]
        elif path == '/api/status':
            data = {'status': 'ok', 'version': '2.0.0'}
        else:
            self.send_error(404, f'API endpoint not found: {path}')
            return

        # Send JSON response
        response = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        """Custom logging"""
        print(f'[{self.log_date_time_string()}] {format % args}')

def run_server():
    """Start the HTTP server"""
    # Change to working directory
    os.chdir(BASE_DIR)

    print('=' * 70)
    print('🚀 DashboardV2 HTTP Server')
    print('=' * 70)
    print(f'URL:  http://localhost:{PORT}/v2')
    print(f'API:  http://localhost:{PORT}/api/status')
    print(f'\nPress CTRL+C to stop')
    print('=' * 70)
    print()

    # Create server
    handler = DashboardHandler
    with socketserver.TCPServer(('127.0.0.1', PORT), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n\n✓ Server stopped')

if __name__ == '__main__':
    run_server()
