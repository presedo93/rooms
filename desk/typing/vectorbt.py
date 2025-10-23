"""Protocol definitions for vectorbt library.

VectorBT uses dynamic attribute generation which makes LSP type checking difficult.
These Protocol classes define the interface for vectorbt's Portfolio, Trades, and
related objects to enable autocomplete and type checking.

Usage:
    from desk.typing import PortfolioProtocol

    def analyze_backtest(portfolio: PortfolioProtocol) -> dict:
        return {
            "total_return": portfolio.total_return(),
            "sharpe": portfolio.sharpe_ratio(),
        }
"""

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class ExitTradesProtocol(Protocol):
    """Protocol for vectorbt ExitTrades objects (winning/losing trades).

    This is the type of portfolio.trades.winning and portfolio.trades.losing.
    """

    def count(self) -> int:
        """Return number of trades."""
        ...

    @property
    def pnl(self) -> pd.Series:
        """Return Series of profit/loss values for each trade."""
        ...

    @property
    def returns(self) -> pd.Series:
        """Return Series of return values for each trade."""
        ...

    @property
    def duration(self) -> pd.Series:
        """Return Series of trade durations."""
        ...

    @property
    def entry_price(self) -> pd.Series:
        """Return Series of entry prices."""
        ...

    @property
    def exit_price(self) -> pd.Series:
        """Return Series of exit prices."""
        ...


@runtime_checkable
class TradesProtocol(Protocol):
    """Protocol for vectorbt Trades object.

    This is the type of portfolio.trades.
    """

    def count(self) -> int:
        """Return total number of trades."""
        ...

    def win_rate(self) -> float:
        """Return win rate as decimal (e.g., 0.65 = 65%)."""
        ...

    def avg_duration(self) -> Any:
        """Return average trade duration."""
        ...

    def expectancy(self) -> float:
        """Return expected profit per trade."""
        ...

    def coverage(self) -> float:
        """Return fraction of time in market."""
        ...

    @property
    def records_readable(self) -> pd.DataFrame:
        """Return human-readable DataFrame of all trades.

        Columns typically include:
        - Entry Date
        - Exit Date
        - PnL
        - Return
        - Duration
        - Entry Price
        - Exit Price
        - Entry Fees
        - Exit Fees
        """
        ...

    @property
    def winning(self) -> ExitTradesProtocol:
        """Return ExitTrades object containing only winning trades."""
        ...

    @property
    def losing(self) -> ExitTradesProtocol:
        """Return ExitTrades object containing only losing trades."""
        ...

    @property
    def closed(self) -> ExitTradesProtocol:
        """Return ExitTrades object containing only closed trades."""
        ...

    @property
    def pnl(self) -> pd.Series:
        """Return Series of profit/loss for all trades."""
        ...

    @property
    def returns(self) -> pd.Series:
        """Return Series of returns for all trades."""
        ...

    @property
    def duration(self) -> pd.Series:
        """Return Series of durations for all trades."""
        ...

    @property
    def entry_price(self) -> pd.Series:
        """Return Series of entry prices."""
        ...

    @property
    def exit_price(self) -> pd.Series:
        """Return Series of exit prices."""
        ...

    @property
    def entry_fees(self) -> pd.Series:
        """Return Series of entry fees paid."""
        ...

    @property
    def exit_fees(self) -> pd.Series:
        """Return Series of exit fees paid."""
        ...

    @property
    def direction(self) -> pd.Series:
        """Return Series of trade directions (long/short)."""
        ...


@runtime_checkable
class OrdersProtocol(Protocol):
    """Protocol for vectorbt Orders object.

    This is the type of portfolio.orders.
    """

    def count(self) -> int:
        """Return total number of orders."""
        ...

    @property
    def records_readable(self) -> pd.DataFrame:
        """Return human-readable DataFrame of all orders."""
        ...

    @property
    def size(self) -> pd.Series:
        """Return Series of order sizes."""
        ...

    @property
    def price(self) -> pd.Series:
        """Return Series of order prices."""
        ...

    @property
    def fees(self) -> pd.Series:
        """Return Series of fees paid."""
        ...

    @property
    def direction(self) -> pd.Series:
        """Return Series of order directions."""
        ...


@runtime_checkable
class PositionsProtocol(Protocol):
    """Protocol for vectorbt Positions object.

    This is the type of portfolio.positions.
    """

    def count(self) -> int:
        """Return total number of positions."""
        ...

    @property
    def records_readable(self) -> pd.DataFrame:
        """Return human-readable DataFrame of all positions."""
        ...

    @property
    def pnl(self) -> pd.Series:
        """Return Series of profit/loss per position."""
        ...

    @property
    def returns(self) -> pd.Series:
        """Return Series of returns per position."""
        ...

    @property
    def duration(self) -> pd.Series:
        """Return Series of position durations."""
        ...


@runtime_checkable
class DrawdownsProtocol(Protocol):
    """Protocol for vectorbt Drawdowns object.

    This is the type of portfolio.drawdowns.
    """

    def count(self) -> int:
        """Return total number of drawdown periods."""
        ...

    @property
    def records_readable(self) -> pd.DataFrame:
        """Return human-readable DataFrame of drawdown periods."""
        ...

    @property
    def max_drawdown(self) -> float:
        """Return maximum drawdown as decimal."""
        ...

    @property
    def avg_drawdown(self) -> float:
        """Return average drawdown."""
        ...

    @property
    def duration(self) -> pd.Series:
        """Return Series of drawdown durations."""
        ...


@runtime_checkable
class PortfolioProtocol(Protocol):
    """Protocol for vectorbt Portfolio object.

    This Protocol defines the interface for vectorbt's Portfolio class,
    enabling LSP autocomplete and type checking.

    Example:
        >>> def backtest(portfolio: PortfolioProtocol) -> None:
        ...     # LSP will now autocomplete these methods
        ...     total_return = portfolio.total_return()
        ...     sharpe = portfolio.sharpe_ratio()
        ...     win_rate = portfolio.trades.win_rate()
    """

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def trades(self) -> TradesProtocol:
        """Return Trades accessor object."""
        ...

    @property
    def orders(self) -> OrdersProtocol:
        """Return Orders accessor object."""
        ...

    @property
    def positions(self) -> PositionsProtocol:
        """Return Positions accessor object."""
        ...

    @property
    def drawdowns(self) -> DrawdownsProtocol:
        """Return Drawdowns accessor object."""
        ...

    @property
    def close(self) -> pd.Series | pd.DataFrame:
        """Return close prices used in the portfolio."""
        ...

    @property
    def init_cash(self) -> float:
        """Return initial cash amount."""
        ...

    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================

    def total_return(self, **kwargs) -> float:
        """Return total portfolio return as decimal (e.g., 0.25 = 25%)."""
        ...

    def total_profit(self, **kwargs) -> float:
        """Return total profit in currency units."""
        ...

    def final_value(self, **kwargs) -> float:
        """Return final portfolio value."""
        ...

    def annualized_return(self, **kwargs) -> float:
        """Return annualized return."""
        ...

    def cumulative_returns(self, **kwargs) -> pd.Series:
        """Return Series of cumulative returns over time."""
        ...

    def annual_returns(self, **kwargs) -> pd.Series:
        """Return Series of returns per year."""
        ...

    def daily_returns(self, **kwargs) -> pd.Series:
        """Return Series of daily returns."""
        ...

    def returns(self, **kwargs) -> pd.Series:
        """Return Series of portfolio returns."""
        ...

    # ========================================================================
    # RISK METRICS
    # ========================================================================

    def sharpe_ratio(self, **kwargs) -> float:
        """Return Sharpe ratio (risk-adjusted return)."""
        ...

    def sortino_ratio(self, **kwargs) -> float:
        """Return Sortino ratio (downside risk-adjusted return)."""
        ...

    def calmar_ratio(self, **kwargs) -> float:
        """Return Calmar ratio (return / max drawdown)."""
        ...

    def max_drawdown(self, **kwargs) -> float:
        """Return maximum drawdown as decimal (e.g., 0.15 = 15%)."""
        ...

    def omega_ratio(self, **kwargs) -> float:
        """Return Omega ratio."""
        ...

    def tail_ratio(self, **kwargs) -> float:
        """Return tail ratio."""
        ...

    def value_at_risk(self, **kwargs) -> float:
        """Return Value at Risk (VaR)."""
        ...

    def cond_value_at_risk(self, **kwargs) -> float:
        """Return Conditional Value at Risk (CVaR)."""
        ...

    def deflated_sharpe_ratio(self, **kwargs) -> float:
        """Return deflated Sharpe ratio."""
        ...

    def annualized_volatility(self, **kwargs) -> float:
        """Return annualized volatility."""
        ...

    def downside_risk(self, **kwargs) -> float:
        """Return downside deviation."""
        ...

    # ========================================================================
    # BENCHMARK COMPARISON
    # ========================================================================

    def alpha(self, **kwargs) -> float:
        """Return alpha versus benchmark."""
        ...

    def beta(self, **kwargs) -> float:
        """Return beta versus benchmark."""
        ...

    def information_ratio(self, **kwargs) -> float:
        """Return information ratio."""
        ...

    def capture(self, **kwargs) -> float:
        """Return up/down capture ratio."""
        ...

    def up_capture(self, **kwargs) -> float:
        """Return upside capture."""
        ...

    def down_capture(self, **kwargs) -> float:
        """Return downside capture."""
        ...

    # ========================================================================
    # TIME SERIES DATA
    # ========================================================================

    def value(self, **kwargs) -> pd.Series:
        """Return Series of portfolio value over time."""
        ...

    def drawdown(self, **kwargs) -> pd.Series:
        """Return Series of drawdown over time."""
        ...

    def cash(self, **kwargs) -> pd.Series:
        """Return Series of cash over time."""
        ...

    def assets(self, **kwargs) -> pd.Series:
        """Return Series of asset holdings over time."""
        ...

    def asset_value(self, **kwargs) -> pd.Series:
        """Return Series of asset value over time."""
        ...

    def asset_flow(self, **kwargs) -> pd.Series:
        """Return Series of asset flow (buys/sells) over time."""
        ...

    def cash_flow(self, **kwargs) -> pd.Series:
        """Return Series of cash flow over time."""
        ...

    def gross_exposure(self, **kwargs) -> pd.Series:
        """Return Series of gross exposure over time."""
        ...

    def net_exposure(self, **kwargs) -> pd.Series:
        """Return Series of net exposure over time."""
        ...

    # ========================================================================
    # PLOTTING METHODS
    # ========================================================================

    def plot(self, **kwargs) -> Any:
        """Return main portfolio plot."""
        ...

    def plot_value(self, **kwargs) -> Any:
        """Return plot of portfolio value over time."""
        ...

    def plot_cum_returns(self, **kwargs) -> Any:
        """Return plot of cumulative returns."""
        ...

    def plot_drawdowns(self, **kwargs) -> Any:
        """Return plot of drawdown analysis."""
        ...

    def plot_underwater(self, **kwargs) -> Any:
        """Return underwater (drawdown) plot."""
        ...

    def plot_assets(self, **kwargs) -> Any:
        """Return plot of asset holdings."""
        ...

    def plot_asset_value(self, **kwargs) -> Any:
        """Return plot of asset value."""
        ...

    def plot_asset_flow(self, **kwargs) -> Any:
        """Return plot of asset flow."""
        ...

    def plot_cash(self, **kwargs) -> Any:
        """Return plot of cash over time."""
        ...

    def plot_cash_flow(self, **kwargs) -> Any:
        """Return plot of cash flow."""
        ...

    def plot_gross_exposure(self, **kwargs) -> Any:
        """Return plot of gross exposure."""
        ...

    def plot_net_exposure(self, **kwargs) -> Any:
        """Return plot of net exposure."""
        ...

    def plot_trades(self, **kwargs) -> Any:
        """Return plot of all trades."""
        ...

    def plot_trade_pnl(self, **kwargs) -> Any:
        """Return plot of trade P&L."""
        ...

    def plot_orders(self, **kwargs) -> Any:
        """Return plot of orders."""
        ...

    def plot_positions(self, **kwargs) -> Any:
        """Return plot of positions."""
        ...

    def plot_position_pnl(self, **kwargs) -> Any:
        """Return plot of position P&L."""
        ...

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def stats(self, **kwargs) -> pd.Series:
        """Return Series of portfolio statistics."""
        ...

    def get_trades(self, **kwargs) -> TradesProtocol:
        """Return Trades accessor object."""
        ...

    def get_orders(self, **kwargs) -> OrdersProtocol:
        """Return Orders accessor object."""
        ...

    def get_positions(self, **kwargs) -> PositionsProtocol:
        """Return Positions accessor object."""
        ...

    def get_drawdowns(self, **kwargs) -> DrawdownsProtocol:
        """Return Drawdowns accessor object."""
        ...
