"""Backtest metrics display utilities.

This module provides generic functions for displaying backtest performance metrics
in a consistent format across different strategies.
"""

import pandas as pd
import streamlit as st


def display_backtest_metrics(
    portfolio,
    close_prices: pd.Series,
    strategy_name: str = "Strategy",
) -> None:
    """Display comprehensive backtest performance metrics.

    This function creates a consistent layout for displaying backtest results including:
    - Top-level performance metrics (Total Return, Sharpe, Max Drawdown, Win Rate)
    - Detailed statistics (Portfolio Stats, Trade Analysis, Risk Metrics)
    - Strategy vs Buy & Hold comparison

    Args:
        portfolio: vectorbt Portfolio object with backtest results
        close_prices: Series of close prices used in the backtest
        strategy_name: Name of the strategy for display purposes (default: "Strategy")

    Example:
        >>> from desk.stats import display_backtest_metrics
        >>> display_backtest_metrics(
        ...     portfolio=portfolio,
        ...     close_prices=df["close"],
        ...     strategy_name="Golden Cross"
        ... )
    """
    st.success("✅ Backtest completed successfully!")
    st.subheader("📊 Performance Metrics")

    # Top-level metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_return = portfolio.total_return() * 100
        st.metric(
            "Total Return",
            f"{total_return:.2f}%",
            delta=f"{total_return:.2f}%",
        )

    with col2:
        sharpe_ratio = portfolio.sharpe_ratio()
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

    with col3:
        max_dd = portfolio.max_drawdown() * 100
        st.metric("Max Drawdown", f"{max_dd:.2f}%", delta=f"-{max_dd:.2f}%")

    with col4:
        win_rate = portfolio.trades.win_rate() * 100
        st.metric("Win Rate", f"{win_rate:.2f}%")

    # Detailed statistics section
    st.subheader("📈 Detailed Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Portfolio Stats**")
        st.metric("Final Value", f"${portfolio.final_value():.2f}")
        st.metric("Total Profit", f"${portfolio.total_profit():.2f}")
        st.metric("Total Trades", portfolio.trades.count())

    with col2:
        st.markdown("**Trade Analysis**")
        st.metric("Winning Trades", portfolio.trades.winning.count())
        st.metric("Losing Trades", portfolio.trades.losing.count())
        avg_win = portfolio.trades.winning.pnl.mean() if portfolio.trades.winning.count() > 0 else 0
        st.metric("Avg Win", f"${avg_win:.2f}")

    with col3:
        st.markdown("**Risk Metrics**")
        calmar = portfolio.calmar_ratio()
        st.metric("Calmar Ratio", f"{calmar:.2f}")
        sortino = portfolio.sortino_ratio()
        st.metric("Sortino Ratio", f"{sortino:.2f}")
        avg_loss = portfolio.trades.losing.pnl.mean() if portfolio.trades.losing.count() > 0 else 0
        st.metric("Avg Loss", f"${avg_loss:.2f}")

    # Strategy vs Buy & Hold comparison
    st.subheader("📊 Strategy vs Buy & Hold")
    buy_hold_return = ((close_prices.iloc[-1] / close_prices.iloc[0]) - 1) * 100
    outperformance = total_return - buy_hold_return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            f"{strategy_name} Return",
            f"{total_return:.2f}%",
            delta=f"{total_return:.2f}%",
        )

    with col2:
        st.metric(
            "Buy & Hold Return",
            f"{buy_hold_return:.2f}%",
            delta=f"{buy_hold_return:.2f}%",
        )

    with col3:
        st.metric(
            "Outperformance",
            f"{outperformance:.2f}%",
            delta=f"{outperformance:.2f}%",
            delta_color="normal" if outperformance > 0 else "inverse",
        )
