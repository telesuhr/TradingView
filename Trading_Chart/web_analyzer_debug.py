"""Interactive web-based trading analysis system with enhanced debugging."""

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
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

class TradingAnalysisHandler(BaseHTTPRequestHandler):
    """HTTP request handler with enhanced debugging."""
    
    def do_GET(self):
        """Handle GET requests with enhanced error handling."""
        try:
            print(f"[DEBUG] Received request: {self.path}")
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/':
                self.serve_main_page()
            elif parsed_path.path == '/api/symbols':
                print("[DEBUG] Serving symbols list")
                self.serve_symbols_list()
            elif parsed_path.path == '/api/analyze':
                print(f"[DEBUG] Serving analysis with query: {parsed_path.query}")
                self.serve_analysis(parsed_path.query)
            elif parsed_path.path == '/api/symbol-info':
                print(f"[DEBUG] Serving symbol info with query: {parsed_path.query}")
                self.serve_symbol_info(parsed_path.query)
            elif parsed_path.path == '/api/chart-data':
                print(f"[DEBUG] Serving chart data with query: {parsed_path.query}")
                self.serve_chart_data(parsed_path.query)
            else:
                print(f"[DEBUG] Path not found: {parsed_path.path}")
                self.send_error(404, "Page not found")
                
        except Exception as e:
            print(f"[ERROR] Exception in do_GET: {e}")
            traceback.print_exc()
            try:
                self.send_error(500, f"Internal server error: {str(e)}")
            except:
                pass
    
    def log_message(self, format, *args):
        """Override to show request logs."""
        print(f"[REQUEST] {format % args}")
    
    def serve_main_page(self):
        """Serve the main web interface with enhanced debugging."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>LME Trading Analysis System - Debug Version</title>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
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
        .debug-panel {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
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
        .btn-danger {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
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
        .error {
            color: red;
            background: #ffe6e6;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .success {
            color: green;
            background: #e6ffe6;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .chart-section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            margin: 10px;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #f39c12; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 LME Trading Analysis System</h1>
            <p>Debug Version - Enhanced Error Handling</p>
        </div>
        
        <div class="content">
            <div class="debug-panel" id="debugPanel">
                <strong>Debug Log:</strong><br>
                System initialized...<br>
            </div>
            
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
            
            <div class="btn-group">
                <button class="btn-danger" onclick="clearDebugLog()">Clear Debug Log</button>
                <button class="btn-secondary" onclick="testConnection()">Test Connection</button>
                <button class="btn-primary" onclick="debugAnalysis()">Debug Analysis</button>
            </div>
            
            <div class="loading" id="loading">
                <div>🔄 Processing... Please wait...</div>
                <div style="margin-top: 10px; font-size: 14px;" id="loadingMessage">Loading...</div>
            </div>
            
            <div class="results" id="results">
                <div id="resultsContent"></div>
            </div>
        </div>
    </div>

    <script>
        function addDebugLog(message) {
            const debugPanel = document.getElementById('debugPanel');
            const timestamp = new Date().toLocaleTimeString();
            debugPanel.innerHTML += `[${timestamp}] ${message}<br>`;
            debugPanel.scrollTop = debugPanel.scrollHeight;
            console.log(`[DEBUG] ${message}`);
        }
        
        function clearDebugLog() {
            document.getElementById('debugPanel').innerHTML = '<strong>Debug Log:</strong><br>Debug log cleared...<br>';
        }
        
        window.onload = function() {
            addDebugLog('Page loaded, initializing...');
            loadSymbols();
        };
        
        function loadSymbols() {
            addDebugLog('Loading symbols...');
            
            fetch('/api/symbols')
                .then(response => {
                    addDebugLog(`Symbols API response status: ${response.status}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    addDebugLog(`Received ${data.symbols ? data.symbols.length : 0} symbols`);
                    const select = document.getElementById('symbolSelect');
                    select.innerHTML = '<option value="">Select a symbol...</option>';
                    
                    if (data.symbols && data.symbols.length > 0) {
                        data.symbols.forEach(symbol => {
                            const option = document.createElement('option');
                            option.value = symbol.symbol;
                            option.textContent = `${symbol.name} - ${symbol.records} records`;
                            select.appendChild(option);
                        });
                        addDebugLog('Symbols loaded successfully');
                    } else {
                        select.innerHTML = '<option value="">No symbols available</option>';
                        addDebugLog('No symbols received');
                    }
                })
                .catch(error => {
                    addDebugLog(`ERROR loading symbols: ${error.message}`);
                    showError(`Failed to load symbols: ${error.message}`);
                });
        }
        
        function testConnection() {
            addDebugLog('Testing connection to server...');
            showLoading('Testing connection...');
            
            fetch('/api/symbols')
                .then(response => {
                    hideLoading();
                    if (response.ok) {
                        addDebugLog('✓ Connection test successful');
                        showSuccess('Connection test successful!');
                    } else {
                        addDebugLog(`✗ Connection test failed: ${response.status}`);
                        showError(`Connection test failed: ${response.status}`);
                    }
                })
                .catch(error => {
                    hideLoading();
                    addDebugLog(`✗ Connection test failed: ${error.message}`);
                    showError(`Connection test failed: ${error.message}`);
                });
        }
        
        function getSymbolInfo() {
            const symbol = document.getElementById('symbolSelect').value;
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            addDebugLog(`Getting info for symbol: ${symbol}`);
            showLoading('Getting symbol information...');
            
            fetch(`/api/symbol-info?symbol=${encodeURIComponent(symbol)}`)
                .then(response => {
                    addDebugLog(`Symbol info response status: ${response.status}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    hideLoading();
                    addDebugLog('Symbol info received successfully');
                    if (data.error) {
                        showError(data.error);
                    } else {
                        showSymbolInfo(data);
                    }
                })
                .catch(error => {
                    hideLoading();
                    addDebugLog(`ERROR getting symbol info: ${error.message}`);
                    showError('Error getting symbol info: ' + error.message);
                });
        }
        
        function debugAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            addDebugLog(`Starting debug analysis for ${symbol}, period: ${period}`);
            showLoading('Running debug analysis...');
            
            // Test each API endpoint individually
            const urls = [
                `/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`,
                `/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${period}`
            ];
            
            Promise.all(urls.map(url => {
                addDebugLog(`Testing URL: ${url}`);
                return fetch(url)
                    .then(response => {
                        addDebugLog(`${url} - Status: ${response.status}`);
                        if (!response.ok) {
                            throw new Error(`${url} failed with status ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        addDebugLog(`${url} - Data received: ${JSON.stringify(data).substring(0, 100)}...`);
                        return data;
                    })
                    .catch(error => {
                        addDebugLog(`${url} - ERROR: ${error.message}`);
                        throw error;
                    });
            }))
            .then(results => {
                hideLoading();
                addDebugLog('✓ All API endpoints working correctly');
                showSuccess('Debug analysis completed successfully!');
            })
            .catch(error => {
                hideLoading();
                addDebugLog(`✗ Debug analysis failed: ${error.message}`);
                showError('Debug analysis failed: ' + error.message);
            });
        }
        
        function runBasicAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            addDebugLog(`Starting basic analysis for ${symbol}`);
            showLoading('Running basic analysis...');
            
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`)
                .then(response => {
                    addDebugLog(`Basic analysis response status: ${response.status}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    hideLoading();
                    addDebugLog('Basic analysis completed successfully');
                    if (data.error) {
                        showError(data.error);
                    } else {
                        showAnalysisResults(data);
                    }
                })
                .catch(error => {
                    hideLoading();
                    addDebugLog(`ERROR in basic analysis: ${error.message}`);
                    showError('Error running basic analysis: ' + error.message);
                });
        }
        
        function runDeepAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            addDebugLog(`Starting deep analysis for ${symbol}`);
            showLoading('Running deep analysis...');
            
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=deep`)
                .then(response => {
                    addDebugLog(`Deep analysis response status: ${response.status}`);
                    addDebugLog(`Response headers: ${JSON.stringify([...response.headers.entries()])}`);
                    
                    if (!response.ok) {
                        addDebugLog(`Response not OK: ${response.status} ${response.statusText}`);
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    return response.text().then(text => {
                        addDebugLog(`Response text length: ${text.length}`);
                        addDebugLog(`Response text preview: ${text.substring(0, 200)}...`);
                        try {
                            return JSON.parse(text);
                        } catch (e) {
                            addDebugLog(`JSON parse error: ${e.message}`);
                            throw new Error(`Invalid JSON response: ${e.message}`);
                        }
                    });
                })
                .then(data => {
                    hideLoading();
                    addDebugLog('Deep analysis completed successfully');
                    if (data.error) {
                        addDebugLog(`Server returned error: ${data.error}`);
                        showError(data.error);
                    } else {
                        addDebugLog(`Analysis data keys: ${Object.keys(data).join(', ')}`);
                        showAnalysisResults(data);
                    }
                })
                .catch(error => {
                    hideLoading();
                    addDebugLog(`ERROR in deep analysis: ${error.message}`);
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
                <h3>📊 Symbol Information</h3>
                <div class="metric-card">
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
        
        function showAnalysisResults(data) {
            let html = `<h3>📈 Analysis Results for ${data.symbol}</h3>`;
            
            // Data summary
            html += `
                <div class="metric-card">
                    <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
                    <p><strong>Data Points:</strong> ${data.data_points} trading days</p>
                </div>
            `;
            
            // Current market metrics
            if (data.current_metrics) {
                html += `
                    <h4>📊 Current Market Status</h4>
                    <div class="metric-card">
                        <div class="metric-value ${data.current_metrics.price_change >= 0 ? 'positive' : 'negative'}">
                            $${data.current_metrics.current_price.toFixed(2)}
                        </div>
                        <p>Current Price (${data.current_metrics.price_change >= 0 ? '+' : ''}${data.current_metrics.price_change.toFixed(2)})</p>
                        <p>Volatility: ${data.current_metrics.volatility.toFixed(2)}%</p>
                        <p>Volume: ${data.current_metrics.volume.toLocaleString()}</p>
                    </div>
                `;
            }
            
            // Technical indicators
            if (data.technical_indicators) {
                html += `
                    <h4>🔍 Technical Indicators</h4>
                    <div class="metric-card">
                        <p><strong>SMA 20:</strong> $${data.technical_indicators.sma20.toFixed(2)}</p>
                        <p><strong>SMA 50:</strong> $${data.technical_indicators.sma50.toFixed(2)}</p>
                        <p><strong>RSI:</strong> ${data.technical_indicators.rsi.toFixed(1)}</p>
                        <p><strong>MACD:</strong> ${data.technical_indicators.macd.toFixed(2)}</p>
                    </div>
                `;
            }
            
            // Strategy performance (deep analysis)
            if (data.strategy_performance) {
                html += `
                    <h4>📊 Strategy Performance</h4>
                    <div class="metric-card">
                        <table style="width:100%; border-collapse: collapse;">
                            <tr style="background: #f8f9fa;">
                                <th>Strategy</th><th>Trades</th><th>Win Rate</th><th>Return</th>
                            </tr>
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
                        </tr>
                    `;
                });
                
                html += `</table></div>`;
            }
            
            // Recommendations
            if (data.recommendations) {
                html += `
                    <h4>💡 Recommendations</h4>
                    <div class="metric-card">
                        <ul>
                `;
                
                data.recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                
                html += `</ul></div>`;
            }
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
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
        
        function showSuccess(message) {
            document.getElementById('resultsContent').innerHTML = `
                <div class="success">
                    <h3>✅ Success</h3>
                    <p>${message}</p>
                </div>
            `;
            document.getElementById('results').style.display = 'block';
        }
    </script>
</body>
</html>
        """
        
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            print("[DEBUG] Main page served successfully")
        except Exception as e:
            print(f"[ERROR] Failed to serve main page: {e}")
    
    def serve_symbols_list(self):
        """Serve available symbols list."""
        try:
            print("[DEBUG] Starting serve_symbols_list")
            
            with SQLServerConnector() as conn:
                print("[DEBUG] Database connection established")
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
                rows = cursor.fetchall()
                print(f"[DEBUG] Found {len(rows)} symbols in database")
                
                for row in rows:
                    symbol = row[0]
                    name = symbol
                    
                    # Create friendly names
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
                    
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'records': row[1],
                        'date_range': f"{row[2]} to {row[3]}"
                    })
                
                response = {'symbols': symbols}
                print(f"[DEBUG] Prepared response with {len(symbols)} symbols")
                
        except Exception as e:
            print(f"[ERROR] Exception in serve_symbols_list: {e}")
            traceback.print_exc()
            response = {'error': str(e), 'symbols': []}
        
        self.send_json_response(response)
    
    def serve_symbol_info(self, query_string):
        """Serve detailed symbol information."""
        try:
            print(f"[DEBUG] serve_symbol_info called with query: {query_string}")
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            print(f"[DEBUG] Extracted symbol: {symbol}")
            
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
                print(f"[DEBUG] Query returned row: {row}")
                
                if row and row[0] > 0:
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
                    print(f"[DEBUG] Prepared successful response")
                else:
                    raise ValueError(f"No data found for symbol {symbol}")
                    
        except Exception as e:
            print(f"[ERROR] Exception in serve_symbol_info: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def serve_analysis(self, query_string):
        """Serve trading analysis results with enhanced debugging."""
        try:
            print(f"[DEBUG] serve_analysis called with query: {query_string}")
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            analysis_type = params.get('type', ['basic'])[0]
            
            print(f"[DEBUG] Parameters - Symbol: {symbol}, Period: {period}, Type: {analysis_type}")
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Load data
            print("[DEBUG] Loading data from database...")
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
                print(f"[DEBUG] Start date: {start_date}")
                
                data = pd.read_sql_query(
                    query, 
                    conn.connection,
                    params=[start_date],
                    parse_dates=['Date']
                )
                
                print(f"[DEBUG] Loaded {len(data)} rows from database")
                
                if not data.empty:
                    data.set_index('Date', inplace=True)
                    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')
                    data.sort_index(inplace=True)
                    print(f"[DEBUG] Data processed, final shape: {data.shape}")
            
            if data.empty:
                raise ValueError(f"No data available for {symbol} in the specified period")
            
            # Perform analysis
            print(f"[DEBUG] Starting analysis...")
            response = self.analyze_symbol(symbol, data, analysis_type)
            print(f"[DEBUG] Analysis completed successfully")
            
        except Exception as e:
            print(f"[ERROR] Exception in serve_analysis: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def serve_chart_data(self, query_string):
        """Serve chart data for visualizations."""
        try:
            print(f"[DEBUG] serve_chart_data called with query: {query_string}")
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Simplified chart data response
            chart_data = {
                'dates': [],
                'close_prices': [],
                'message': 'Chart data temporarily simplified for debugging'
            }
            
        except Exception as e:
            print(f"[ERROR] Exception in serve_chart_data: {e}")
            traceback.print_exc()
            chart_data = {'error': str(e)}
        
        self.send_json_response(chart_data)
    
    def analyze_symbol(self, symbol, data, analysis_type):
        """Perform analysis with enhanced debugging."""
        print(f"[DEBUG] analyze_symbol called for {symbol}, type: {analysis_type}")
        
        response = {
            'symbol': symbol,
            'analysis_period': f"{len(data)} days ({data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')})",
            'data_points': len(data)
        }
        
        try:
            # Current market metrics
            print("[DEBUG] Calculating current metrics...")
            current_price = float(data['Close'].iloc[-1])
            prev_price = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            volatility = float(data['Close'].pct_change().std() * 100)
            avg_volume = float(data['Volume'].mean())
            
            response['current_metrics'] = {
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'volatility': volatility,
                'volume': avg_volume
            }
            print("[DEBUG] Current metrics calculated")
            
            # Technical indicators
            print("[DEBUG] Calculating technical indicators...")
            indicators = TechnicalIndicators()
            sma20 = float(indicators.sma(data['Close'], 20).iloc[-1])
            sma50 = float(indicators.sma(data['Close'], 50).iloc[-1])
            rsi = float(indicators.rsi(data['Close']).iloc[-1])
            macd_data = indicators.macd(data['Close'])
            macd = float(macd_data['macd'].iloc[-1])
            
            response['technical_indicators'] = {
                'sma20': sma20,
                'sma50': sma50,
                'rsi': rsi,
                'macd': macd
            }
            print("[DEBUG] Technical indicators calculated")
            
            # Pattern recognition
            print("[DEBUG] Starting pattern recognition...")
            recognizer = PatternRecognizer(data)
            signals = recognizer.analyze_all_patterns()
            print(f"[DEBUG] Found {len(signals)} signals")
            
            # Recent signals (last 30 days)
            recent_signals = [s for s in signals if s['date'] >= data.index[-min(30, len(data))]]
            recent_signals.sort(key=lambda x: x['date'], reverse=True)
            
            response['recent_signals'] = [{
                'date': signal['date'].strftime('%Y-%m-%d'),
                'type': signal['type'],
                'price': float(signal['price']),
                'confidence': float(signal['confidence']),
                'details': str(signal['details'])
            } for signal in recent_signals[:10]]
            
            # Deep analysis
            if analysis_type == 'deep':
                print("[DEBUG] Running deep analysis...")
                try:
                    response['strategy_performance'] = self.run_strategy_analysis(data)
                    response['recommendations'] = self.generate_recommendations(data, signals)
                    print("[DEBUG] Deep analysis completed")
                except Exception as e:
                    print(f"[ERROR] Deep analysis failed: {e}")
                    response['strategy_performance'] = []
                    response['recommendations'] = [f"深層分析でエラーが発生しました: {str(e)}"]
            
        except Exception as e:
            print(f"[ERROR] Exception in analyze_symbol: {e}")
            traceback.print_exc()
            response['error'] = str(e)
        
        return response
    
    def run_strategy_analysis(self, data):
        """Run comprehensive strategy analysis with error handling."""
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
            }
        }
        
        results = []
        runner = StrategyRunner(data)
        
        for name, config in strategies.items():
            try:
                print(f"[DEBUG] Testing strategy: {name}")
                result = runner.run_pattern_strategy(
                    patterns=config['patterns'],
                    position_size=config['position_size'],
                    confidence_threshold=config['confidence']
                )
                
                metrics = result['metrics']
                
                results.append({
                    'name': name,
                    'trades': int(metrics['total_trades']),
                    'win_rate': float(metrics['win_rate']),
                    'total_return': float(metrics['total_return']),
                    'sharpe_ratio': float(metrics['sharpe_ratio']),
                    'max_drawdown': float(metrics['max_drawdown'])
                })
                print(f"[DEBUG] Strategy {name} completed: {metrics['total_trades']} trades")
                
            except Exception as e:
                print(f"[ERROR] Strategy {name} failed: {e}")
                results.append({
                    'name': f"{name} (Failed)",
                    'trades': 0,
                    'win_rate': 0.0,
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                })
        
        return results
    
    def generate_recommendations(self, data, signals):
        """Generate trading recommendations."""
        recommendations = []
        
        try:
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
            else:
                recommendations.append("📊 RSIは中立的な水準です")
            
            if not recommendations:
                recommendations.append("📊 市場は中立的 - より明確なシグナルを待つ")
                
        except Exception as e:
            print(f"[ERROR] Failed to generate recommendations: {e}")
            recommendations.append(f"推奨事項の生成でエラーが発生しました: {str(e)}")
        
        return recommendations
    
    def send_json_response(self, data):
        """Send JSON response with proper headers and error handling."""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            # Convert numpy types to Python types for JSON serialization
            def convert_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif pd.isna(obj):
                    return None
                return obj
            
            # Clean the data recursively
            def clean_data(data):
                if isinstance(data, dict):
                    return {k: clean_data(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [clean_data(v) for v in data]
                else:
                    return convert_types(data)
            
            cleaned_data = clean_data(data)
            response_json = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            print(f"[DEBUG] JSON response sent successfully (length: {len(response_json)})")
            
        except Exception as e:
            print(f"[ERROR] Failed to send JSON response: {e}")
            traceback.print_exc()
            try:
                error_response = json.dumps({'error': f'Response serialization error: {str(e)}'})
                self.wfile.write(error_response.encode('utf-8'))
            except:
                pass

def start_debug_server():
    """Start the debug web server."""
    port = 8083
    server = HTTPServer(('localhost', port), TradingAnalysisHandler)
    
    print(f"=== LME Trading Analysis Debug Server ===")
    print(f"Server starting at http://localhost:{port}")
    print(f"Enhanced debugging and error handling enabled")
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
    start_debug_server()