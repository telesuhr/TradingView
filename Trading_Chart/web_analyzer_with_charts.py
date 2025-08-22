"""Interactive web-based trading analysis system with visual charts."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import webbrowser
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time
import traceback

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

class TradingAnalysisHandler(BaseHTTPRequestHandler):
    """HTTP request handler with visual charts support."""
    
    def do_GET(self):
        """Handle GET requests with proper error handling."""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/':
                self.serve_main_page()
            elif parsed_path.path == '/api/symbols':
                self.serve_symbols_list()
            elif parsed_path.path == '/api/analyze':
                self.serve_analysis(parsed_path.query)
            elif parsed_path.path == '/api/symbol-info':
                self.serve_symbol_info(parsed_path.query)
            elif parsed_path.path == '/api/chart-data':
                self.serve_chart_data(parsed_path.query)
            else:
                self.send_error(404, "Page not found")
                
        except Exception as e:
            print(f"Error in do_GET: {e}")
            traceback.print_exc()
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        return
    
    def serve_main_page(self):
        """Serve the main web interface with charts."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>LME Trading Analysis System with Charts</title>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@2.0.1/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(90deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .content {
            padding: 30px;
        }
        .form-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #2c3e50;
        }
        select, input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        select:focus, input:focus {
            border-color: #3498db;
            outline: none;
        }
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin: 30px 0;
        }
        button {
            padding: 15px 25px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
        }
        .btn-secondary {
            background: linear-gradient(45deg, #95a5a6, #7f8c8d);
            color: white;
        }
        .btn-success {
            background: linear-gradient(45deg, #27ae60, #229954);
            color: white;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #3498db;
            font-size: 18px;
        }
        .results {
            margin-top: 30px;
            display: none;
        }
        .chart-section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .symbol-info {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            margin: 10px 0;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #f39c12; }
        .strategy-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        .strategy-table th, .strategy-table td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .strategy-table th {
            background: #3498db;
            color: white;
            font-size: 12px;
        }
        .strategy-table tr:hover {
            background: #f5f5f5;
        }
        .section-title {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin: 30px 0 20px 0;
        }
        .error {
            color: red;
            background: #ffe6e6;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 LME Trading Analysis System</h1>
            <p>AI-Powered Multi-Symbol Technical Analysis with Visual Charts</p>
        </div>
        
        <div class="content">
            <div class="form-section">
                <div class="form-group">
                    <label for="symbolSelect">Select Symbol for Analysis:</label>
                    <select id="symbolSelect">
                        <option value="">Loading symbols...</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="periodSelect">Analysis Period:</label>
                    <select id="periodSelect">
                        <option value="180">6 Months</option>
                        <option value="365" selected>1 Year</option>
                        <option value="730">2 Years</option>
                    </select>
                </div>
            </div>
            
            <div class="btn-group">
                <button class="btn-secondary" onclick="getSymbolInfo()">Symbol Info</button>
                <button class="btn-primary" onclick="runBasicAnalysis()">Basic Analysis</button>
                <button class="btn-success" onclick="runDeepAnalysis()">Deep Analysis</button>
            </div>
            
            <div class="loading" id="loading">
                <div>🔄 Analyzing... Please wait...</div>
                <div style="margin-top: 10px; font-size: 14px;" id="loadingMessage">Loading data and generating charts...</div>
            </div>
            
            <div class="results" id="results">
                <div id="resultsContent"></div>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
        let indicatorsChart = null;
        let performanceChart = null;
        
        window.onload = function() {
            loadSymbols();
        };
        
        function loadSymbols() {
            console.log('Loading symbols...');
            fetch('/api/symbols')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    const select = document.getElementById('symbolSelect');
                    select.innerHTML = '<option value="">Select a symbol...</option>';
                    
                    if (data.symbols && data.symbols.length > 0) {
                        data.symbols.forEach(symbol => {
                            const option = document.createElement('option');
                            option.value = symbol.symbol;
                            option.textContent = `${symbol.name} - ${symbol.records} records`;
                            select.appendChild(option);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading symbols:', error);
                    showError(`Failed to load symbols: ${error.message}`);
                });
        }
        
        function getSymbolInfo() {
            const symbol = document.getElementById('symbolSelect').value;
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading('Getting symbol information...');
            
            fetch(`/api/symbol-info?symbol=${encodeURIComponent(symbol)}`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.error) {
                        showError(data.error);
                    } else {
                        showSymbolInfo(data);
                    }
                })
                .catch(error => {
                    hideLoading();
                    showError('Error getting symbol info: ' + error.message);
                });
        }
        
        function runBasicAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading('Running basic analysis and generating charts...');
            
            Promise.all([
                fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`),
                fetch(`/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${period}`)
            ])
            .then(responses => Promise.all(responses.map(r => r.json())))
            .then(([analysisData, chartData]) => {
                hideLoading();
                if (analysisData.error) {
                    showError(analysisData.error);
                } else {
                    showAnalysisResults(analysisData, chartData);
                }
            })
            .catch(error => {
                hideLoading();
                showError('Error running analysis: ' + error.message);
            });
        }
        
        function runDeepAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading('Running deep analysis and generating charts...');
            
            Promise.all([
                fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=deep`),
                fetch(`/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${period}`)
            ])
            .then(responses => Promise.all(responses.map(r => r.json())))
            .then(([analysisData, chartData]) => {
                hideLoading();
                if (analysisData.error) {
                    showError(analysisData.error);
                } else {
                    showAnalysisResults(analysisData, chartData);
                }
            })
            .catch(error => {
                hideLoading();
                showError('Error running deep analysis: ' + error.message);
            });
        }
        
        function showLoading(message = 'Processing...') {
            document.getElementById('loadingMessage').textContent = message;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showSymbolInfo(data) {
            const html = `
                <h3 class="section-title">📊 Symbol Information</h3>
                <div class="symbol-info">
                    <h4>${data.symbol}</h4>
                    <p><strong>Total Records:</strong> ${data.total_records}</p>
                    <p><strong>Date Range:</strong> ${data.date_range}</p>
                    <p><strong>Average Price:</strong> $${data.avg_price}</p>
                    <p><strong>Price Range:</strong> $${data.min_price} - $${data.max_price}</p>
                    <p><strong>Average Volume:</strong> ${data.avg_volume}</p>
                    <p><strong>Data Quality Score:</strong> ${data.quality_score}/100</p>
                </div>
            `;
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
        }
        
        function showAnalysisResults(data, chartData) {
            // Destroy existing charts
            if (priceChart) priceChart.destroy();
            if (indicatorsChart) indicatorsChart.destroy();
            if (performanceChart) performanceChart.destroy();
            
            let html = `<h3 class="section-title">📈 Analysis Results for ${data.symbol}</h3>`;
            
            // Data summary
            html += `
                <div class="symbol-info">
                    <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
                    <p><strong>Data Points:</strong> ${data.data_points} trading days</p>
                </div>
            `;
            
            // Add chart containers
            html += `
                <div class="chart-section">
                    <h4 class="section-title">📊 Price Chart with Technical Indicators</h4>
                    <div class="chart-container">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-grid">
                    <div class="chart-section">
                        <h4>🔍 Technical Indicators</h4>
                        <div class="chart-container">
                            <canvas id="indicatorsChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-section">
                        <h4>📈 Performance Metrics</h4>
                        <div class="chart-container">
                            <canvas id="performanceChart"></canvas>
                        </div>
                    </div>
                </div>
            `;
            
            // Current market metrics
            if (data.current_metrics) {
                html += `
                    <h4 class="section-title">📊 Current Market Status</h4>
                    <div class="analysis-grid">
                        <div class="metric-card">
                            <div class="metric-value ${data.current_metrics.price_change >= 0 ? 'positive' : 'negative'}">
                                $${data.current_metrics.current_price.toFixed(2)}
                            </div>
                            <div>Current Price</div>
                            <div style="font-size: 0.9em; margin-top: 5px;">
                                ${data.current_metrics.price_change >= 0 ? '+' : ''}${data.current_metrics.price_change.toFixed(2)} 
                                (${data.current_metrics.price_change_pct.toFixed(2)}%)
                            </div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value neutral">
                                ${data.current_metrics.volatility.toFixed(2)}%
                            </div>
                            <div>Daily Volatility</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value neutral">
                                ${data.current_metrics.volume.toLocaleString()}
                            </div>
                            <div>Average Volume</div>
                        </div>
                    </div>
                `;
            }
            
            // Trading signals
            if (data.recent_signals && data.recent_signals.length > 0) {
                html += `
                    <h4 class="section-title">🎯 Recent Trading Signals</h4>
                    <table class="strategy-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Price</th>
                                <th>Confidence</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.recent_signals.forEach(signal => {
                    const signalClass = signal.type.includes('BUY') || signal.type.includes('BULLISH') ? 'positive' : 'negative';
                    html += `
                        <tr>
                            <td>${signal.date}</td>
                            <td class="${signalClass}">${signal.type.replace(/_/g, ' ')}</td>
                            <td>$${signal.price.toFixed(2)}</td>
                            <td>${(signal.confidence * 100).toFixed(1)}%</td>
                            <td>${signal.details}</td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table>`;
            }
            
            // Strategy performance (deep analysis)
            if (data.strategy_performance) {
                html += `
                    <h4 class="section-title">📊 Strategy Performance Analysis</h4>
                    <table class="strategy-table">
                        <thead>
                            <tr>
                                <th>Strategy</th>
                                <th>Trades</th>
                                <th>Win Rate</th>
                                <th>Total Return</th>
                                <th>Sharpe Ratio</th>
                                <th>Max Drawdown</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.strategy_performance.forEach(strategy => {
                    html += `
                        <tr>
                            <td>${strategy.name}</td>
                            <td>${strategy.trades}</td>
                            <td>${strategy.win_rate.toFixed(1)}%</td>
                            <td class="${strategy.total_return >= 0 ? 'positive' : 'negative'}">
                                ${strategy.total_return >= 0 ? '+' : ''}${strategy.total_return.toFixed(2)}%
                            </td>
                            <td>${strategy.sharpe_ratio.toFixed(2)}</td>
                            <td class="negative">${strategy.max_drawdown.toFixed(2)}%</td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table>`;
            }
            
            // Recommendations
            if (data.recommendations) {
                html += `
                    <h4 class="section-title">💡 Recommendations</h4>
                    <div class="symbol-info">
                        <ul>
                `;
                
                data.recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                
                html += `</ul></div>`;
            }
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
            
            // Create charts after DOM is updated
            setTimeout(() => {
                createCharts(data, chartData);
            }, 100);
        }
        
        function createCharts(analysisData, chartData) {
            if (!chartData || !chartData.dates) {
                console.log('No chart data available');
                return;
            }
            
            // Price Chart with Moving Averages
            const priceCtx = document.getElementById('priceChart');
            if (priceCtx) {
                priceChart = new Chart(priceCtx, {
                    type: 'line',
                    data: {
                        labels: chartData.dates,
                        datasets: [
                            {
                                label: 'Close Price',
                                data: chartData.close_prices,
                                borderColor: '#3498db',
                                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                                fill: false,
                                tension: 0.1
                            },
                            {
                                label: 'SMA 20',
                                data: chartData.sma20,
                                borderColor: '#e74c3c',
                                backgroundColor: 'transparent',
                                fill: false,
                                borderWidth: 1
                            },
                            {
                                label: 'SMA 50',
                                data: chartData.sma50,
                                borderColor: '#f39c12',
                                backgroundColor: 'transparent',
                                fill: false,
                                borderWidth: 1
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: `${analysisData.symbol} Price Chart`
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    parser: 'YYYY-MM-DD',
                                    tooltipFormat: 'MMM DD, YYYY',
                                    displayFormats: {
                                        day: 'MMM DD',
                                        month: 'MMM YYYY'
                                    }
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Price ($)'
                                }
                            }
                        }
                    }
                });
            }
            
            // Technical Indicators Chart
            const indicatorsCtx = document.getElementById('indicatorsChart');
            if (indicatorsCtx && chartData.rsi) {
                indicatorsChart = new Chart(indicatorsCtx, {
                    type: 'line',
                    data: {
                        labels: chartData.dates,
                        datasets: [
                            {
                                label: 'RSI',
                                data: chartData.rsi,
                                borderColor: '#9b59b6',
                                backgroundColor: 'rgba(155, 89, 182, 0.1)',
                                fill: false,
                                yAxisID: 'y'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'RSI Indicator'
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    parser: 'YYYY-MM-DD'
                                }
                            },
                            y: {
                                min: 0,
                                max: 100,
                                title: {
                                    display: true,
                                    text: 'RSI'
                                }
                            }
                        }
                    }
                });
            }
            
            // Performance Chart (for strategy performance)
            const performanceCtx = document.getElementById('performanceChart');
            if (performanceCtx && analysisData.strategy_performance) {
                const strategies = analysisData.strategy_performance.map(s => s.name);
                const returns = analysisData.strategy_performance.map(s => s.total_return);
                
                performanceChart = new Chart(performanceCtx, {
                    type: 'bar',
                    data: {
                        labels: strategies,
                        datasets: [{
                            label: 'Total Return (%)',
                            data: returns,
                            backgroundColor: returns.map(r => r >= 0 ? 'rgba(39, 174, 96, 0.8)' : 'rgba(231, 76, 60, 0.8)'),
                            borderColor: returns.map(r => r >= 0 ? '#27ae60' : '#e74c3c'),
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Strategy Performance'
                            }
                        },
                        scales: {
                            y: {
                                title: {
                                    display: true,
                                    text: 'Return (%)'
                                }
                            }
                        }
                    }
                });
            }
        }
        
        function showError(message) {
            document.getElementById('resultsContent').innerHTML = `
                <div class="error">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                </div>
            `;
            document.getElementById('results').style.display = 'block';
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_symbols_list(self):
        """Serve available symbols list."""
        try:
            with SQLServerConnector() as conn:
                cursor = conn.connection.cursor()
                cursor.execute("""
                    SELECT 
                        market_name,
                        COUNT(*) as record_count,
                        MIN(Market_Date) as earliest_date,
                        MAX(Market_Date) as latest_date
                    FROM MarketData
                    GROUP BY market_name
                    HAVING COUNT(*) > 100
                    ORDER BY record_count DESC
                """)
                
                symbols = []
                for row in cursor.fetchall():
                    # Create friendly names
                    symbol = row[0]
                    name = symbol
                    
                    if 'LMCADS03' in symbol:
                        name = 'LME Copper'
                    elif 'XAU' in symbol:
                        name = 'Gold'
                    elif 'XAG' in symbol:
                        name = 'Silver'
                    elif 'SPX' in symbol:
                        name = 'S&P 500'
                    elif 'GC1' in symbol:
                        name = 'Gold Futures'
                    elif 'SI1' in symbol:
                        name = 'Silver Futures'
                    elif 'C 1' in symbol:
                        name = 'Corn'
                    elif 'EURUSD' in symbol:
                        name = 'EUR/USD'
                    elif 'GBPUSD' in symbol:
                        name = 'GBP/USD'
                    
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'records': row[1],
                        'date_range': f"{row[2]} to {row[3]}"
                    })
                
                response = {'symbols': symbols}
                
        except Exception as e:
            print(f"Error in serve_symbols_list: {e}")
            traceback.print_exc()
            response = {'error': str(e), 'symbols': []}
        
        self.send_json_response(response)
    
    def serve_symbol_info(self, query_string):
        """Serve detailed symbol information."""
        try:
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            with SQLServerConnector() as conn:
                cursor = conn.connection.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        MIN(Market_Date) as start_date,
                        MAX(Market_Date) as end_date,
                        AVG(Closing_Price) as avg_price,
                        MIN(Closing_Price) as min_price,
                        MAX(Closing_Price) as max_price,
                        AVG(volume) as avg_volume,
                        COUNT(CASE WHEN volume > 0 THEN 1 END) as records_with_volume
                    FROM MarketData
                    WHERE market_name = ?
                """, (symbol,))
                
                row = cursor.fetchone()
                
                if row:
                    quality_score = (row[7] / row[0]) * 100 if row[0] > 0 else 0
                    
                    response = {
                        'symbol': symbol,
                        'total_records': row[0],
                        'date_range': f"{row[1]} to {row[2]}",
                        'avg_price': round(row[3], 2) if row[3] else 0,
                        'min_price': round(row[4], 2) if row[4] else 0,
                        'max_price': round(row[5], 2) if row[5] else 0,
                        'avg_volume': f"{row[6]:,.0f}" if row[6] else "N/A",
                        'quality_score': round(quality_score, 1)
                    }
                else:
                    raise ValueError(f"No data found for symbol {symbol}")
                    
        except Exception as e:
            print(f"Error in serve_symbol_info: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def serve_chart_data(self, query_string):
        """Serve chart data for visualizations."""
        try:
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Load data
            with SQLServerConnector() as conn:
                query = f"""
                    SELECT 
                        Market_Date as [Date],
                        Opening_Price as [Open],
                        Daily_High as [High],
                        Daily_Low as [Low],
                        Closing_Price as [Close],
                        volume as [Volume]
                    FROM MarketData
                    WHERE market_name = '{symbol}'
                        AND Market_Date >= ?
                    ORDER BY Market_Date ASC
                """
                
                start_date = datetime.now() - timedelta(days=period)
                data = pd.read_sql_query(
                    query, 
                    conn.connection,
                    params=[start_date],
                    parse_dates=['Date']
                )
                
                if not data.empty:
                    data.set_index('Date', inplace=True)
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    data.sort_index(inplace=True)
            
            if data.empty:
                raise ValueError(f"No data available for {symbol}")
            
            # Calculate technical indicators for charts
            indicators = TechnicalIndicators()
            sma20 = indicators.sma(data['Close'], 20)
            sma50 = indicators.sma(data['Close'], 50)
            rsi = indicators.rsi(data['Close'])
            
            # Prepare chart data
            chart_data = {
                'dates': [d.strftime('%Y-%m-%d') for d in data.index],
                'close_prices': data['Close'].tolist(),
                'sma20': sma20.tolist(),
                'sma50': sma50.tolist(),
                'rsi': rsi.tolist(),
                'volume': data['Volume'].tolist()
            }
            
            # Clean NaN values for JSON serialization
            for key, values in chart_data.items():
                if key != 'dates':
                    chart_data[key] = [None if pd.isna(v) else float(v) for v in values]
            
        except Exception as e:
            print(f"Error in serve_chart_data: {e}")
            traceback.print_exc()
            chart_data = {'error': str(e)}
        
        self.send_json_response(chart_data)
    
    def serve_analysis(self, query_string):
        """Serve trading analysis results."""
        try:
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            analysis_type = params.get('type', ['basic'])[0]
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Load data
            with SQLServerConnector() as conn:
                query = f"""
                    SELECT 
                        Market_Date as [Date],
                        Opening_Price as [Open],
                        Daily_High as [High],
                        Daily_Low as [Low],
                        Closing_Price as [Close],
                        volume as [Volume]
                    FROM MarketData
                    WHERE market_name = '{symbol}'
                        AND Market_Date >= ?
                    ORDER BY Market_Date ASC
                """
                
                start_date = datetime.now() - timedelta(days=period)
                data = pd.read_sql_query(
                    query, 
                    conn.connection,
                    params=[start_date],
                    parse_dates=['Date']
                )
                
                if not data.empty:
                    data.set_index('Date', inplace=True)
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    data.sort_index(inplace=True)
            
            if data.empty:
                raise ValueError(f"No data available for {symbol} in the specified period")
            
            # Perform analysis
            response = self.analyze_symbol(symbol, data, analysis_type)
            
        except Exception as e:
            print(f"Error in serve_analysis: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def analyze_symbol(self, symbol, data, analysis_type):
        """Perform detailed analysis on the symbol data."""
        response = {
            'symbol': symbol,
            'analysis_period': f"{len(data)} days ({data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')})",
            'data_points': len(data)
        }
        
        # Current market metrics
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
        volatility = data['Close'].pct_change().std() * 100
        avg_volume = data['Volume'].mean()
        
        response['current_metrics'] = {
            'current_price': current_price,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volatility': volatility,
            'volume': avg_volume
        }
        
        # Technical indicators
        indicators = TechnicalIndicators()
        sma20 = indicators.sma(data['Close'], 20).iloc[-1]
        sma50 = indicators.sma(data['Close'], 50).iloc[-1]
        rsi = indicators.rsi(data['Close']).iloc[-1]
        macd_data = indicators.macd(data['Close'])
        macd = macd_data['macd'].iloc[-1]
        
        response['technical_indicators'] = {
            'sma20': sma20,
            'sma50': sma50,
            'rsi': rsi,
            'macd': macd
        }
        
        # Pattern recognition and signals
        recognizer = PatternRecognizer(data)
        signals = recognizer.analyze_all_patterns()
        
        # Recent signals (last 30 days)
        recent_signals = [s for s in signals if s['date'] >= data.index[-min(30, len(data))]]
        recent_signals.sort(key=lambda x: x['date'], reverse=True)
        
        response['recent_signals'] = [{
            'date': signal['date'].strftime('%Y-%m-%d'),
            'type': signal['type'],
            'price': signal['price'],
            'confidence': signal['confidence'],
            'details': signal['details']
        } for signal in recent_signals[:10]]  # Top 10 recent signals
        
        # Deep analysis
        if analysis_type == 'deep':
            response['strategy_performance'] = self.run_strategy_analysis(data)
            response['recommendations'] = self.generate_recommendations(data, signals)
        
        return response
    
    def run_strategy_analysis(self, data):
        """Run comprehensive strategy analysis."""
        strategies = {
            'MA Crossover': {
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
                'position_size': 0.08,
                'confidence': 0.70
            },
            'Candlestick Patterns': {
                'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
                'position_size': 0.10,
                'confidence': 0.75
            },
            'Mixed Strategy': {
                'patterns': ['MA_CROSSOVER_BUY', 'BULLISH_ENGULFING', 'MA_CROSSOVER_SELL', 'BEARISH_ENGULFING'],
                'position_size': 0.08,
                'confidence': 0.65
            }
        }
        
        runner = StrategyRunner(data)
        results = []
        
        for name, config in strategies.items():
            try:
                result = runner.run_pattern_strategy(
                    patterns=config['patterns'],
                    position_size=config['position_size'],
                    confidence_threshold=config['confidence']
                )
                
                metrics = result['metrics']
                
                results.append({
                    'name': name,
                    'trades': metrics['total_trades'],
                    'win_rate': metrics['win_rate'],
                    'total_return': metrics['total_return'],
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'max_drawdown': metrics['max_drawdown']
                })
                
            except Exception:
                # Skip failed strategies
                continue
        
        return results
    
    def generate_recommendations(self, data, signals):
        """Generate trading recommendations based on analysis."""
        recommendations = []
        
        # Technical indicator recommendations
        indicators = TechnicalIndicators()
        current_price = data['Close'].iloc[-1]
        sma20 = indicators.sma(data['Close'], 20).iloc[-1]
        sma50 = indicators.sma(data['Close'], 50).iloc[-1]
        rsi = indicators.rsi(data['Close']).iloc[-1]
        
        if current_price > sma20 > sma50:
            recommendations.append("📈 強気トレンド: 価格が両移動平均線を上回っています")
        elif current_price < sma20 < sma50:
            recommendations.append("📉 弱気トレンド: 価格が両移動平均線を下回っています")
        
        if rsi < 30:
            recommendations.append("🟢 RSIが売られすぎ水準 - 買いチャンスの可能性")
        elif rsi > 70:
            recommendations.append("🔴 RSIが買われすぎ水準 - 利益確定を検討")
        
        # Recent signals recommendation
        recent_signals = [s for s in signals if s['date'] >= data.index[-7]]
        if recent_signals:
            buy_signals = len([s for s in recent_signals if 'BUY' in s['type'] or 'BULLISH' in s['type']])
            sell_signals = len([s for s in recent_signals if 'SELL' in s['type'] or 'BEARISH' in s['type']])
            
            if buy_signals > sell_signals:
                recommendations.append("🎯 最近のパターン分析は強気傾向")
            elif sell_signals > buy_signals:
                recommendations.append("⚠️ 最近のパターン分析は弱気傾向")
        
        # Volatility recommendation
        volatility = data['Close'].pct_change().std() * 100
        if volatility > 3:
            recommendations.append("⚡ 高ボラティリティ検出 - ポジションサイズを小さめに")
        elif volatility < 1:
            recommendations.append("😴 低ボラティリティ - より明確なシグナルを待つ")
        
        if not recommendations:
            recommendations.append("📊 市場は中立的 - より明確なシグナルを待つ")
        
        return recommendations
    
    def send_json_response(self, data):
        """Send JSON response with proper headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            response_json = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            print(f"Error serializing JSON: {e}")
            error_response = json.dumps({'error': f'JSON serialization error: {str(e)}'})
            self.wfile.write(error_response.encode('utf-8'))

def start_server():
    """Start the web server with charts."""
    port = 8082
    server = HTTPServer(('localhost', port), TradingAnalysisHandler)
    
    print(f"=== LME Trading Analysis Web Server with Charts ===")
    print(f"Server starting at http://localhost:{port}")
    print(f"Opening browser...")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\nServer stopped")
        server.shutdown()

if __name__ == "__main__":
    start_server()