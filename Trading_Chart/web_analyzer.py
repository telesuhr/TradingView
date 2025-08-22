"""Interactive web-based trading analysis system with symbol selection."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import webbrowser
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

class TradingAnalysisServer(SimpleHTTPRequestHandler):
    """Custom HTTP server for trading analysis."""
    
    def do_GET(self):
        """Handle GET requests."""
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
            self.send_error(404)
    
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
                    <option value="1095">3 Years</option>
                </select>
            </div>
            
            <div class="btn-group">
                <button class="btn-secondary" onclick="getSymbolInfo()">Symbol Info</button>
                <button class="btn-primary" onclick="runBasicAnalysis()">Basic Analysis</button>
                <button class="btn-success" onclick="runDeepAnalysis()">Deep Analysis</button>
            </div>
            
            <div class="loading" id="loading">
                <div>🔄 Analyzing... Please wait...</div>
                <div style="margin-top: 10px; font-size: 14px;">This may take 30-60 seconds for deep analysis</div>
            </div>
            
            <div class="results" id="results">
                <div id="resultsContent"></div>
            </div>
        </div>
    </div>

    <script>
        // Load symbols on page load
        window.onload = function() {
            loadSymbols();
        };
        
        function loadSymbols() {
            fetch('/api/symbols')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('symbolSelect');
                    select.innerHTML = '<option value="">Select a symbol...</option>';
                    
                    data.symbols.forEach(symbol => {
                        const option = document.createElement('option');
                        option.value = symbol.symbol;
                        option.textContent = `${symbol.name} (${symbol.symbol}) - ${symbol.records} records`;
                        select.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading symbols:', error);
                    document.getElementById('symbolSelect').innerHTML = '<option value="">Error loading symbols</option>';
                });
        }
        
        function getSymbolInfo() {
            const symbol = document.getElementById('symbolSelect').value;
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading();
            fetch(`/api/symbol-info?symbol=${encodeURIComponent(symbol)}`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    showSymbolInfo(data);
                })
                .catch(error => {
                    hideLoading();
                    showError('Error getting symbol info: ' + error);
                });
        }
        
        function runBasicAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading();
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    showAnalysisResults(data);
                })
                .catch(error => {
                    hideLoading();
                    showError('Error running analysis: ' + error);
                });
        }
        
        function runDeepAnalysis() {
            const symbol = document.getElementById('symbolSelect').value;
            const period = document.getElementById('periodSelect').value;
            
            if (!symbol) {
                alert('Please select a symbol first');
                return;
            }
            
            showLoading();
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=deep`)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    showAnalysisResults(data);
                })
                .catch(error => {
                    hideLoading();
                    showError('Error running deep analysis: ' + error);
                });
        }
        
        function showLoading() {
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
                <div class="symbol-info">
                    <p><strong>Analysis Period:</strong> ${data.analysis_period}</p>
                    <p><strong>Data Points:</strong> ${data.data_points} trading days</p>
                </div>
            `;
            
            // Current market metrics
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
            
            // Technical indicators
            if (data.technical_indicators) {
                html += `
                    <h4>🔍 Technical Indicators</h4>
                    <div class="analysis-grid">
                `;
                
                const indicators = data.technical_indicators;
                
                html += `
                    <div class="metric-card">
                        <div class="metric-value neutral">$${indicators.sma20.toFixed(2)}</div>
                        <div>SMA 20</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">$${indicators.sma50.toFixed(2)}</div>
                        <div>SMA 50</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value ${indicators.rsi < 30 ? 'positive' : indicators.rsi > 70 ? 'negative' : 'neutral'}">
                            ${indicators.rsi.toFixed(1)}
                        </div>
                        <div>RSI</div>
                        <div style="font-size: 0.8em;">
                            ${indicators.rsi < 30 ? 'Oversold' : indicators.rsi > 70 ? 'Overbought' : 'Neutral'}
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value ${indicators.macd >= 0 ? 'positive' : 'negative'}">
                            ${indicators.macd.toFixed(2)}
                        </div>
                        <div>MACD</div>
                    </div>
                `;
                
                html += `</div>`;
            }
            
            // Trading signals
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
            }
            
            // Strategy performance (deep analysis)
            if (data.strategy_performance) {
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
            
            // Recommendations
            if (data.recommendations) {
                html += `
                    <h4>💡 Recommendations</h4>
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
                <div style="color: red; padding: 20px; text-align: center;">
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
            recommendations.append("📈 Bullish trend: Price above both moving averages")
        elif current_price < sma20 < sma50:
            recommendations.append("📉 Bearish trend: Price below both moving averages")
        
        if rsi < 30:
            recommendations.append("🟢 RSI indicates oversold condition - potential buying opportunity")
        elif rsi > 70:
            recommendations.append("🔴 RSI indicates overbought condition - consider taking profits")
        
        # Recent signals recommendation
        recent_signals = [s for s in signals if s['date'] >= data.index[-7]]
        if recent_signals:
            buy_signals = len([s for s in recent_signals if 'BUY' in s['type'] or 'BULLISH' in s['type']])
            sell_signals = len([s for s in recent_signals if 'SELL' in s['type'] or 'BEARISH' in s['type']])
            
            if buy_signals > sell_signals:
                recommendations.append("🎯 Recent pattern analysis leans bullish")
            elif sell_signals > buy_signals:
                recommendations.append("⚠️ Recent pattern analysis leans bearish")
        
        # Volatility recommendation
        volatility = data['Close'].pct_change().std() * 100
        if volatility > 3:
            recommendations.append("⚡ High volatility detected - use smaller position sizes")
        elif volatility < 1:
            recommendations.append("😴 Low volatility - consider waiting for clearer signals")
        
        if not recommendations:
            recommendations.append("📊 Markets appear neutral - wait for clearer signals")
        
        return recommendations
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))

def start_server():
    """Start the web server."""
    port = 8080
    server = HTTPServer(('localhost', port), TradingAnalysisServer)
    
    print(f"=== LME Trading Analysis Web Server ===")
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