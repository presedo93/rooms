"""Plotting utilities for backtesting strategies.

This module provides reusable charting functions for visualizing
backtesting results including equity curves, drawdowns, and price signals.
"""

import pandas as pd
import plotly.graph_objects as go

from desk.typing.vectorbt import PortfolioProtocol


def plot_equity_curve(
    portfolio_value: pd.Series,
    benchmark_value: pd.Series | None = None,
    *,
    strategy_name: str = "Strategy",
    benchmark_name: str = "Benchmark",
    title: str = "Portfolio Value Over Time",
    height: int = 400,
) -> go.Figure:
    """Create equity curve visualization comparing strategy vs benchmark.

    Args:
        portfolio_value: Series of portfolio values over time
        benchmark_value: Optional series of benchmark values (e.g., buy & hold)
        strategy_name: Name for the strategy line
        benchmark_name: Name for the benchmark line
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Strategy equity
    fig.add_trace(
        go.Scatter(
            x=portfolio_value.index,
            y=portfolio_value.values,
            name=strategy_name,
            line=dict(color="#00CC96", width=2),
        )
    )

    # Benchmark (if provided)
    if benchmark_value is not None:
        fig.add_trace(
            go.Scatter(
                x=benchmark_value.index,
                y=benchmark_value.values,
                name=benchmark_name,
                line=dict(color="#636EFA", width=2, dash="dash"),
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified",
        template="plotly_white",
        height=height,
    )

    return fig


def plot_drawdown(
    drawdown: pd.Series,
    *,
    as_percentage: bool = True,
    title: str = "Drawdown Over Time",
    height: int = 300,
) -> go.Figure:
    """Create drawdown visualization.

    Args:
        drawdown: Series of drawdown values
        as_percentage: Whether to display as percentage (multiply by 100)
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    drawdown_display = drawdown * 100 if as_percentage else drawdown
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=drawdown_display.index,
            y=drawdown_display.values,
            name="Drawdown",
            fill="tozeroy",
            line=dict(color="#EF553B", width=1),
        )
    )

    yaxis_title = "Drawdown (%)" if as_percentage else "Drawdown"
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        template="plotly_white",
        height=height,
    )

    return fig


def plot_price_with_signals(
    price: pd.Series,
    entries: pd.Series | None = None,
    exits: pd.Series | None = None,
    indicators: dict[str, pd.Series] | None = None,
    *,
    price_name: str = "Price",
    entry_name: str = "Buy Signal",
    exit_name: str = "Sell Signal",
    title: str = "Price Chart with Signals",
    height: int = 500,
) -> go.Figure:
    """Create price chart with trade signals and optional indicators.

    Args:
        price: Series of prices (typically close prices)
        entries: Boolean series indicating entry signals
        exits: Boolean series indicating exit signals
        indicators: Optional dict of indicator name -> series to plot
        price_name: Label for the price line
        entry_name: Label for entry signals
        exit_name: Label for exit signals
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Price line
    fig.add_trace(
        go.Scatter(
            x=price.index,
            y=price.values,
            name=price_name,
            line=dict(color="#636EFA", width=1),
        )
    )

    # Optional indicators (e.g., moving averages, bands, etc.)
    if indicators:
        colors = ["#00CC96", "#EF553B", "#AB63FA", "#FFA15A", "#19D3F3"]
        for idx, (name, indicator) in enumerate(indicators.items()):
            color = colors[idx % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=indicator.index,
                    y=indicator.values,
                    name=name,
                    line=dict(color=color, width=1.5),
                )
            )

    # Entry signals
    if entries is not None:
        entry_points: pd.Series = price[entries]  # type: ignore[assignment]
        if len(entry_points) > 0:
            fig.add_trace(
                go.Scatter(
                    x=entry_points.index,
                    y=entry_points.values,
                    mode="markers",
                    name=entry_name,
                    marker=dict(color="green", size=10, symbol="triangle-up"),
                )
            )

    # Exit signals
    if exits is not None:
        exit_points: pd.Series = price[exits]  # type: ignore[assignment]
        if len(exit_points) > 0:
            fig.add_trace(
                go.Scatter(
                    x=exit_points.index,
                    y=exit_points.values,
                    mode="markers",
                    name=exit_name,
                    marker=dict(color="red", size=10, symbol="triangle-down"),
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
        template="plotly_white",
        height=height,
    )

    return fig


def plot_portfolio_equity_from_vectorbt(
    portfolio: PortfolioProtocol,
    close_prices: pd.Series,
    *,
    strategy_name: str = "Strategy",
    title: str = "Portfolio Value Over Time",
    height: int = 400,
) -> go.Figure:
    """Create equity curve from vectorbt Portfolio object.

    Convenience wrapper around plot_equity_curve for vectorbt portfolios.

    Args:
        portfolio: vectorbt Portfolio object
        close_prices: Series of close prices for buy & hold benchmark
        strategy_name: Name for the strategy
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    equity = portfolio.value()
    buy_hold_value = (close_prices / close_prices.iloc[0]) * portfolio.init_cash

    return plot_equity_curve(
        portfolio_value=equity,
        benchmark_value=buy_hold_value,
        strategy_name=strategy_name,
        benchmark_name="Buy & Hold",
        title=title,
        height=height,
    )


def plot_drawdown_from_vectorbt(
    portfolio: PortfolioProtocol,
    *,
    title: str = "Drawdown Over Time",
    height: int = 300,
) -> go.Figure:
    """Create drawdown chart from vectorbt Portfolio object.

    Convenience wrapper around plot_drawdown for vectorbt portfolios.

    Args:
        portfolio: vectorbt Portfolio object
        title: Chart title
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    drawdown = portfolio.drawdown()
    return plot_drawdown(
        drawdown=drawdown,
        as_percentage=True,
        title=title,
        height=height,
    )
