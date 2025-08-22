"""Fixed interactive web-based trading analysis system."""

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
    """Fixed HTTP request handler for trading analysis."""
    
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
        """Serve the main web interface."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>LME Trading Analysis System</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
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
        .form-group {
            margin-bottom: 20px;
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
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .symbol-info {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
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
        }
        .strategy-table th, .strategy-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .strategy-table th {
            background: #3498db;
            color: white;
        }
        .strategy-table tr:hover {
            background: #f5f5f5;
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
            <h1>🚀 LME Trading Analysis System</h1>
            <p>AI-Powered Multi-Symbol Technical Analysis</p>
        </div>
        
        <div class="content">
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
            
            <div class="btn-group">
                <button class="btn-secondary" onclick="getSymbolInfo()">Symbol Info</button>
                <button class="btn-primary" onclick="runBasicAnalysis()">Basic Analysis</button>
                <button class="btn-success" onclick="runDeepAnalysis()">Deep Analysis</button>
            </div>
            
            <div class="loading" id="loading">
                <div>🔄 Analyzing... Please wait...</div>
                <div style="margin-top: 10px; font-size: 14px;" id="loadingMessage">This may take 30-60 seconds</div>
            </div>
            
            <div class="results" id="results">
                <div id="resultsContent"></div>
            </div>
        </div>
    </div>

    <script>
        window.onload = function() {
            loadSymbols();
        };
        
        function loadSymbols() {
            console.log('Loading symbols...');
            fetch('/api/symbols')
                .then(response => {
                    console.log('Symbols response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Symbols data:', data);
                    const select = document.getElementById('symbolSelect');
                    select.innerHTML = '<option value="">Select a symbol...</option>';
                    
                    if (data.symbols && data.symbols.length > 0) {
                        data.symbols.forEach(symbol => {
                            const option = document.createElement('option');
                            option.value = symbol.symbol;
                            option.textContent = `${symbol.name} - ${symbol.records} records`;
                            select.appendChild(option);
                        });
                    } else {
                        select.innerHTML = '<option value="">No symbols available</option>';
                    }
                })
                .catch(error => {
                    console.error('Error loading symbols:', error);
                    document.getElementById('symbolSelect').innerHTML = '<option value="">Error loading symbols</option>';
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
                .then(response => {
                    console.log('Symbol info response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Symbol info data:', data);
                    hideLoading();
                    if (data.error) {
                        showError(`Symbol info error: ${data.error}`);
                    } else {
                        showSymbolInfo(data);
                    }
                })
                .catch(error => {
                    console.error('Symbol info error:', error);
                    hideLoading();
                    showError(`Error getting symbol info: ${error.message}`);
                });
        }
        
        function runBasicAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading('Running basic analysis...');
            
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`)
                .then(response => {
                    console.log('Basic analysis response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Basic analysis data:', data);
                    hideLoading();
                    if (data.error) {
                        showError(`Analysis error: ${data.error}`);
                    } else {
                        showAnalysisResults(data);
                    }
                })
                .catch(error => {
                    console.error('Basic analysis error:', error);
                    hideLoading();
                    showError(`Error running basic analysis: ${error.message}`);
                });
        }
        
        function runDeepAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading('Running deep analysis... This may take up to 60 seconds.');
            
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=deep`)
                .then(response => {
                    console.log('Deep analysis response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Deep analysis data:', data);
                    hideLoading();
                    if (data.error) {
                        showError(`Analysis error: ${data.error}`);
                    } else {
                        showAnalysisResults(data);
                    }
                })
                .catch(error => {
                    console.error('Deep analysis error:', error);
                    hideLoading();
                    showError(`Error running deep analysis: ${error.message}`);
                });
        }
        
        function showLoading(message) {
            document.getElementById('loadingMessage').textContent = message || 'Processing...';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showSymbolInfo(data) {
            const html = `
                <h3>📊 Symbol Information</h3>
                <div class="symbol-info">
                    <h4>${data.symbol}</h4>
                    <p><strong>Total Records:</strong> ${data.total_records.toLocaleString()}</p>
                    <p><strong>Date Range:</strong> ${data.date_range}</p>
                    <p><strong>Average Price:</strong> $${data.avg_price.toLocaleString()}</p>
                    <p><strong>Price Range:</strong> $${data.min_price.toLocaleString()} - $${data.max_price.toLocaleString()}</p>
                    <p><strong>Average Volume:</strong> ${data.avg_volume}</p>
                    <p><strong>Data Quality Score:</strong> ${data.quality_score}/100</p>
                </div>
            `;
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
        }
        
        function showAnalysisResults(data) {
            let html = `<h3>📈 Analysis Results for ${data.symbol}</h3>`;
            
            html += `
                <div class="symbol-info">
                    <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
                    <p><strong>Data Points:</strong> ${data.data_points} trading days</p>
                </div>
            `;
            
            if (data.current_metrics) {
                html += `
                    <h4>📊 Current Market Status</h4>
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
            
            if (data.technical_indicators) {
                html += `
                    <h4>🔍 Technical Indicators</h4>
                    <div class="analysis-grid">
                        <div class="metric-card">
                            <div class="metric-value neutral">$${data.technical_indicators.sma20.toFixed(2)}</div>
                            <div>SMA 20</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value neutral">$${data.technical_indicators.sma50.toFixed(2)}</div>
                            <div>SMA 50</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value ${data.technical_indicators.rsi < 30 ? 'positive' : data.technical_indicators.rsi > 70 ? 'negative' : 'neutral'}">
                                ${data.technical_indicators.rsi.toFixed(1)}
                            </div>
                            <div>RSI</div>
                            <div style="font-size: 0.8em;">
                                ${data.technical_indicators.rsi < 30 ? 'Oversold' : data.technical_indicators.rsi > 70 ? 'Overbought' : 'Neutral'}
                            </div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value ${data.technical_indicators.macd >= 0 ? 'positive' : 'negative'}">
                                ${data.technical_indicators.macd.toFixed(2)}
                            </div>
                            <div>MACD</div>
                        </div>
                    </div>
                `;
            }
            
            if (data.recent_signals && data.recent_signals.length > 0) {
                html += `
                    <h4>🎯 Recent Trading Signals</h4>
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
            } else {
                html += `
                    <h4>🎯 Recent Trading Signals</h4>
                    <div class="symbol-info">
                        <p>No recent trading signals found for this period.</p>
                    </div>
                `;
            }
            
            if (data.strategy_performance && data.strategy_performance.length > 0) {
                html += `
                    <h4>📊 Strategy Performance Analysis</h4>
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
            
            if (data.recommendations && data.recommendations.length > 0) {
                html += `
                    <h4>💡 AI Recommendations</h4>
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
        }
        
        function showError(message) {
            document.getElementById('resultsContent').innerHTML = `
                <div class="error">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                    <p><small>Check the browser console (F12) for more details.</small></p>
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
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_symbols_list(self):
        """Serve available symbols list."""
        try:
            print("Loading symbols from database...")
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
                    OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY
                """)
                
                symbols = []
                for row in cursor.fetchall():
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
                    elif 'EURUSD' in symbol:
                        name = 'EUR/USD'
                    elif 'GBPUSD' in symbol:
                        name = 'GBP/USD'
                    elif 'DJI' in symbol:
                        name = 'Dow Jones'
                    else:
                        # Generic cleanup
                        name = symbol.replace('Comdty', '').replace('Curncy', '').replace('Index', '').strip()
                    
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'records': row[1],
                        'date_range': f"{row[2]} to {row[3]}"
                    })
                
                print(f"Found {len(symbols)} symbols")
                response = {'symbols': symbols}
                
        except Exception as e:
            print(f"Error loading symbols: {e}")
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
            
            print(f"Getting symbol info for: {symbol}")
            
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
                else:
                    raise ValueError(f"No data found for symbol {symbol}")
                    
        except Exception as e:
            print(f"Error getting symbol info: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def serve_analysis(self, query_string):
        """Serve trading analysis results."""
        try:
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            analysis_type = params.get('type', ['basic'])[0]
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            print(f"Running {analysis_type} analysis for {symbol} over {period} days...")
            
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
                        AND Closing_Price > 0
                        AND Opening_Price > 0
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
                    
                    # Remove rows with NaN values
                    data = data.dropna()
                    data.sort_index(inplace=True)
            
            if data.empty or len(data) < 50:
                raise ValueError(f"Insufficient data for {symbol}: only {len(data)} valid records found")
            
            print(f"Loaded {len(data)} days of valid data")
            
            # Perform analysis
            response = self.analyze_symbol(symbol, data, analysis_type)
            
        except Exception as e:
            print(f"Error in analysis: {e}")
            traceback.print_exc()
            response = {'error': str(e)}
        
        self.send_json_response(response)
    
    def analyze_symbol(self, symbol, data, analysis_type):
        """Perform detailed analysis on the symbol data."""
        try:
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
            volatility = data['Close'].pct_change().std() * 100 * np.sqrt(252)  # Annualized
            avg_volume = data['Volume'].mean()
            
            response['current_metrics'] = {
                'current_price': float(current_price),
                'price_change': float(price_change),
                'price_change_pct': float(price_change_pct),
                'volatility': float(volatility),
                'volume': float(avg_volume) if not np.isnan(avg_volume) else 0
            }
            
            # Technical indicators
            indicators = TechnicalIndicators()
            sma20 = indicators.sma(data['Close'], 20)
            sma50 = indicators.sma(data['Close'], 50)
            rsi = indicators.rsi(data['Close'])
            macd_data = indicators.macd(data['Close'])
            
            response['technical_indicators'] = {
                'sma20': float(sma20.iloc[-1]) if not sma20.empty and not np.isnan(sma20.iloc[-1]) else float(current_price),
                'sma50': float(sma50.iloc[-1]) if not sma50.empty and not np.isnan(sma50.iloc[-1]) else float(current_price),
                'rsi': float(rsi.iloc[-1]) if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0,
                'macd': float(macd_data['macd'].iloc[-1]) if not macd_data['macd'].empty and not np.isnan(macd_data['macd'].iloc[-1]) else 0.0
            }
            
            # Pattern recognition and signals
            try:
                recognizer = PatternRecognizer(data)
                signals = recognizer.analyze_all_patterns()
                
                # Recent signals (last 30 days)
                recent_signals = [s for s in signals if s['date'] >= data.index[-min(30, len(data))]]
                recent_signals.sort(key=lambda x: x['date'], reverse=True)
                
                response['recent_signals'] = [{
                    'date': signal['date'].strftime('%Y-%m-%d'),
                    'type': signal['type'],
                    'price': float(signal['price']),
                    'confidence': float(signal['confidence']),
                    'details': signal['details']
                } for signal in recent_signals[:10]]  # Top 10 recent signals
                
            except Exception as e:
                print(f"Error in pattern recognition: {e}")
                response['recent_signals'] = []
            
            # Deep analysis
            if analysis_type == 'deep':
                try:
                    response['strategy_performance'] = self.run_strategy_analysis(data)
                    response['recommendations'] = self.generate_recommendations(data, response['technical_indicators'], volatility)
                except Exception as e:
                    print(f"Error in deep analysis: {e}")
                    response['strategy_performance'] = []
                    response['recommendations'] = [f"Deep analysis error: {str(e)}"]
            
            return response
            
        except Exception as e:
            print(f"Error in analyze_symbol: {e}")
            traceback.print_exc()
            return {'error': str(e)}
    
    def run_strategy_analysis(self, data):
        """Run comprehensive strategy analysis."""
        strategies = {
            'MA Crossover': {
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
                'position_size': 0.08,
                'confidence': 0.60
            },
            'Candlestick Patterns': {
                'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
                'position_size': 0.10,
                'confidence': 0.65
            },
            'Mixed Strategy': {
                'patterns': ['MA_CROSSOVER_BUY', 'BULLISH_ENGULFING'],
                'position_size': 0.08,
                'confidence': 0.60
            }
        }
        
        runner = StrategyRunner(data)
        results = []
        
        for name, config in strategies.items():
            try:
                print(f"  Testing {name}...")
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
                    'sharpe_ratio': float(metrics['sharpe_ratio']) if not np.isnan(metrics['sharpe_ratio']) else 0.0,
                    'max_drawdown': float(metrics['max_drawdown'])
                })
                
            except Exception as e:
                print(f"  Error in strategy {name}: {e}")
                # Add empty result to show the strategy was attempted
                results.append({
                    'name': name,
                    'trades': 0,
                    'win_rate': 0.0,
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                })
        
        return results
    
    def generate_recommendations(self, data, tech_indicators, volatility):
        """Generate trading recommendations based on analysis."""
        recommendations = []
        
        try:
            current_price = data['Close'].iloc[-1]
            sma20 = tech_indicators['sma20']
            sma50 = tech_indicators['sma50']
            rsi = tech_indicators['rsi']
            
            # Trend analysis
            if current_price > sma20 > sma50:
                recommendations.append("📈 Bullish trend: Price trading above both moving averages")
            elif current_price < sma20 < sma50:
                recommendations.append("📉 Bearish trend: Price trading below both moving averages")
            else:
                recommendations.append("🔄 Mixed signals: Price between moving averages")
            
            # RSI analysis
            if rsi < 30:
                recommendations.append("🟢 RSI oversold ({}): Potential buying opportunity".format(round(rsi, 1)))
            elif rsi > 70:
                recommendations.append("🔴 RSI overbought ({}): Consider profit-taking".format(round(rsi, 1)))
            else:
                recommendations.append("🟡 RSI neutral ({}): Wait for clearer signals".format(round(rsi, 1)))
            
            # Volatility analysis
            if volatility > 30:
                recommendations.append("⚡ High volatility ({:.1f}%): Use smaller position sizes".format(volatility))
            elif volatility < 15:
                recommendations.append("😴 Low volatility ({:.1f}%): Consider waiting for catalyst".format(volatility))
            else:
                recommendations.append("📊 Normal volatility ({:.1f}%): Standard risk management applies".format(volatility))
            
            # Price action
            recent_returns = data['Close'].pct_change().tail(5)
            if recent_returns.mean() > 0.01:
                recommendations.append("🚀 Strong recent momentum: Trend continuation likely")
            elif recent_returns.mean() < -0.01:
                recommendations.append("🔻 Weak recent performance: Consider defensive strategies")
            
        except Exception as e:
            recommendations.append(f"⚠️ Recommendation generation error: {str(e)}")
        
        if not recommendations:
            recommendations.append("📊 Analysis inconclusive: Monitor for clearer signals")
        
        return recommendations
    
    def send_json_response(self, data):
        """Send JSON response with proper headers."""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            response_json = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            print(f"Error sending JSON response: {e}")
            traceback.print_exc()

def start_server():
    """Start the web server."""
    port = 8081  # Changed port to avoid conflicts
    
    try:
        server = HTTPServer(('localhost', port), TradingAnalysisHandler)
        
        print(f"=== LME Trading Analysis Web Server (Fixed) ===")
        print(f"Server starting at http://localhost:{port}")
        print(f"Opening browser...")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{port}')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print(f"Server ready! Press Ctrl+C to stop.")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print(f"\nServer stopped by user")
        server.shutdown()
    except Exception as e:
        print(f"Server error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    start_server()