"""Backtesting engine for trading strategies."""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: int = 1
    trade_type: str = 'BUY'  # BUY or SELL
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    commission: float = 0.0
    
    @property
    def is_open(self) -> bool:
        """Check if trade is still open."""
        return self.exit_date is None
    
    @property
    def pnl(self) -> float:
        """Calculate profit/loss."""
        if self.exit_price is None:
            return 0.0
        
        if self.trade_type == 'BUY':
            return (self.exit_price - self.entry_price) * self.quantity - self.commission
        else:  # SELL
            return (self.entry_price - self.exit_price) * self.quantity - self.commission
    
    @property
    def return_pct(self) -> float:
        """Calculate return percentage."""
        if self.exit_price is None or self.entry_price == 0:
            return 0.0
        
        if self.trade_type == 'BUY':
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:  # SELL
            return ((self.entry_price - self.exit_price) / self.entry_price) * 100


class BacktestEngine:
    """Main backtesting engine."""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.001,  # 0.1%
        slippage: float = 0.0005  # 0.05%
    ):
        """Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate per trade
            slippage: Slippage percentage
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # Portfolio state
        self.capital = initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
        
        # Performance metrics
        self.metrics = {}
        
    def reset(self):
        """Reset engine state."""
        self.capital = self.initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
        self.metrics = {}
        
    def execute_signal(
        self,
        signal: Dict[str, Any],
        current_price: float,
        current_date: datetime,
        position_size: float = 0.1  # 10% of capital
    ):
        """Execute a trading signal.
        
        Args:
            signal: Signal dictionary with type, confidence, etc.
            current_price: Current market price
            current_date: Current date
            position_size: Position size as fraction of capital
        """
        # Determine signal direction
        if 'BUY' in signal['type'] or 'BULLISH' in signal['type']:
            trade_type = 'BUY'
        elif 'SELL' in signal['type'] or 'BEARISH' in signal['type']:
            trade_type = 'SELL'
        else:
            return
        
        # Check if we have an open position
        if self.positions and self.positions[0].trade_type != trade_type:
            # Close existing position
            self.close_position(current_price, current_date)
        
        # Open new position if we have no position
        if not self.positions:
            # Calculate position size
            trade_value = self.capital * position_size
            quantity = int(trade_value / current_price)
            
            if quantity > 0:
                # Apply slippage
                entry_price = current_price * (1 + self.slippage if trade_type == 'BUY' else 1 - self.slippage)
                
                # Calculate commission
                commission = trade_value * self.commission_rate
                
                # Create trade
                trade = Trade(
                    entry_date=current_date,
                    entry_price=entry_price,
                    quantity=quantity,
                    trade_type=trade_type,
                    commission=commission
                )
                
                # Set stop loss and take profit based on ATR or fixed percentage
                trade.stop_loss = entry_price * (0.98 if trade_type == 'BUY' else 1.02)
                trade.take_profit = entry_price * (1.03 if trade_type == 'BUY' else 0.97)
                
                self.positions.append(trade)
                self.capital -= (trade_value + commission)
                
                logger.info(f"Opened {trade_type} position: {quantity} @ {entry_price:.2f}")
    
    def close_position(self, current_price: float, current_date: datetime):
        """Close current position."""
        if not self.positions:
            return
        
        trade = self.positions[0]
        
        # Apply slippage
        exit_price = current_price * (1 - self.slippage if trade.trade_type == 'BUY' else 1 + self.slippage)
        
        # Update trade
        trade.exit_date = current_date
        trade.exit_price = exit_price
        
        # Calculate proceeds
        proceeds = trade.quantity * exit_price
        commission = proceeds * self.commission_rate
        trade.commission += commission
        
        # Update capital
        self.capital += (proceeds - commission)
        
        # Move to closed trades
        self.closed_trades.append(trade)
        self.positions = []
        
        logger.info(f"Closed {trade.trade_type} position: {trade.quantity} @ {exit_price:.2f}, PnL: {trade.pnl:.2f}")
    
    def check_stops(self, high: float, low: float, current_date: datetime):
        """Check stop loss and take profit levels."""
        if not self.positions:
            return
        
        trade = self.positions[0]
        
        if trade.trade_type == 'BUY':
            # Check stop loss
            if trade.stop_loss and low <= trade.stop_loss:
                self.close_position(trade.stop_loss, current_date)
                return
            
            # Check take profit
            if trade.take_profit and high >= trade.take_profit:
                self.close_position(trade.take_profit, current_date)
                return
        
        else:  # SELL
            # Check stop loss
            if trade.stop_loss and high >= trade.stop_loss:
                self.close_position(trade.stop_loss, current_date)
                return
            
            # Check take profit
            if trade.take_profit and low <= trade.take_profit:
                self.close_position(trade.take_profit, current_date)
                return
    
    def update_equity(self, current_price: float, current_date: datetime):
        """Update equity curve."""
        # Calculate current portfolio value
        portfolio_value = self.capital
        
        # Add value of open positions
        for trade in self.positions:
            if trade.trade_type == 'BUY':
                position_value = trade.quantity * current_price
            else:  # SELL
                position_value = trade.quantity * (2 * trade.entry_price - current_price)
            portfolio_value += position_value
        
        self.equity_curve.append({
            'date': current_date,
            'equity': portfolio_value,
            'capital': self.capital,
            'positions': len(self.positions)
        })
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics."""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        # Basic metrics
        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl < 0]
        
        total_trades = len(self.closed_trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        
        # Profit factor
        gross_profit = sum([t.pnl for t in wins])
        gross_loss = abs(sum([t.pnl for t in losses]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Portfolio metrics
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df.set_index('date', inplace=True)
            
            # Total return
            final_equity = equity_df['equity'].iloc[-1]
            total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
            
            # Daily returns for Sharpe ratio
            daily_returns = equity_df['equity'].pct_change().dropna()
            if len(daily_returns) > 0:
                sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0.0
            
            # Maximum drawdown
            cumulative = equity_df['equity'] / equity_df['equity'].cummax() - 1
            max_drawdown = cumulative.min() * 100
        else:
            total_return = 0.0
            sharpe_ratio = 0.0
            max_drawdown = 0.0
        
        self.metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
        
        return self.metrics
    
    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as DataFrame."""
        if not self.closed_trades:
            return pd.DataFrame()
        
        trades_data = []
        for trade in self.closed_trades:
            trades_data.append({
                'entry_date': trade.entry_date,
                'exit_date': trade.exit_date,
                'type': trade.trade_type,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'return_pct': trade.return_pct,
                'commission': trade.commission
            })
        
        return pd.DataFrame(trades_data)