"""Interactive web-based trading analysis system - Enhanced Version."""

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
    """Enhanced HTTP request handler with better error handling."""
    
    def do_GET(self):
        """Handle GET requests with robust error handling."""
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
            try:
                self.send_error(500, f"Internal server error: {str(e)}")
            except:
                pass
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        return
    
    def serve_main_page(self):
        """Serve the main web interface with beautiful design and charts."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>LME Trading Analysis System</title>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js"></script>
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
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
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
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
            font-size: 14px;
        }
        select, input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
            transition: all 0.3s ease;
            background: white;
        }
        select:focus, input:focus {
            border-color: #3498db;
            outline: none;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin: 30px 0;
        }
        button {
            padding: 16px 25px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
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
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        button:active {
            transform: translateY(-1px);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            margin: 20px 0;
        }
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .results {
            margin-top: 30px;
            display: none;
        }
        .chart-section {
            background: white;
            padding: 25px;
            margin: 25px 0;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .chart-container {
            position: relative;
            height: 450px;
            margin: 20px 0;
        }
        .chart-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin: 25px 0;
        }
        .chart-mini {
            height: 300px;
        }
        .symbol-info {
            background: linear-gradient(135deg, #e8f4f8, #d4f1f4);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #3498db;
        }
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
            border: 1px solid #e1e8ed;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2.2em;
            font-weight: 700;
            margin: 15px 0;
            line-height: 1;
        }
        .metric-label {
            font-size: 14px;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .positive { color: #27ae60; }
        .negative { color: #e74c3c; }
        .neutral { color: #f39c12; }
        .strategy-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        .strategy-table th, .strategy-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e1e8ed;
        }
        .strategy-table th {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }
        .strategy-table tr:hover {
            background: #f8f9fa;
        }
        .section-title {
            color: #2c3e50;
            font-size: 1.8em;
            font-weight: 700;
            margin: 40px 0 20px 0;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
            position: relative;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -3px;
            left: 0;
            width: 60px;
            height: 3px;
            background: #e74c3c;
        }
        .error {
            background: linear-gradient(135deg, #ffe6e6, #ffcccc);
            color: #c0392b;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #e74c3c;
            box-shadow: 0 5px 20px rgba(231, 76, 60, 0.1);
        }
        .success {
            background: linear-gradient(135deg, #e6ffe6, #ccffcc);
            color: #27ae60;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 5px solid #27ae60;
            box-shadow: 0 5px 20px rgba(39, 174, 96, 0.1);
        }
        .recommendation-card {
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid #f39c12;
            box-shadow: 0 2px 10px rgba(243, 156, 18, 0.1);
        }
        @media (max-width: 768px) {
            .form-section, .chart-grid, .btn-group {
                grid-template-columns: 1fr;
            }
            .analysis-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 LME Trading Analysis System</h1>
            <p>AI-Powered Multi-Symbol Technical Analysis with Interactive Charts</p>
        </div>
        
        <div class="content">
            <div class="form-section">
                <div class="form-group">
                    <label for="symbolSelect">📈 Select Symbol for Analysis:</label>
                    <select id="symbolSelect">
                        <option value="">Loading symbols...</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="periodSelect">📅 Analysis Period:</label>
                    <select id="periodSelect">
                        <option value="180">6 Months</option>
                        <option value="365" selected>1 Year</option>
                        <option value="730">2 Years</option>
                    </select>
                </div>
            </div>
            
            <div class="btn-group">
                <button class="btn-secondary" onclick="getSymbolInfo()">
                    📊 Symbol Info
                </button>
                <button class="btn-primary" onclick="runBasicAnalysis()">
                    📈 Basic Analysis
                </button>
                <button class="btn-success" onclick="runDeepAnalysis()">
                    🔍 Deep Analysis
                </button>
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <div style="color: #3498db; font-size: 18px; font-weight: 600;">
                    🔄 Analyzing... Please wait
                </div>
                <div style="margin-top: 10px; font-size: 14px; color: #6c757d;" id="loadingMessage">
                    Processing market data and generating insights...
                </div>
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
            console.log('Loading symbols from server...');
            const select = document.getElementById('symbolSelect');
            select.innerHTML = '<option value="">Loading symbols...</option>';
            
            fetch('/api/symbols')
                .then(response => {
                    console.log('Symbols response status:', response.status);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Symbols data received:', data);
                    select.innerHTML = '<option value="">Select a symbol...</option>';
                    
                    if (data.error) {
                        console.error('Server error:', data.error);
                        select.innerHTML = `<option value="">Error: ${data.error}</option>`;
                        showError(`Symbol loading error: ${data.error}`);
                        return;
                    }
                    
                    if (data.symbols && Array.isArray(data.symbols) && data.symbols.length > 0) {
                        console.log(`Loading ${data.symbols.length} symbols`);
                        data.symbols.forEach((symbol, index) => {
                            const option = document.createElement('option');
                            option.value = symbol.symbol;
                            option.textContent = `${symbol.name} (${symbol.records.toLocaleString()} records)`;
                            select.appendChild(option);
                        });
                        console.log('Symbols loaded successfully');
                    } else {
                        console.warn('No symbols found in response');
                        select.innerHTML = '<option value="">No symbols available</option>';
                    }
                })
                .catch(error => {
                    console.error('Error loading symbols:', error);
                    select.innerHTML = '<option value="">Failed to load symbols</option>';
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
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
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
            
            // Sequential loading to avoid timeout
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=basic`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    return response.json();
                })
                .then(analysisData => {
                    if (analysisData.error) {
                        throw new Error(analysisData.error);
                    }
                    
                    // Load chart data separately
                    return fetch(`/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${period}`)
                        .then(response => response.json())
                        .then(chartData => {
                            hideLoading();
                            showAnalysisResults(analysisData, chartData);
                        });
                })
                .catch(error => {
                    hideLoading();
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
            
            showLoading('Running comprehensive deep analysis...');
            
            // Use timeout and better error handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 second timeout
            
            fetch(`/api/analyze?symbol=${encodeURIComponent(symbol)}&period=${period}&type=deep`, {
                signal: controller.signal
            })
                .then(response => {
                    clearTimeout(timeoutId);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(analysisData => {
                    if (analysisData.error) {
                        throw new Error(analysisData.error);
                    }
                    
                    // Load chart data
                    return fetch(`/api/chart-data?symbol=${encodeURIComponent(symbol)}&period=${period}`)
                        .then(response => response.json())
                        .then(chartData => {
                            hideLoading();
                            showAnalysisResults(analysisData, chartData);
                        });
                })
                .catch(error => {
                    clearTimeout(timeoutId);
                    hideLoading();
                    if (error.name === 'AbortError') {
                        showError('Analysis timed out. Please try with a shorter period or different symbol.');
                    } else {
                        showError('Error running deep analysis: ' + error.message);
                    }
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
                    <h4 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 1.5em;">${data.symbol}</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div><strong>Total Records:</strong> ${data.total_records.toLocaleString()}</div>
                        <div><strong>Date Range:</strong> ${data.date_range}</div>
                        <div><strong>Average Price:</strong> $${data.avg_price}</div>
                        <div><strong>Price Range:</strong> $${data.min_price} - $${data.max_price}</div>
                        <div><strong>Average Volume:</strong> ${data.avg_volume}</div>
                        <div><strong>Data Quality:</strong> ${data.quality_score}/100</div>
                    </div>
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
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div><strong>Analysis Period:</strong> ${data.analysis_period}</div>
                        <div><strong>Data Points:</strong> ${data.data_points} trading days</div>
                    </div>
                </div>
            `;
            
            // Charts section
            html += `
                <div class="chart-section">
                    <h4 class="section-title">📊 Price Chart with Technical Indicators</h4>
                    <div class="chart-container">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            `;
            
            if (data.technical_indicators) {
                html += `
                    <div class="chart-grid">
                        <div class="chart-section">
                            <h4 style="color: #2c3e50; margin-bottom: 20px;">🔍 Technical Indicators</h4>
                            <div class="chart-container chart-mini">
                                <canvas id="indicatorsChart"></canvas>
                            </div>
                        </div>
                        <div class="chart-section">
                            <h4 style="color: #2c3e50; margin-bottom: 20px;">📊 Current Indicators</h4>
                            <div class="analysis-grid" style="grid-template-columns: 1fr 1fr;">
                                <div class="metric-card">
                                    <div class="metric-value neutral">$${data.technical_indicators.sma20.toFixed(2)}</div>
                                    <div class="metric-label">SMA 20</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value neutral">$${data.technical_indicators.sma50.toFixed(2)}</div>
                                    <div class="metric-label">SMA 50</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value ${data.technical_indicators.rsi < 30 ? 'positive' : data.technical_indicators.rsi > 70 ? 'negative' : 'neutral'}">
                                        ${data.technical_indicators.rsi.toFixed(1)}
                                    </div>
                                    <div class="metric-label">RSI</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value ${data.technical_indicators.macd >= 0 ? 'positive' : 'negative'}">
                                        ${data.technical_indicators.macd.toFixed(2)}
                                    </div>
                                    <div class="metric-label">MACD</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Current market metrics
            if (data.current_metrics) {
                html += `
                    <h4 class="section-title">📊 Current Market Status</h4>
                    <div class="analysis-grid">
                        <div class="metric-card">
                            <div class="metric-value ${data.current_metrics.price_change >= 0 ? 'positive' : 'negative'}">
                                $${data.current_metrics.current_price.toFixed(2)}
                            </div>
                            <div class="metric-label">Current Price</div>
                            <div style="font-size: 0.9em; margin-top: 8px; color: ${data.current_metrics.price_change >= 0 ? '#27ae60' : '#e74c3c'};">
                                ${data.current_metrics.price_change >= 0 ? '+' : ''}${data.current_metrics.price_change.toFixed(2)} 
                                (${data.current_metrics.price_change_pct.toFixed(2)}%)
                            </div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value neutral">
                                ${data.current_metrics.volatility.toFixed(2)}%
                            </div>
                            <div class="metric-label">Daily Volatility</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-value neutral">
                                ${data.current_metrics.volume.toLocaleString()}
                            </div>
                            <div class="metric-label">Average Volume</div>
                        </div>
                    </div>
                `;
            }
            
            // Strategy performance (deep analysis)
            if (data.strategy_performance && data.strategy_performance.length > 0) {
                html += `
                    <div class="chart-section">
                        <h4 class="section-title">📊 Strategy Performance Analysis</h4>
                        <div class="chart-container chart-mini">
                            <canvas id="performanceChart"></canvas>
                        </div>
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
                            <td style="font-weight: 600;">${strategy.name}</td>
                            <td>${strategy.trades}</td>
                            <td>${strategy.win_rate.toFixed(1)}%</td>
                            <td class="${strategy.total_return >= 0 ? 'positive' : 'negative'}" style="font-weight: 600;">
                                ${strategy.total_return >= 0 ? '+' : ''}${strategy.total_return.toFixed(2)}%
                            </td>
                            <td>${strategy.sharpe_ratio.toFixed(2)}</td>
                            <td class="negative">${strategy.max_drawdown.toFixed(2)}%</td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table></div>`;
            }
            
            // Trading signals
            if (data.recent_signals && data.recent_signals.length > 0) {
                html += `
                    <h4 class="section-title">🎯 Recent Trading Signals</h4>
                    <table class="strategy-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Signal Type</th>
                                <th>Price</th>
                                <th>Confidence</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.recent_signals.slice(0, 10).forEach(signal => {
                    const signalClass = signal.type.includes('BUY') || signal.type.includes('BULLISH') ? 'positive' : 'negative';
                    html += `
                        <tr>
                            <td>${signal.date}</td>
                            <td class="${signalClass}" style="font-weight: 600;">${signal.type.replace(/_/g, ' ')}</td>
                            <td>$${signal.price.toFixed(2)}</td>
                            <td>${(signal.confidence * 100).toFixed(1)}%</td>
                            <td style="font-size: 0.9em;">${signal.details}</td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table>`;
            }
            
            // Recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                html += `
                    <h4 class="section-title">💡 AI Recommendations</h4>
                    <div style="display: grid; gap: 15px;">
                `;
                
                data.recommendations.forEach(rec => {
                    html += `<div class="recommendation-card">${rec}</div>`;
                });
                
                html += `</div>`;
            }
            
            document.getElementById('resultsContent').innerHTML = html;
            document.getElementById('results').style.display = 'block';
            
            // Create charts after DOM is updated
            setTimeout(() => {
                createCharts(data, chartData);
            }, 100);
        }
        
        function createCharts(analysisData, chartData) {
            console.log('Creating charts with data:', chartData);
            
            if (!chartData || chartData.error) {
                console.log('Chart data error:', chartData);
                return;
            }
            
            if (!chartData.dates || chartData.dates.length === 0) {
                console.log('No chart dates available');
                return;
            }
            
            // Price Chart with Moving Averages
            const priceCtx = document.getElementById('priceChart');
            if (priceCtx) {
                console.log('Creating price chart with', chartData.dates.length, 'data points');
                
                // Simple chart data structure
                const validCloseData = chartData.close_prices.filter(price => price !== null && price !== undefined && !isNaN(price));
                
                if (validCloseData.length === 0) {
                    console.log('No valid price data available');
                    return;
                }
                
                console.log('Valid data points:', validCloseData.length);
                
                // Create datasets with simple arrays
                const datasets = [
                    {
                        label: 'Close Price',
                        data: chartData.close_prices,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    }
                ];
                
                // Add SMA lines if available
                if (chartData.sma20 && chartData.sma20.some(v => v !== null && !isNaN(v))) {
                    datasets.push({
                        label: 'SMA 20',
                        data: chartData.sma20,
                        borderColor: '#e74c3c',
                        backgroundColor: 'transparent',
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 0
                    });
                }
                
                if (chartData.sma50 && chartData.sma50.some(v => v !== null && !isNaN(v))) {
                    datasets.push({
                        label: 'SMA 50',
                        data: chartData.sma50,
                        borderColor: '#f39c12',
                        backgroundColor: 'transparent',
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 0
                    });
                }
                
                priceChart = new Chart(priceCtx, {
                    type: 'line',
                    data: {
                        labels: chartData.dates,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: `${analysisData.symbol} - Price Chart`,
                                font: { size: 16, weight: 'bold' }
                            },
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            x: {
                                type: 'category',
                                grid: {
                                    display: false
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Price ($)'
                                },
                                grid: {
                                    color: '#e1e8ed'
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        }
                    }
                });
                
                console.log('Price chart created successfully');
            }
            
            // Technical Indicators Chart (RSI)
            const indicatorsCtx = document.getElementById('indicatorsChart');
            if (indicatorsCtx && chartData.rsi && chartData.rsi.some(v => v !== null && !isNaN(v))) {
                console.log('Creating RSI chart');
                
                indicatorsChart = new Chart(indicatorsCtx, {
                    type: 'line',
                    data: {
                        labels: chartData.dates,
                        datasets: [{
                            label: 'RSI',
                            data: chartData.rsi,
                            borderColor: '#9b59b6',
                            backgroundColor: 'rgba(155, 89, 182, 0.1)',
                            fill: true,
                            tension: 0.1,
                            pointRadius: 0,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'RSI (Relative Strength Index)',
                                font: { size: 14, weight: 'bold' }
                            }
                        },
                        scales: {
                            x: {
                                type: 'category',
                                grid: {
                                    display: false
                                }
                            },
                            y: {
                                min: 0,
                                max: 100,
                                title: {
                                    display: true,
                                    text: 'RSI Value'
                                },
                                grid: {
                                    color: '#e1e8ed'
                                }
                            }
                        }
                    }
                });
                console.log('RSI chart created successfully');
            }
            
            // Performance Chart (for strategy performance)
            const performanceCtx = document.getElementById('performanceChart');
            if (performanceCtx && analysisData.strategy_performance && analysisData.strategy_performance.length > 0) {
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
                            borderWidth: 2,
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Strategy Performance Comparison',
                                font: { size: 14, weight: 'bold' }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Return (%)'
                                },
                                grid: {
                                    color: '#e1e8ed'
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
                    <p style="font-size: 0.9em; margin-top: 15px;">
                        <strong>Troubleshooting:</strong><br>
                        • Try selecting a different symbol<br>
                        • Check your internet connection<br>
                        • Try a shorter analysis period<br>
                        • Refresh the page and try again
                    </p>
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
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            print(f"Error serving main page: {e}")
    
    def serve_symbols_list(self):
        """Serve available symbols list with error handling and name sorting."""
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
                    WHERE Market_Date >= DATEADD(year, -5, GETDATE())
                    GROUP BY market_name
                    HAVING COUNT(*) > 50
                    ORDER BY COUNT(*) DESC
                """)
                
                symbols = []
                rows = cursor.fetchall()
                print(f"Found {len(rows)} symbols in database")
                
                for row in rows:
                    try:
                        symbol = str(row[0]) if row[0] else ''
                        name = symbol
                        record_count = int(row[1]) if row[1] is not None else 0
                        start_date = str(row[2]) if row[2] else ''
                        end_date = str(row[3]) if row[3] else ''
                        
                        # Create friendly names with more comprehensive mapping
                        if 'LMCADS03' in symbol:
                            name = 'LME Copper'
                        elif 'LMAHDS03' in symbol:
                            name = 'LME Aluminum'
                        elif 'LMZSDS03' in symbol:
                            name = 'LME Zinc'
                        elif 'LMNIDS03' in symbol:
                            name = 'LME Nickel'
                        elif 'LMPBDS03' in symbol:
                            name = 'LME Lead'
                        elif 'LMSNDS03' in symbol:
                            name = 'LME Tin'
                        elif 'XAU' in symbol and 'Comdty' in symbol:
                            name = 'Gold Spot'
                        elif 'XAG' in symbol and 'Comdty' in symbol:
                            name = 'Silver Spot'
                        elif 'GC1' in symbol:
                            name = 'Gold Futures'
                        elif 'SI1' in symbol:
                            name = 'Silver Futures'
                        elif 'HG1' in symbol:
                            name = 'Copper Futures'
                        elif 'SPX' in symbol:
                            name = 'S&P 500 Index'
                        elif 'DJI' in symbol:
                            name = 'Dow Jones Index'
                        elif 'NDX' in symbol:
                            name = 'NASDAQ 100'
                        elif 'C 1' in symbol:
                            name = 'Corn Futures'
                        elif 'S 1' in symbol:
                            name = 'Soybean Futures'
                        elif 'W 1' in symbol:
                            name = 'Wheat Futures'
                        elif 'EURUSD' in symbol:
                            name = 'EUR/USD'
                        elif 'GBPUSD' in symbol:
                            name = 'GBP/USD'
                        elif 'USDJPY' in symbol:
                            name = 'USD/JPY'
                        elif 'CLA' in symbol:
                            name = 'Crude Oil WTI'
                        elif 'CO1' in symbol:
                            name = 'Brent Oil'
                        
                        symbols.append({
                            'symbol': symbol,
                            'name': name,
                            'records': record_count,
                            'date_range': f"{start_date} to {end_date}",
                            'earliest_date': start_date,
                            'latest_date': end_date
                        })
                        
                    except Exception as row_error:
                        print(f"Error processing row {row}: {row_error}")
                        continue
                
                # Sort symbols by name for better user experience
                symbols.sort(key=lambda x: x['name'])
                print(f"Sorted {len(symbols)} symbols by name")
                
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
            print(f"Error in serve_symbol_info: {e}")
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
                    SELECT TOP 1000
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
                    data = data.dropna()  # Remove rows with NaN values
            
            if data.empty:
                raise ValueError(f"No valid data available for {symbol}")
            
            # Calculate technical indicators for charts
            print(f"Calculating indicators for {len(data)} data points")
            indicators = TechnicalIndicators()
            
            try:
                sma20 = indicators.sma(data['Close'], 20)
                sma50 = indicators.sma(data['Close'], 50)
                rsi = indicators.rsi(data['Close'])
                print("Technical indicators calculated successfully")
            except Exception as ind_error:
                print(f"Indicator calculation error: {ind_error}")
                sma20 = pd.Series([None] * len(data), index=data.index)
                sma50 = pd.Series([None] * len(data), index=data.index)
                rsi = pd.Series([None] * len(data), index=data.index)
            
            # Prepare chart data with safe conversion
            def safe_convert(series):
                """Convert pandas series to list, handling NaN values."""
                try:
                    if hasattr(series, 'values'):
                        return [None if pd.isna(x) else float(x) for x in series.values]
                    else:
                        return [None if pd.isna(x) else float(x) for x in series]
                except Exception as e:
                    print(f"Safe convert error: {e}")
                    return []
            
            # Create chart data
            dates = [d.strftime('%Y-%m-%d') for d in data.index]
            close_prices = safe_convert(data['Close'])
            sma20_values = safe_convert(sma20)
            sma50_values = safe_convert(sma50)
            rsi_values = safe_convert(rsi)
            volume_values = safe_convert(data['Volume'])
            
            chart_data = {
                'dates': dates,
                'close_prices': close_prices,
                'sma20': sma20_values,
                'sma50': sma50_values,
                'rsi': rsi_values,
                'volume': volume_values,
                'data_points': len(dates)
            }
            
            print(f"Chart data prepared: {len(dates)} dates, {len(close_prices)} prices")
            
        except Exception as e:
            print(f"Error in serve_chart_data: {e}")
            traceback.print_exc()
            chart_data = {'error': str(e)}
        
        self.send_json_response(chart_data)
    
    def serve_analysis(self, query_string):
        """Serve trading analysis results with timeout handling."""
        try:
            params = parse_qs(query_string)
            symbol = params.get('symbol', [''])[0]
            period = int(params.get('period', ['365'])[0])
            analysis_type = params.get('type', ['basic'])[0]
            
            if not symbol:
                raise ValueError("Symbol parameter is required")
            
            # Load data with limit to prevent timeout
            with SQLServerConnector() as conn:
                query = f"""
                    SELECT TOP 1000
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
                    data = data.dropna()  # Remove rows with NaN values
            
            if data.empty:
                raise ValueError(f"No valid data available for {symbol} in the specified period")
            
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
        
        try:
            # Current market metrics
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
            
            # Technical indicators
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
            
            # Lightweight pattern recognition
            try:
                print("Running pattern recognition...")
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
                    'details': str(signal['details'])
                } for signal in recent_signals[:5]]  # Limit to 5 signals
                
                print(f"Found {len(recent_signals)} recent signals")
                
            except Exception as pattern_error:
                print(f"Pattern recognition failed: {pattern_error}")
                response['recent_signals'] = []
                signals = []
            
            # Deep analysis
            if analysis_type == 'deep':
                try:
                    response['strategy_performance'] = self.run_strategy_analysis(data)
                    response['recommendations'] = self.generate_recommendations(data, signals)
                except Exception as e:
                    print(f"Deep analysis error: {e}")
                    response['strategy_performance'] = []
                    response['recommendations'] = [f"深層分析でエラーが発生しました: {str(e)}"]
            
        except Exception as e:
            print(f"Analysis error: {e}")
            response['error'] = str(e)
        
        return response
    
    def run_strategy_analysis(self, data):
        """Run lightweight strategy analysis to avoid timeout."""
        print("Running strategy analysis...")
        
        # Simplified strategies to reduce processing time
        strategies = {
            'MA Crossover': {
                'patterns': ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
                'position_size': 0.08,
                'confidence': 0.70
            },
            'Candlestick': {
                'patterns': ['BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
                'position_size': 0.10,
                'confidence': 0.75
            }
        }
        
        results = []
        
        try:
            runner = StrategyRunner(data)
            
            for name, config in strategies.items():
                try:
                    print(f"Testing strategy: {name}")
                    
                    # Run with timeout protection
                    result = runner.run_pattern_strategy(
                        patterns=config['patterns'],
                        position_size=config['position_size'],
                        confidence_threshold=config['confidence']
                    )
                    
                    if result and 'metrics' in result:
                        metrics = result['metrics']
                        
                        results.append({
                            'name': name,
                            'trades': int(metrics.get('total_trades', 0)),
                            'win_rate': float(metrics.get('win_rate', 0.0)),
                            'total_return': float(metrics.get('total_return', 0.0)),
                            'sharpe_ratio': float(metrics.get('sharpe_ratio', 0.0)),
                            'max_drawdown': float(metrics.get('max_drawdown', 0.0))
                        })
                        print(f"Strategy {name} completed: {metrics.get('total_trades', 0)} trades")
                    
                except Exception as strategy_error:
                    print(f"Strategy {name} failed: {strategy_error}")
                    # Add placeholder result to avoid empty response
                    results.append({
                        'name': f"{name} (Failed)",
                        'trades': 0,
                        'win_rate': 0.0,
                        'total_return': 0.0,
                        'sharpe_ratio': 0.0,
                        'max_drawdown': 0.0
                    })
                    continue
                    
        except Exception as e:
            print(f"Strategy analysis failed: {e}")
            # Return basic placeholder results
            results = [
                {
                    'name': 'Analysis Failed',
                    'trades': 0,
                    'win_rate': 0.0,
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                }
            ]
        
        print(f"Strategy analysis completed with {len(results)} results")
        return results
    
    def generate_recommendations(self, data, signals):
        """Generate trading recommendations based on analysis."""
        recommendations = []
        
        try:
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
                
        except Exception as e:
            print(f"Recommendation error: {e}")
            recommendations.append(f"推奨事項の生成でエラーが発生しました: {str(e)}")
        
        return recommendations
    
    def send_json_response(self, data):
        """Send JSON response with safe serialization."""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            # Simple and safe JSON conversion
            import datetime
            import decimal
            
            def safe_json_convert(obj):
                """Safely convert objects for JSON serialization."""
                if obj is None:
                    return None
                elif isinstance(obj, bool):
                    return obj
                elif isinstance(obj, (int, float, str)):
                    return obj
                elif isinstance(obj, (datetime.datetime, datetime.date)):
                    return str(obj)
                elif isinstance(obj, decimal.Decimal):
                    return float(obj)
                elif isinstance(obj, dict):
                    return {str(k): safe_json_convert(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [safe_json_convert(item) for item in obj]
                else:
                    # Convert everything else to string as fallback
                    return str(obj)
            
            # Convert data safely
            safe_data = safe_json_convert(data)
            response_json = json.dumps(safe_data, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            print(f"JSON response error: {e}")
            traceback.print_exc()
            try:
                # Send minimal error response
                error_response = '{"error": "JSON serialization failed"}'
                self.wfile.write(error_response.encode('utf-8'))
            except:
                pass

def start_enhanced_server():
    """Start the enhanced web server."""
    port = 8084
    server = HTTPServer(('localhost', port), TradingAnalysisHandler)
    
    print(f"=== LME Trading Analysis System - Enhanced Version ===")
    print(f"Server starting at http://localhost:{port}")
    print(f"Beautiful UI with interactive charts")
    print(f"Enhanced error handling and stability")
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
    start_enhanced_server()