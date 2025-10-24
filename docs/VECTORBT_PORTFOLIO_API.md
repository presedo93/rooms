# VectorBT Portfolio API Reference

This document provides a comprehensive reference for the
`vectorbt.portfolio.base.Portfolio` class methods and properties.

## Table of Contents

- [Creating a Portfolio](#creating-a-portfolio)
- [Statistics & Metrics Methods](#statistics--metrics-methods)
- [Plotting Methods](#plotting-methods)
- [Data Access Methods](#data-access-methods)
- [Portfolio Properties](#portfolio-properties)
- [Trades Object](#trades-object)
- [Orders Object](#orders-object)
- [Positions Object](#positions-object)

______________________________________________________________________

## Creating a Portfolio

### Factory Methods

#### `Portfolio.from_signals()`

Create portfolio from entry/exit signals.

**Key Parameters:**

- `close`: Price data (array, Series, or DataFrame)
- `entries`: Boolean array/Series indicating buy signals
- `exits`: Boolean array/Series indicating sell signals
- `init_cash`: Initial capital (default: 100)
- `fees`: Trading fees as decimal (e.g., 0.001 for 0.1%)
- `freq`: Frequency for annualization (e.g., '1D', '1H')

**Example:**

```python
portfolio = vbt.Portfolio.from_signals(
    close=close_prices.values,
    entries=entries.values,
    exits=exits.values,
    init_cash=10000.0,
    fees=0.001,  # 0.1%
    freq="1D",
)
```

#### `Portfolio.from_orders()`

Create portfolio from order size/direction data.

#### `Portfolio.from_holding()`

Create buy-and-hold portfolio for benchmarking.

#### `Portfolio.from_order_func()`

Create portfolio using custom order function (advanced).

______________________________________________________________________

## Statistics & Metrics Methods

### Returns & Performance

| Method | Returns | Description |
|--------|---------|-------------|
| `total_return()` | float | Total portfolio return as decimal (0.25 = 25%) |
| `annualized_return()` | float | Annualized return |
| `total_profit()` | float | Total profit in currency units |
| `final_value()` | float | Final portfolio value |
| `cumulative_returns()` | Series | Cumulative returns over time |
| `annual_returns()` | Series | Returns per year |
| `daily_returns()` | Series | Daily returns |
| `returns()` | Series | Portfolio returns |

**Example:**

```python
total_return = portfolio.total_return()  # 0.234 (23.4%)
final_value = portfolio.final_value()    # 12340.50
```

### Risk Metrics

| Method | Returns | Description |
|--------|---------|-------------|
| `sharpe_ratio()` | float | Sharpe ratio (risk-adjusted return) |
| `sortino_ratio()` | float | Sortino ratio (downside risk-adjusted) |
| `calmar_ratio()` | float | Calmar ratio (return / max drawdown) |
| `max_drawdown()` | float | Maximum drawdown as decimal |
| `omega_ratio()` | float | Omega ratio |
| `tail_ratio()` | float | Tail ratio |
| `value_at_risk()` | float | Value at Risk (VaR) |
| `cond_value_at_risk()` | float | Conditional VaR (CVaR) |
| `deflated_sharpe_ratio()` | float | Deflated Sharpe ratio |
| `annualized_volatility()` | float | Annualized volatility |
| `downside_risk()` | float | Downside deviation |

**Example:**

```python
sharpe = portfolio.sharpe_ratio()       # 1.45
max_dd = portfolio.max_drawdown()       # 0.15 (15%)
sortino = portfolio.sortino_ratio()     # 2.1
```

### Benchmark Comparison

| Method | Returns | Description |
|--------|---------|-------------|
| `alpha()` | float | Alpha vs benchmark |
| `beta()` | float | Beta vs benchmark |
| `information_ratio()` | float | Information ratio |
| `capture()` | float | Up/down capture ratio |
| `up_capture()` | float | Upside capture |
| `down_capture()` | float | Downside capture |

______________________________________________________________________

## Plotting Methods

All plotting methods return plotly Figure objects.

| Method | Description |
|--------|-------------|
| `plot()` | Main portfolio plot |
| `plot_value()` | Plot portfolio value over time |
| `plot_cum_returns()` | Plot cumulative returns |
| `plot_drawdowns()` | Plot drawdown analysis |
| `plot_underwater()` | Underwater (drawdown) plot |
| `plot_assets()` | Plot asset holdings |
| `plot_asset_value()` | Plot asset value |
| `plot_asset_flow()` | Plot asset flow |
| `plot_cash()` | Plot cash over time |
| `plot_cash_flow()` | Plot cash flow |
| `plot_gross_exposure()` | Plot gross exposure |
| `plot_net_exposure()` | Plot net exposure |
| `plot_trades()` | Plot all trades |
| `plot_trade_pnl()` | Plot trade P&L |
| `plot_orders()` | Plot orders |
| `plot_positions()` | Plot positions |
| `plot_position_pnl()` | Plot position P&L |

**Example:**

```python
# These return plotly figures - display in Streamlit or Jupyter
fig = portfolio.plot_value()
st.plotly_chart(fig)
```

______________________________________________________________________

## Data Access Methods

### Time Series Data

| Method | Returns | Description |
|--------|---------|-------------|
| `value()` | Series | Portfolio value over time |
| `drawdown()` | Series | Drawdown series |
| `cash()` | Series | Cash over time |
| `assets()` | Series | Asset holdings over time |
| `asset_value()` | Series | Value of assets over time |
| `asset_flow()` | Series | Asset flow (buys/sells) |
| `cash_flow()` | Series | Cash flow |
| `gross_exposure()` | Series | Gross exposure over time |
| `net_exposure()` | Series | Net exposure over time |

**Example:**

```python
equity_curve = portfolio.value()  # Series of portfolio value
drawdowns = portfolio.drawdown()  # Series of drawdown values
```

### Records & Trade Data

| Method | Returns | Description |
|--------|---------|-------------|
| `get_trades()` | Trades | Get trades accessor object |
| `get_orders()` | Orders | Get orders accessor object |
| `get_positions()` | Positions | Get positions accessor object |
| `get_drawdowns()` | Drawdowns | Get drawdowns accessor object |
| `get_logs()` | Logs | Get simulation logs |

______________________________________________________________________

## Portfolio Properties

Properties are accessed without parentheses (e.g., `portfolio.trades`).

| Property | Type | Description |
|----------|------|-------------|
| `trades` | Trades | Trades accessor object |
| `orders` | Orders | Orders accessor object |
| `positions` | Positions | Positions accessor object |
| `drawdowns` | Drawdowns | Drawdowns accessor object |
| `logs` | Logs | Simulation logs |
| `close` | Series/DataFrame | Close prices used |
| `init_cash` | float | Initial cash |
| `cash_sharing` | bool | Whether cash is shared |
| `call_seq` | array | Call sequence |
| `wrapper` | Wrapper | Array wrapper |
| `config` | dict | Portfolio configuration |

______________________________________________________________________

## Trades Object

Access via `portfolio.trades`. This object contains information about all
executed trades.

### Trades Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `count()` | int | Total number of trades |
| `win_rate()` | float | Win rate as decimal (e.g., 0.65 = 65%) |
| `avg_duration()` | timedelta | Average trade duration |
| `expectancy()` | float | Expected profit per trade |
| `coverage()` | float | Time in market |

### Trades Properties

| Property | Type | Description |
|----------|------|-------------|
| `records_readable` | DataFrame | Human-readable trades table |
| `winning` | ExitTrades | Winning trades only |
| `losing` | ExitTrades | Losing trades only |
| `closed` | ExitTrades | Closed trades |
| `pnl` | Series | Profit/loss per trade |
| `returns` | Series | Return per trade |
| `duration` | Series | Duration per trade |
| `entry_price` | Series | Entry prices |
| `exit_price` | Series | Exit prices |
| `entry_fees` | Series | Entry fees paid |
| `exit_fees` | Series | Exit fees paid |
| `direction` | Series | Trade direction (long/short) |

### Sub-Objects (Winning/Losing Trades)

Both `portfolio.trades.winning` and `portfolio.trades.losing` are `ExitTrades`
objects with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `count()` | int | Number of trades |
| `pnl` | Series | P&L for these trades |
| `pnl.mean()` | float | Average P&L |
| `pnl.sum()` | float | Total P&L |
| `pnl.std()` | float | P&L standard deviation |
| All other trades properties | - | Same as parent trades object |

### Usage Examples

```python
# Basic stats
total_trades = portfolio.trades.count()         # 150
win_rate = portfolio.trades.win_rate()          # 0.65 (65%)

# Winning trades
num_winners = portfolio.trades.winning.count()  # 97
avg_win = portfolio.trades.winning.pnl.mean()   # 45.32

# Losing trades
num_losers = portfolio.trades.losing.count()    # 53
avg_loss = portfolio.trades.losing.pnl.mean()   # -23.15

# Trades table
trades_df = portfolio.trades.records_readable
# DataFrame with columns: Entry Date, Exit Date, PnL, Return, Duration, etc.

# Check if trades exist before accessing
if portfolio.trades.count() > 0:
    if portfolio.trades.winning.count() > 0:
        avg_win = portfolio.trades.winning.pnl.mean()
```

______________________________________________________________________

## Orders Object

Access via `portfolio.orders`.

### Orders Properties

| Property | Type | Description |
|----------|------|-------------|
| `records_readable` | DataFrame | Human-readable orders table |
| `count()` | int | Total number of orders |
| `size` | Series | Order sizes |
| `price` | Series | Order prices |
| `fees` | Series | Fees paid |
| `direction` | Series | Order direction |

______________________________________________________________________

## Positions Object

Access via `portfolio.positions`.

### Positions Properties

| Property | Type | Description |
|----------|------|-------------|
| `records_readable` | DataFrame | Human-readable positions table |
| `count()` | int | Total number of positions |
| `pnl` | Series | P&L per position |
| `returns` | Series | Return per position |
| `duration` | Series | Duration per position |

______________________________________________________________________

## Common Patterns

### 1. Display Key Metrics in Streamlit

```python
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_return = portfolio.total_return() * 100
    st.metric("Total Return", f"{total_return:.2f}%")

with col2:
    sharpe = portfolio.sharpe_ratio()
    st.metric("Sharpe Ratio", f"{sharpe:.2f}")

with col3:
    max_dd = portfolio.max_drawdown() * 100
    st.metric("Max Drawdown", f"{max_dd:.2f}%")

with col4:
    win_rate = portfolio.trades.win_rate() * 100
    st.metric("Win Rate", f"{win_rate:.2f}%")
```

### 2. Plot Equity Curve

```python
# Get equity curve
equity = portfolio.value()

# Plot with plotly
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=equity.index,
    y=equity.values,
    mode='lines',
    name='Portfolio Value'
))
st.plotly_chart(fig)
```

### 3. Safe Trade Access Pattern

```python
# Always check if trades exist
trades_count = portfolio.trades.count()

if trades_count > 0:
    # Access trade statistics
    win_count = portfolio.trades.winning.count()
    loss_count = portfolio.trades.losing.count()
    
    # Safe average calculation
    avg_win = (portfolio.trades.winning.pnl.mean() 
               if win_count > 0 else 0)
    avg_loss = (portfolio.trades.losing.pnl.mean() 
                if loss_count > 0 else 0)
else:
    st.warning("No trades executed")
```

### 4. Benchmark Comparison

```python
# Create buy-and-hold portfolio
buy_hold = vbt.Portfolio.from_holding(
    close=close_prices,
    init_cash=10000
)

# Compare
strategy_return = portfolio.total_return() * 100
benchmark_return = buy_hold.total_return() * 100
outperformance = strategy_return - benchmark_return

st.metric(
    "Outperformance vs Buy & Hold",
    f"{outperformance:.2f}%",
    delta=f"{outperformance:.2f}%"
)
```

______________________________________________________________________

## Type Hints

Due to vectorbt's dynamic nature, use `Any` for type hints:

```python
from typing import Any

def analyze_portfolio(portfolio: Any) -> dict:
    """Analyze vectorbt portfolio.
    
    Args:
        portfolio: vectorbt Portfolio object (typed as Any due to dynamic attrs)
    
    Returns:
        Dictionary of metrics
    """
    return {
        "total_return": portfolio.total_return(),
        "sharpe_ratio": portfolio.sharpe_ratio(),
        "max_drawdown": portfolio.max_drawdown(),
        "win_rate": portfolio.trades.win_rate(),
    }
```

______________________________________________________________________

## Additional Resources

- Official vectorbt docs: <https://vectorbt.pro/>
- Portfolio class source: `vectorbt.portfolio.base.Portfolio`
- All metrics accept optional `group_by` parameter for multi-column analysis
- Most methods return pandas Series/DataFrame or scalar values
- Use `help(portfolio.method_name)` in Python for detailed docs

______________________________________________________________________

## Notes

1. **Return Values**: Most metrics return scalars for single-column portfolios
   and Series for multi-column portfolios
1. **Frequency**: Set `freq` parameter in `from_signals()` for correct annualization
1. **Fees**: Fees are applied as decimals (0.001 = 0.1%)
1. **NaN Handling**: Methods handle NaN values automatically
1. **Performance**: vectorbt is optimized with NumPy/Numba for fast calculations
1. **Chaining**: Most accessors support method chaining (e.g., `portfolio.trades.winning.pnl.mean()`)
