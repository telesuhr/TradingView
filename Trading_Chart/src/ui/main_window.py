"""Main window for LME Copper Trading System."""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QTextEdit, QGroupBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTabWidget,
    QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
import logging

from ..data import SQLServerConnector
from ..analysis import TechnicalIndicators, PatternRecognizer
from ..backtest import StrategyRunner

logger = logging.getLogger(__name__)


class DataLoaderThread(QThread):
    """Thread for loading data from SQL Server."""
    
    data_loaded = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, start_date=None, end_date=None):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        
    def run(self):
        """Load data in background thread."""
        try:
            with SQLServerConnector() as conn:
                data = conn.get_lme_copper_data(
                    start_date=self.start_date,
                    end_date=self.end_date
                )
                self.data_loaded.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BacktestThread(QThread):
    """Thread for running backtests."""
    
    backtest_complete = pyqtSignal(dict)
    progress_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, data, strategy_type, params):
        super().__init__()
        self.data = data
        self.strategy_type = strategy_type
        self.params = params
        
    def run(self):
        """Run backtest in background thread."""
        try:
            runner = StrategyRunner(self.data)
            
            if self.strategy_type == 'pattern':
                self.progress_update.emit("Running pattern strategy backtest...")
                result = runner.run_pattern_strategy(
                    patterns=self.params['patterns'],
                    position_size=self.params.get('position_size', 0.1),
                    confidence_threshold=self.params.get('confidence_threshold', 0.7)
                )
            elif self.strategy_type == 'optimize':
                self.progress_update.emit("Optimizing pattern combinations...")
                result = runner.optimize_pattern_combinations()
                result = {'optimization_results': result}
            else:
                self.progress_update.emit("Running indicator strategy backtest...")
                result = runner.run_indicator_strategy(
                    indicator_rules=self.params['rules'],
                    position_size=self.params.get('position_size', 0.1)
                )
            
            self.backtest_complete.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class TradingSystemMainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.current_signals = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("LME Copper Trading System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Chart tab
        self.chart_tab = self.create_chart_tab()
        self.tabs.addTab(self.chart_tab, "Chart Analysis")
        
        # Backtest tab
        self.backtest_tab = self.create_backtest_tab()
        self.tabs.addTab(self.backtest_tab, "Backtesting")
        
        # Signals tab
        self.signals_tab = self.create_signals_tab()
        self.tabs.addTab(self.signals_tab, "Trading Signals")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Load initial data
        self.load_data()
        
    def create_header(self):
        """Create header section."""
        header = QGroupBox("LME Copper Trading System")
        layout = QHBoxLayout()
        
        # Title
        title = QLabel("AI-Powered Chart Pattern Recognition")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Data controls
        self.load_btn = QPushButton("Reload Data")
        self.load_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_btn)
        
        header.setLayout(layout)
        return header
        
    def create_chart_tab(self):
        """Create chart analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Chart area (placeholder for Plotly chart)
        self.chart_widget = QTextEdit()
        self.chart_widget.setReadOnly(True)
        self.chart_widget.setHtml("<h3>Chart will be displayed here</h3>")
        layout.addWidget(self.chart_widget, 3)
        
        # Controls
        controls = QGroupBox("Chart Controls")
        controls_layout = QHBoxLayout()
        
        # Indicator selection
        controls_layout.addWidget(QLabel("Indicators:"))
        
        self.ma_check = QCheckBox("Moving Averages")
        self.ma_check.setChecked(True)
        controls_layout.addWidget(self.ma_check)
        
        self.rsi_check = QCheckBox("RSI")
        controls_layout.addWidget(self.rsi_check)
        
        self.macd_check = QCheckBox("MACD")
        controls_layout.addWidget(self.macd_check)
        
        self.bb_check = QCheckBox("Bollinger Bands")
        controls_layout.addWidget(self.bb_check)
        
        controls_layout.addStretch()
        
        self.update_chart_btn = QPushButton("Update Chart")
        self.update_chart_btn.clicked.connect(self.update_chart)
        controls_layout.addWidget(self.update_chart_btn)
        
        controls.setLayout(controls_layout)
        layout.addWidget(controls)
        
        tab.setLayout(layout)
        return tab
        
    def create_backtest_tab(self):
        """Create backtesting tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Strategy selection
        strategy_group = QGroupBox("Backtest Strategy")
        strategy_layout = QVBoxLayout()
        
        # Pattern selection
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Patterns:"))
        
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems([
            "MA Crossover",
            "RSI Divergence",
            "Support/Resistance Breakout",
            "Candlestick Patterns",
            "All Patterns"
        ])
        pattern_layout.addWidget(self.pattern_combo)
        
        pattern_layout.addWidget(QLabel("Position Size:"))
        self.position_size_spin = QDoubleSpinBox()
        self.position_size_spin.setRange(0.01, 1.0)
        self.position_size_spin.setSingleStep(0.05)
        self.position_size_spin.setValue(0.1)
        pattern_layout.addWidget(self.position_size_spin)
        
        strategy_layout.addLayout(pattern_layout)
        
        # Run buttons
        button_layout = QHBoxLayout()
        
        self.run_backtest_btn = QPushButton("Run Backtest")
        self.run_backtest_btn.clicked.connect(self.run_backtest)
        button_layout.addWidget(self.run_backtest_btn)
        
        self.optimize_btn = QPushButton("Optimize Patterns")
        self.optimize_btn.clicked.connect(self.optimize_patterns)
        button_layout.addWidget(self.optimize_btn)
        
        strategy_layout.addLayout(button_layout)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        # Results area
        results_group = QGroupBox("Backtest Results")
        results_layout = QVBoxLayout()
        
        # Metrics display
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(150)
        results_layout.addWidget(self.metrics_text)
        
        # Trade history table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels([
            "Entry Date", "Exit Date", "Type", "Entry Price", 
            "Exit Price", "P&L", "Return %"
        ])
        results_layout.addWidget(self.trades_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab
        
    def create_signals_tab(self):
        """Create trading signals tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Current signals
        signals_group = QGroupBox("Current Trading Signals")
        signals_layout = QVBoxLayout()
        
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(5)
        self.signals_table.setHorizontalHeaderLabels([
            "Date", "Type", "Price", "Confidence", "Details"
        ])
        signals_layout.addWidget(self.signals_table)
        
        # Analyze button
        self.analyze_btn = QPushButton("Analyze Current Patterns")
        self.analyze_btn.clicked.connect(self.analyze_patterns)
        signals_layout.addWidget(self.analyze_btn)
        
        signals_group.setLayout(signals_layout)
        layout.addWidget(signals_group)
        
        tab.setLayout(layout)
        return tab
        
    def load_data(self):
        """Load data from SQL Server."""
        self.status_label.setText("Loading data...")
        self.load_btn.setEnabled(False)
        
        # Start data loading thread
        self.data_thread = DataLoaderThread()
        self.data_thread.data_loaded.connect(self.on_data_loaded)
        self.data_thread.error_occurred.connect(self.on_data_error)
        self.data_thread.start()
        
    def on_data_loaded(self, data):
        """Handle loaded data."""
        self.data = data
        self.status_label.setText(f"Loaded {len(data)} days of data")
        self.load_btn.setEnabled(True)
        
        # Update chart
        self.update_chart()
        
    def on_data_error(self, error_msg):
        """Handle data loading error."""
        self.status_label.setText("Error loading data")
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to load data: {error_msg}")
        
    def update_chart(self):
        """Update the chart display."""
        if self.data is None:
            return
            
        # Create Plotly figure
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=self.data.index,
                open=self.data['Open'],
                high=self.data['High'],
                low=self.data['Low'],
                close=self.data['Close'],
                name='LME Copper'
            ),
            row=1, col=1
        )
        
        # Add indicators
        indicators = TechnicalIndicators()
        
        if self.ma_check.isChecked():
            ma20 = indicators.sma(self.data['Close'], 20)
            ma50 = indicators.sma(self.data['Close'], 50)
            
            fig.add_trace(
                go.Scatter(x=self.data.index, y=ma20, name='MA20', line=dict(color='blue')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=self.data.index, y=ma50, name='MA50', line=dict(color='red')),
                row=1, col=1
            )
            
        if self.bb_check.isChecked():
            bb = indicators.bollinger_bands(self.data['Close'])
            
            fig.add_trace(
                go.Scatter(x=self.data.index, y=bb['upper'], name='BB Upper', 
                          line=dict(color='gray', dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=self.data.index, y=bb['lower'], name='BB Lower',
                          line=dict(color='gray', dash='dash')),
                row=1, col=1
            )
            
        # Volume
        fig.add_trace(
            go.Bar(x=self.data.index, y=self.data['Volume'], name='Volume'),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title='LME Copper Price Chart',
            xaxis_title='Date',
            yaxis_title='Price (USD/MT)',
            height=600
        )
        
        # Save and display chart
        html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
        self.chart_widget.setHtml(html)
        
    def analyze_patterns(self):
        """Analyze current patterns."""
        if self.data is None:
            return
            
        self.status_label.setText("Analyzing patterns...")
        
        # Run pattern recognition
        recognizer = PatternRecognizer(self.data)
        signals = recognizer.analyze_all_patterns()
        
        # Filter recent signals
        recent_signals = [s for s in signals if s['date'] >= self.data.index[-10]]
        
        # Update signals table
        self.signals_table.setRowCount(len(recent_signals))
        
        for i, signal in enumerate(recent_signals):
            self.signals_table.setItem(i, 0, QTableWidgetItem(str(signal['date'].date())))
            self.signals_table.setItem(i, 1, QTableWidgetItem(signal['type']))
            self.signals_table.setItem(i, 2, QTableWidgetItem(f"{signal['price']:.2f}"))
            self.signals_table.setItem(i, 3, QTableWidgetItem(f"{signal['confidence']:.2%}"))
            self.signals_table.setItem(i, 4, QTableWidgetItem(signal['details']))
            
        self.status_label.setText(f"Found {len(recent_signals)} recent signals")
        
    def run_backtest(self):
        """Run backtest with selected parameters."""
        if self.data is None:
            return
            
        # Get selected patterns
        pattern_map = {
            "MA Crossover": ['MA_CROSSOVER_BUY', 'MA_CROSSOVER_SELL'],
            "RSI Divergence": ['RSI_BULLISH_DIVERGENCE', 'RSI_BEARISH_DIVERGENCE'],
            "Support/Resistance Breakout": ['RESISTANCE_BREAKOUT', 'SUPPORT_BREAKDOWN'],
            "Candlestick Patterns": ['HAMMER_BULLISH', 'SHOOTING_STAR_BEARISH', 
                                    'BULLISH_ENGULFING', 'BEARISH_ENGULFING'],
            "All Patterns": None  # Will use all patterns
        }
        
        selected = self.pattern_combo.currentText()
        patterns = pattern_map.get(selected)
        
        if patterns is None:
            patterns = sum(pattern_map.values(), [])
            
        params = {
            'patterns': patterns,
            'position_size': self.position_size_spin.value()
        }
        
        # Start backtest thread
        self.backtest_thread = BacktestThread(self.data, 'pattern', params)
        self.backtest_thread.backtest_complete.connect(self.on_backtest_complete)
        self.backtest_thread.progress_update.connect(lambda msg: self.status_label.setText(msg))
        self.backtest_thread.error_occurred.connect(self.on_backtest_error)
        self.backtest_thread.start()
        
        self.run_backtest_btn.setEnabled(False)
        
    def optimize_patterns(self):
        """Run pattern optimization."""
        if self.data is None:
            return
            
        # Start optimization thread
        self.backtest_thread = BacktestThread(self.data, 'optimize', {})
        self.backtest_thread.backtest_complete.connect(self.on_optimization_complete)
        self.backtest_thread.progress_update.connect(lambda msg: self.status_label.setText(msg))
        self.backtest_thread.error_occurred.connect(self.on_backtest_error)
        self.backtest_thread.start()
        
        self.optimize_btn.setEnabled(False)
        
    def on_backtest_complete(self, results):
        """Handle backtest completion."""
        self.run_backtest_btn.setEnabled(True)
        
        # Display metrics
        metrics = results['metrics']
        metrics_text = f"""
Backtest Results:
- Total Trades: {metrics['total_trades']}
- Win Rate: {metrics['win_rate']:.1f}%
- Total Return: {metrics['total_return']:.2f}%
- Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
- Max Drawdown: {metrics['max_drawdown']:.2f}%
- Profit Factor: {metrics['profit_factor']:.2f}
        """
        self.metrics_text.setText(metrics_text)
        
        # Display trades
        trades_df = results['trades']
        if not trades_df.empty:
            self.trades_table.setRowCount(len(trades_df))
            
            for i, (idx, trade) in enumerate(trades_df.iterrows()):
                self.trades_table.setItem(i, 0, QTableWidgetItem(str(trade['entry_date'].date())))
                self.trades_table.setItem(i, 1, QTableWidgetItem(str(trade['exit_date'].date())))
                self.trades_table.setItem(i, 2, QTableWidgetItem(trade['type']))
                self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade['entry_price']:.2f}"))
                self.trades_table.setItem(i, 4, QTableWidgetItem(f"{trade['exit_price']:.2f}"))
                self.trades_table.setItem(i, 5, QTableWidgetItem(f"{trade['pnl']:.2f}"))
                self.trades_table.setItem(i, 6, QTableWidgetItem(f"{trade['return_pct']:.2f}%"))
                
        self.status_label.setText("Backtest complete")
        
    def on_optimization_complete(self, results):
        """Handle optimization completion."""
        self.optimize_btn.setEnabled(True)
        
        # Display optimization results
        opt_df = results['optimization_results']
        
        # Show top 10 results
        top_results = opt_df.head(10)
        
        results_text = "Top 10 Pattern Combinations:\n\n"
        for idx, row in top_results.iterrows():
            results_text += f"{row['patterns']}\n"
            results_text += f"  - Win Rate: {row['win_rate']:.1f}%, Return: {row['total_return']:.1f}%\n\n"
            
        self.metrics_text.setText(results_text)
        self.status_label.setText("Optimization complete")
        
    def on_backtest_error(self, error_msg):
        """Handle backtest error."""
        self.run_backtest_btn.setEnabled(True)
        self.optimize_btn.setEnabled(True)
        self.status_label.setText("Backtest error")
        QMessageBox.critical(self, "Error", f"Backtest failed: {error_msg}")