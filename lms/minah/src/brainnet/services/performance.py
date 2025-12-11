"""
Performance metrics for trading strategies.
Includes Sharpe ratio, drawdown, win rate, and other key metrics.
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0, annualization_factor: int = 252) -> float:
    """
    Calculate the annualized Sharpe ratio for a series of returns.
    
    Args:
        returns: List of daily returns (as decimals, e.g., 0.01 for 1%)
        risk_free_rate: Annual risk-free rate (default: 0.0)
        annualization_factor: Number of trading days in a year (default: 252)
        
    Returns:
        Annualized Sharpe ratio (float)
    """
    if not returns:
        return 0.0
    
    returns = np.array(returns)
    if len(returns) < 2:
        return 0.0
    
    # Calculate excess returns
    excess_returns = returns - (risk_free_rate / annualization_factor)
    
    # Calculate mean and std of excess returns
    mean_return = np.mean(excess_returns)
    std_return = np.std(excess_returns, ddof=1)
    
    # Handle edge case of zero volatility
    if std_return == 0:
        return 0.0
    
    # Annualize the Sharpe ratio
    sharpe_ratio = mean_return / std_return * np.sqrt(annualization_factor)
    
    return float(sharpe_ratio)


def calculate_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """
    Calculate maximum drawdown and drawdown duration from an equity curve.
    
    Args:
        equity_curve: List of portfolio values over time
        
    Returns:
        Dictionary with max drawdown (as decimal) and drawdown duration (in periods)
    """
    if not equity_curve:
        return {"max_drawdown": 0.0, "drawdown_duration": 0}
    
    equity_curve = np.array(equity_curve)
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_curve)
    
    # Calculate drawdown series
    drawdown = (equity_curve - running_max) / running_max
    
    # Calculate max drawdown
    max_dd = np.min(drawdown)
    
    # Calculate drawdown duration
    drawdown_duration = 0
    current_duration = 0
    
    for dd in drawdown:
        if dd < -0.01:  # Consider it a drawdown if >1%
            current_duration += 1
            drawdown_duration = max(drawdown_duration, current_duration)
        else:
            current_duration = 0
    
    return {
        "max_drawdown": float(max_dd),
        "drawdown_duration": drawdown_duration
    }


def calculate_win_rate(trades: List[Dict]) -> Dict[str, float]:
    """
    Calculate win rate, average win/loss, and profit factor from trade history.
    
    Args:
        trades: List of trade dictionaries with 'profit' key
        
    Returns:
        Dictionary with win_rate, avg_win, avg_loss, profit_factor
    """
    if not trades:
        return {
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0
        }
    
    profits = [t.get('profit', 0) for t in trades]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    
    win_rate = len(wins) / len(profits) if profits else 0.0
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    
    # Calculate profit factor (gross profits / gross losses)
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    return {
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor
    }


def calculate_metrics(
    returns: List[float],
    equity_curve: List[float],
    trades: List[Dict],
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics.
    
    Args:
        returns: List of daily returns
        equity_curve: List of portfolio values over time
        trades: List of trade dictionaries with 'profit' key
        risk_free_rate: Annual risk-free rate (default: 0.0)
        annualization_factor: Number of trading days in a year (default: 252)
        
    Returns:
        Dictionary of performance metrics
    """
    if not returns or not equity_curve:
        return {}
    
    # Basic metrics
    total_return = (equity_curve[-1] / equity_curve[0] - 1) if equity_curve[0] != 0 else 0.0
    annualized_return = ((1 + total_return) ** (annualization_factor / len(returns)) - 1) if returns else 0.0
    
    # Calculate metrics
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate, annualization_factor)
    drawdown_metrics = calculate_drawdown(equity_curve)
    trade_metrics = calculate_win_rate(trades)
    
    # Combine all metrics
    metrics = {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "sharpe_ratio": sharpe,
        **drawdown_metrics,
        **trade_metrics,
        "num_trades": len(trades),
        "num_winning_trades": len([t for t in trades if t.get('profit', 0) > 0]),
        "num_losing_trades": len([t for t in trades if t.get('profit', 0) < 0]),
        "avg_trade_return": np.mean([t.get('profit', 0) for t in trades]) if trades else 0.0,
    }
    
    return metrics


def format_metrics(metrics: Dict[str, float]) -> str:
    """
    Format performance metrics as a human-readable string.
    
    Args:
        metrics: Dictionary of performance metrics
        
    Returns:
        Formatted string with performance metrics
    """
    if not metrics:
        return "No performance metrics available."
    
    # Format numbers appropriately
    formatted = []
    
    # Returns
    formatted.append("=== Returns ===")
    formatted.append(f"Total Return: {metrics.get('total_return', 0) * 100:.2f}%")
    formatted.append(f"Annualized Return: {metrics.get('annualized_return', 0) * 100:.2f}%")
    
    # Risk-adjusted metrics
    formatted.append("\n=== Risk-Adjusted Returns ===")
    formatted.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    
    # Drawdown
    formatted.append("\n=== Risk Metrics ===")
    formatted.append(f"Max Drawdown: {metrics.get('max_drawdown', 0) * 100:.2f}%")
    formatted.append(f"Drawdown Duration: {metrics.get('drawdown_duration', 0)} periods")
    
    # Trade statistics
    formatted.append("\n=== Trade Statistics ===")
    formatted.append(f"Win Rate: {metrics.get('win_rate', 0) * 100:.1f}%")
    formatted.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    formatted.append(f"Avg Win: {metrics.get('avg_win', 0):.2f}")
    formatted.append(f"Avg Loss: {metrics.get('avg_loss', 0):.2f}")
    formatted.append(f"Total Trades: {metrics.get('num_trades', 0)}")
    formatted.append(f"Winning Trades: {metrics.get('num_winning_trades', 0)}")
    formatted.append(f"Losing Trades: {metrics.get('num_losing_trades', 0)}")
    
    return "\n".join(formatted)
