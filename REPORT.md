# Trading Performance Report

## Overview
We evaluated the three Brainnet strategies over the past year using daily bars from Yahoo Finance:

- **Minah** tracking BTC-USD  
- **Carter** tracking ETH-USD  
- **Banis** tracking ES=F (S&P 500 E-mini futures)

Each backtest produced standardized metrics saved as JSON artifacts for reproducibility: `btc_backtest_metrics.json`, `eth-usd_backtest_metrics.json`, and `es_f_backtest_metrics.json`.

## Data & Methodology
1. **Data source** – `yfinance` daily candles (`interval=1d`, `days=365` for crypto, 301 trading days for ES=F).  
2. **Returns** – Simple log approximation via `pct_change`.  
3. **Sharpe Ratio** – Annualized using 252 trading days and a 5% risk-free rate assumption.  
4. **Outputs** – Stored via `lms/minah/calculate_sharpe.py` to ensure identical calculations across strategies.  
5. **Files** – `btc_backtest_metrics.json`, `eth-usd_backtest_metrics.json`, `es_f_backtest_metrics.json`.

## Key Metrics
| Strategy | Symbol | Period (days) | Total Return | Annualized Return | Sharpe Ratio | Samples |
| --- | --- | --- | --- | --- | --- | --- |
| Minah | BTC-USD | 365 | -9.72% | -6.84% | -0.16 | 364 |
| Carter | ETH-USD | 365 | -17.48% | -12.45% | 0.02 | 364 |
| Banis | ES=F | 301 | 18.88% | 15.64% | 0.61 | 300 |

Sources: @btc_backtest_metrics.json#1-9, @eth-usd_backtest_metrics.json#1-9, @es_f_backtest_metrics.json#1-9.

## Observations
1. **Risk-adjusted leadership** – Banis (ES futures) delivered the only materially positive Sharpe (0.61).  
2. **Crypto headwinds** – Carter and Minah both faced negative total returns; Carter’s Sharpe hovered near zero while Minah’s dipped negative due to volatility without compensating upside.  
3. **Volatility profile** – Crypto samples (364) captured nearly full-year data, whereas ES=F (300) reflects trading days; all sample counts remain sufficient for Sharpe stability.  
4. **Next steps** –  
   - Increase holding-period diversity (e.g., 4h or 1h bars) for Carter/Minah.  
   - Evaluate hedging overlays or dynamic sizing to lift crypto Sharpe.  
   - Add rolling Sharpe visualization to spot regime changes faster.

## Reproduction
```bash
# Generic symbol backtest (example: ETH-USD)
python3 lms/minah/calculate_sharpe.py --symbol ETH-USD --days 365 --interval 1d

# BTC shorthand
python3 lms/minah/calculate_sharpe.py --btc --days 365
```

Results will be written to `<symbol>_backtest_metrics.json`, enabling diff-friendly audits and historical comparisons.
