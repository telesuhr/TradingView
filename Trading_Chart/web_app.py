"""Simple web-based interface for LME Copper Trading System."""

import sys
import os
from datetime import datetime, timedelta
import webbrowser
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data import SQLServerConnector
from src.analysis import TechnicalIndicators, PatternRecognizer
from src.backtest import StrategyRunner

def create_chart(data, title="LME Copper Price Chart"):
    """Create interactive Plotly chart."""
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Price & Indicators', 'Volume', 'RSI')
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='LME Copper',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )
    
    # Technical indicators
    indicators = TechnicalIndicators()
    
    # Moving averages
    ma20 = indicators.sma(data['Close'], 20)
    ma50 = indicators.sma(data['Close'], 50)
    
    fig.add_trace(
        go.Scatter(x=data.index, y=ma20, name='SMA20', line=dict(color='blue', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=data.index, y=ma50, name='SMA50', line=dict(color='red', width=1)),
        row=1, col=1
    )
    
    # Bollinger Bands
    bb = indicators.bollinger_bands(data['Close'])
    
    fig.add_trace(
        go.Scatter(
            x=data.index, 
            y=bb['upper'], 
            name='BB Upper',
            line=dict(color='gray', dash='dash', width=1),
            showlegend=False
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=data.index, 
            y=bb['lower'], 
            name='BB Lower',
            line=dict(color='gray', dash='dash', width=1),
            fill='tonexty',
            fillcolor='rgba(128,128,128,0.1)',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Volume
    colors = ['green' if close >= open else 'red' 
              for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data.index, 
            y=data['Volume'], 
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    # RSI
    rsi = indicators.rsi(data['Close'])
    
    fig.add_trace(
        go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')),
        row=3, col=1
    )
    
    # RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="gray", row=3, col=1)
    
    # Mark trading signals
    recognizer = PatternRecognizer(data)
    signals = recognizer.analyze_all_patterns()
    
    # Filter recent signals
    recent_signals = [s for s in signals if s['date'] >= data.index[-60]]  # Last 60 days
    
    buy_signals = [s for s in recent_signals if 'BUY' in s['type'] or 'BULLISH' in s['type']]
    sell_signals = [s for s in recent_signals if 'SELL' in s['type'] or 'BEARISH' in s['type']]
    
    if buy_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in buy_signals],
                y=[s['price'] for s in buy_signals],
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='green'),
                name='Buy Signals',
                text=[f"{s['type']}<br>Confidence: {s['confidence']:.1%}" for s in buy_signals],
                hovertemplate='%{text}<extra></extra>'
            ),
            row=1, col=1
        )
    
    if sell_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in sell_signals],
                y=[s['price'] for s in sell_signals],
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='red'),
                name='Sell Signals',
                text=[f"{s['type']}<br>Confidence: {s['confidence']:.1%}" for s in sell_signals],
                hovertemplate='%{text}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        template='plotly_white'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Price (USD/MT)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    
    return fig

def generate_report(data, backtest_results):
    """Generate HTML report."""
    
    # Current market status
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    # Technical indicators current values
    indicators = TechnicalIndicators()
    current_sma20 = indicators.sma(data['Close'], 20).iloc[-1]
    current_sma50 = indicators.sma(data['Close'], 50).iloc[-1]
    current_rsi = indicators.rsi(data['Close']).iloc[-1]
    macd_data = indicators.macd(data['Close'])
    current_macd = macd_data['macd'].iloc[-1]
    
    # Get recent signals
    recognizer = PatternRecognizer(data)
    signals = recognizer.analyze_all_patterns()
    recent_signals = [s for s in signals if s['date'] >= data.index[-7]]  # Last 7 days
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LME Copper Trading Analysis Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 20px;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .metric-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .positive {{ color: #27ae60; }}
            .negative {{ color: #e74c3c; }}
            .neutral {{ color: #f39c12; }}
            .signals-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .signals-table th, .signals-table td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            .signals-table th {{
                background-color: #3498db;
                color: white;
            }}
            .backtest-results {{
                margin-top: 30px;
                background-color: #ecf0f1;
                padding: 20px;
                border-radius: 8px;
            }}
            .chart-container {{
                margin: 30px 0;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>LME Copper Trading Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">${current_price:.2f}</div>
                    <div class="metric-label">Current Price</div>
                    <div class="{'positive' if price_change >= 0 else 'negative'}">
                        {'+' if price_change >= 0 else ''}{price_change:.2f} ({price_change_pct:+.2f}%)
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${current_sma20:.2f}</div>
                    <div class="metric-label">SMA 20</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${current_sma50:.2f}</div>
                    <div class="metric-label">SMA 50</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{current_rsi:.1f}</div>
                    <div class="metric-label">RSI</div>
                    <div class="{'neutral' if 30 <= current_rsi <= 70 else 'positive' if current_rsi < 30 else 'negative'}">
                        {'Oversold' if current_rsi < 30 else 'Overbought' if current_rsi > 70 else 'Neutral'}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{current_macd:.2f}</div>
                    <div class="metric-label">MACD</div>
                </div>
            </div>
            
            <h2>Recent Trading Signals (Last 7 Days)</h2>
            <table class="signals-table">
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
    """
    
    if recent_signals:
        for signal in recent_signals[-10:]:  # Show last 10 signals
            signal_class = 'positive' if 'BUY' in signal['type'] or 'BULLISH' in signal['type'] else 'negative'
            html_content += f"""
                    <tr>
                        <td>{signal['date'].strftime('%Y-%m-%d')}</td>
                        <td class="{signal_class}">{signal['type'].replace('_', ' ')}</td>
                        <td>${signal['price']:.2f}</td>
                        <td>{signal['confidence']:.1%}</td>
                        <td>{signal['details']}</td>
                    </tr>
            """
    else:
        html_content += """
                    <tr>
                        <td colspan="5" style="text-align: center; font-style: italic;">No recent signals</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
    """
    
    # Add backtest results
    if backtest_results:
        html_content += f"""
            <div class="backtest-results">
                <h2>Strategy Backtest Results</h2>
                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-value">{backtest_results['total_trades']}</div>
                        <div class="metric-label">Total Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{backtest_results['win_rate']:.1f}%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if backtest_results['total_return'] >= 0 else 'negative'}">
                            {backtest_results['total_return']:+.2f}%
                        </div>
                        <div class="metric-label">Total Return</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{backtest_results['sharpe_ratio']:.2f}</div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value negative">{backtest_results['max_drawdown']:.2f}%</div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                </div>
            </div>
        """
    
    html_content += """
            <div class="chart-container">
                <h2>Price Chart with Technical Analysis</h2>
                <p><em>Chart will be displayed below</em></p>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
                <p>Generated by LME Copper Trading System | AI-Powered Technical Analysis</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main function to run web-based analysis."""
    print("=== LME Copper Trading System - Web Interface ===\n")
    
    try:
        # Load data
        print("Loading LME Copper data...")
        with SQLServerConnector() as conn:
            data = conn.get_lme_copper_data(
                start_date=datetime.now() - timedelta(days=180)  # 6 months
            )
        
        print(f"Loaded {len(data)} days of data")
        
        # Run backtest
        print("Running backtests...")
        runner = StrategyRunner(data)
        
        # Test best performing patterns
        backtest_result = runner.run_pattern_strategy(
            patterns=['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL', 'BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            position_size=0.1,
            confidence_threshold=0.7
        )
        
        # Create chart
        print("Creating interactive chart...")
        fig = create_chart(data)
        
        # Generate HTML report
        print("Generating HTML report...")
        html_report = generate_report(data, backtest_result['metrics'])
        
        # Save chart as HTML
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
        
        # Combine report and chart
        full_html = html_report.replace(
            '<p><em>Chart will be displayed below</em></p>',
            chart_html
        )
        
        # Save to file
        output_file = 'lme_copper_analysis.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"\n[OK] Analysis complete!")
        print(f"[OK] Report saved to: {output_file}")
        print(f"[OK] Opening in web browser...")
        
        # Open in browser
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[SUCCESS] Web interface launched successfully!")
        print("[INFO] Interactive chart with trading signals is now open in your browser.")
        input("\nPress Enter to exit...")
    else:
        print("\n[ERROR] Failed to launch web interface.")
        input("\nPress Enter to exit...")