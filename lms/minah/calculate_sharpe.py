#!/usr/bin/env python3
"""
Calculate Sharpe ratio from Minah, Carter, Banis, or generic yfinance data.
"""

import argparse
import json
import math
import statistics
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252,
) -> float:
    """Calculate the annualized Sharpe ratio for a series of returns."""
    if not returns or len(returns) < 2:
        return 0.0

    excess = [r - (risk_free_rate / annualization_factor) for r in returns]
    mean_ret = statistics.fmean(excess)
    # Use sample standard deviation
    try:
        std_ret = statistics.stdev(excess)
    except statistics.StatisticsError:
        return 0.0

    if std_ret == 0:
        return 0.0

    return (mean_ret / std_ret) * math.sqrt(annualization_factor)


def calculate_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """Calculate maximum drawdown and drawdown duration from an equity curve."""
    if not equity_curve:
        return {"max_drawdown": 0.0, "drawdown_duration": 0}

    running_max = []
    current_max = equity_curve[0]
    for v in equity_curve:
        current_max = max(current_max, v)
        running_max.append(current_max)

    drawdowns = []
    for v, m in zip(equity_curve, running_max):
        drawdowns.append((v - m) / m if m != 0 else 0.0)

    max_dd = min(drawdowns)

    drawdown_duration = 0
    current_duration = 0
    for dd in drawdowns:
        if dd < -0.01:
            current_duration += 1
            drawdown_duration = max(drawdown_duration, current_duration)
        else:
            current_duration = 0

    return {"max_drawdown": float(max_dd), "drawdown_duration": drawdown_duration}


def calculate_win_rate(trades: List[Dict]) -> Dict[str, float]:
    """Calculate win rate, average win/loss, and profit factor from trade history."""
    if not trades:
        return {
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
        }

    profits = [t.get("profit", 0) for t in trades]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]

    win_rate = len(wins) / len(profits) if profits else 0.0
    avg_win = statistics.fmean(wins) if wins else 0.0
    avg_loss = statistics.fmean(losses) if losses else 0.0

    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else float("inf")

    return {
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
    }


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


def analyze_trading_data(
    trades: List[Dict],
    initial_balance: float = 10000.0,
    risk_free_rate: float = 0.05,
) -> Dict:
    """Analyze trading data and calculate comprehensive performance metrics."""
    if not trades:
        return {}

    equity_curve = [initial_balance]
    returns = []

    for trade in trades:
        if trade.get("exit_price") is not None:
            if trade.get("direction") == 1:
                pnl = trade["exit_price"] - trade["entry_price"]
            else:
                pnl = trade["entry_price"] - trade["exit_price"]

            new_balance = equity_curve[-1] + pnl
            equity_curve.append(new_balance)

            return_pct = pnl / trade["entry_price"]
            returns.append(return_pct)

    total_return = (equity_curve[-1] / equity_curve[0] - 1) if equity_curve[0] != 0 else 0.0
    annualized_return = ((1 + total_return) ** (252 / len(returns)) - 1) if returns else 0.0

    sharpe = calculate_sharpe_ratio(returns, risk_free_rate, 252)
    drawdown_metrics = calculate_drawdown(equity_curve)
    trade_metrics = calculate_win_rate(trades)

    avg_trade_return = (
        statistics.fmean([t.get("pnl", 0) for t in trades if t.get("pnl") is not None])
        if trades
        else 0.0
    )

    metrics = {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "sharpe_ratio": sharpe,
        **drawdown_metrics,
        **trade_metrics,
        "num_trades": len(trades),
        "num_winning_trades": len(
            [
                t
                for t in trades
                if t.get("exit_price") is not None
                and (
                    (t.get("direction", 1) == 1 and t["exit_price"] > t["entry_price"])
                    or (t.get("direction", 1) == -1 and t["exit_price"] < t["entry_price"])
                )
            ]
        ),
        "num_losing_trades": len(
            [
                t
                for t in trades
                if t.get("exit_price") is not None
                and (
                    (t.get("direction", 1) == 1 and t["exit_price"] < t["entry_price"])
                    or (t.get("direction", 1) == -1 and t["exit_price"] > t["entry_price"])
                )
            ]
        ),
        "avg_trade_return": avg_trade_return,
    }

    return metrics


def backtest_symbol_sharpe_yfinance(
    symbol: str,
    days: int = 365,
    interval: str = "1d",
    risk_free_rate: float = 0.05,
) -> Dict:
    """Fetch symbol data from Yahoo Finance and compute Sharpe."""
    if days <= 0:
        raise ValueError("Days must be positive.")

    period = f"{days}d" if days < 3650 else "max"
    data = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
    if data.empty or "Close" not in data:
        raise ValueError(f"No {symbol} data returned from Yahoo Finance.")

    close_col = data["Close"]
    if isinstance(close_col, pd.DataFrame):
        close_series = close_col.iloc[:, 0]
    else:
        close_series = close_col

    closes = close_series.dropna().astype(float).tolist()

    if len(closes) < 2:
        raise ValueError("Insufficient closing prices for BTC-USD.")

    returns = []
    for prev, curr in zip(closes[:-1], closes[1:]):
        if prev != 0:
            returns.append((curr - prev) / prev)

    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=risk_free_rate, annualization_factor=252)
    total_return = (closes[-1] / closes[0]) - 1
    annualized_return = ((1 + total_return) ** (252 / len(returns)) - 1) if returns else 0.0

    return {
        "symbol": symbol,
        "period_days": min(days, len(closes)),
        "interval": interval,
        "total_return": total_return,
        "annualized_return": annualized_return,
        "sharpe_ratio": sharpe,
        "num_returns": len(returns),
    }


def main():
    """Main function to calculate Sharpe ratio from trading data."""
    parser = argparse.ArgumentParser(description="Calculate Sharpe ratio from Minah trading data")
    parser.add_argument("--file", "-f", help="JSON file with trading data")
    parser.add_argument("--risk-free-rate", "-r", type=float, default=0.05, help="Annual risk-free rate (default: 5%)")
    parser.add_argument("--initial-balance", "-b", type=float, default=10000.0, help="Initial balance (default: 10000)")
    parser.add_argument("--btc", action="store_true", help="Fetch last-year BTC-USD data from Yahoo Finance and compute Sharpe")
    parser.add_argument("--symbol", help="Fetch arbitrary symbol via yfinance (e.g., ETH-USD, ES=F)")
    parser.add_argument("--interval", default="1d", help="Data interval for yfinance (default: 1d)")
    parser.add_argument("--days", type=int, default=365, help="Days of history to fetch (default: 365)")

    args = parser.parse_args()
    
    # Symbol backtest mode (Yahoo Finance)
    if args.symbol or args.btc:
        target_symbol = args.symbol or "BTC-USD"
        label = target_symbol if not args.btc else "BTC-USD"

        print(f"Fetching {label} data from Yahoo Finance for last {args.days} days ...")
        metrics = backtest_symbol_sharpe_yfinance(
            symbol=label,
            days=args.days,
            interval=args.interval,
            risk_free_rate=args.risk_free_rate,
        )

        print("\n" + "="*60)
        print(f"  {label} BACKTEST (Yahoo Finance, {args.days}d @ {args.interval})")
        print("="*60)
        print(f"Total Return: {metrics['total_return']*100:.2f}%")
        print(f"Annualized Return: {metrics['annualized_return']*100:.2f}%")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Samples: {metrics['num_returns']}")
        print("="*60)

        safe_symbol = label.replace("/", "_").replace("=", "_")
        output_file = f"{safe_symbol.lower()}_backtest_metrics.json"
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        return

    # Sample data for demonstration
    sample_trades = [
        {
            "entry_time": "2024-01-01 10:00:00",
            "entry_price": 4500.0,
            "direction": 1,  # Long
            "confidence": 0.85,
            "exit_time": "2024-01-01 10:30:00",
            "exit_price": 4525.0,
            "pnl": 25.0,
            "return_pct": 0.0056,
            "exit_reason": "Confidence returned to neutral"
        },
        {
            "entry_time": "2024-01-01 11:00:00",
            "entry_price": 4520.0,
            "direction": -1,  # Short
            "confidence": 0.15,
            "exit_time": "2024-01-01 11:45:00",
            "exit_price": 4500.0,
            "pnl": 20.0,
            "return_pct": 0.0044,
            "exit_reason": "Confidence returned to neutral"
        },
        {
            "entry_time": "2024-01-01 12:00:00",
            "entry_price": 4505.0,
            "direction": 1,  # Long
            "confidence": 0.90,
            "exit_time": "2024-01-01 12:20:00",
            "exit_price": 4490.0,
            "pnl": -15.0,
            "return_pct": -0.0033,
            "exit_reason": "Confidence returned to neutral"
        }
    ]

    # Use sample data if no file provided
    if args.file:
        try:
            with open(args.file, 'r') as f:
                trades = json.load(f)
        except FileNotFoundError:
            print(f"Error: File {args.file} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file {args.file}")
            sys.exit(1)
    else:
        trades = sample_trades
        print("Using sample trading data (use --file to specify your own data)")

    # Calculate metrics
    metrics = analyze_trading_data(trades, args.initial_balance, args.risk_free_rate)

    # Display results
    print("\n" + "="*60)
    print("  MINAH TRADING PERFORMANCE METRICS")
    print("="*60)
    print(format_metrics(metrics))
    print("="*60)

    # Save results to file
    output_file = "minah_performance_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
