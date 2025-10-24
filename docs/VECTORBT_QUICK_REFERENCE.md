# VectorBT Portfolio - Quick Reference

## Most Commonly Used Methods

### Performance Metrics

```python
portfolio.total_return()      # float: Total return (0.25 = 25%)
portfolio.total_profit()      # float: Total profit in $
portfolio.final_value()       # float: Final portfolio value
portfolio.sharpe_ratio()      # float: Risk-adjusted return
portfolio.sortino_ratio()     # float: Downside risk-adjusted
portfolio.calmar_ratio()      # float: Return / max drawdown
portfolio.max_drawdown()      # float: Max drawdown (0.15 = 15%)
```

### Trade Statistics

```python
portfolio.trades.count()                    # int: Total trades
portfolio.trades.win_rate()                 # float: Win rate (0.65 = 65%)
portfolio.trades.winning.count()            # int: Winning trades
portfolio.trades.losing.count()             # int: Losing trades
portfolio.trades.winning.pnl.mean()        # float: Avg winning trade
portfolio.trades.losing.pnl.mean()         # float: Avg losing trade
portfolio.trades.records_readable           # DataFrame: Trade history
```

### Time Series Data

```python
portfolio.value()             # Series: Portfolio value over time
portfolio.drawdown()          # Series: Drawdown over time
portfolio.returns()           # Series: Returns over time
portfolio.cash()              # Series: Cash over time
portfolio.assets()            # Series: Asset holdings over time
```

### Common Patterns

#### Check if trades exist

```python
if portfolio.trades.count() > 0:
    win_rate = portfolio.trades.win_rate()
```

#### Safe average calculation

```python
avg_win = (portfolio.trades.winning.pnl.mean() 
           if portfolio.trades.winning.count() > 0 else 0)
```

#### Display in Streamlit

```python
st.metric("Total Return", f"{portfolio.total_return() * 100:.2f}%")
st.metric("Sharpe Ratio", f"{portfolio.sharpe_ratio():.2f}")
st.metric("Max Drawdown", f"{portfolio.max_drawdown() * 100:.2f}%")
```

## Creating a Portfolio

```python
import vectorbt as vbt

portfolio = vbt.Portfolio.from_signals(
    close=close_prices.values,      # Price array
    entries=entries.values,         # Buy signals (boolean)
    exits=exits.values,             # Sell signals (boolean)
    init_cash=10000.0,             # Starting capital
    fees=0.001,                    # 0.1% fees
    freq="1D",                     # Daily frequency
)
```

## Type Hints

```python
from typing import Any

def backtest(portfolio: Any) -> None:
    """Use Any type for vectorbt Portfolio objects."""
    pass
```

For full API reference, see: `docs/VECTORBT_PORTFOLIO_API.md`
