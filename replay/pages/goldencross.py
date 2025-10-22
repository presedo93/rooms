"""Golden Cross backtesting strategy using vectorbt.

This module implements a classic Golden Cross (DMAC) strategy where:
- Buy signal: Fast MA crosses above Slow MA
- Sell signal: Fast MA crosses below Slow MA

The strategy uses vectorbt for efficient backtesting and portfolio analysis.
"""

from typing import cast
import pandas as pd
import streamlit as st
import talib
import vectorbt as vbt
from loguru import logger

from desk.files import upload_ohlcv_parquet_with_preview
from desk.plotting.backtest import (
    plot_drawdown_from_vectorbt,
    plot_portfolio_equity_from_vectorbt,
    plot_price_with_signals,
)


def goldencross_page():
    """Golden Cross strategy backtesting page."""
    st.header("🕹️ ~ 🛵 ~ Golden Cross Strategy")

    st.markdown(
        """
        The **Golden Cross** is a bullish momentum signal when a short-term moving average 
        crosses above a long-term moving average. Conversely, a **Death Cross** occurs when 
        the short-term MA crosses below the long-term MA.

        **Strategy Rules:**
        - 🟢 **Buy**: When Fast MA crosses above Slow MA
        - 🔴 **Sell**: When Fast MA crosses below Slow MA
        """
    )

    # File upload
    df = upload_ohlcv_parquet_with_preview()

    if df is None:
        st.info("👆 Please upload OHLCV parquet file(s) to begin backtesting")
        return

    # Strategy parameters
    st.subheader("⚙️ Strategy Parameters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fast_window = st.number_input(
            "Fast MA Window",
            min_value=5,
            max_value=100,
            value=50,
            step=5,
            help="Short-term moving average period (typically 50)",
        )

    with col2:
        slow_window = st.number_input(
            "Slow MA Window",
            min_value=50,
            max_value=500,
            value=200,
            step=10,
            help="Long-term moving average period (typically 200)",
        )

    with col3:
        initial_cash = st.number_input(
            "Initial Cash ($)",
            min_value=100.0,
            max_value=1_000_000.0,
            value=10_000.0,
            step=1000.0,
            help="Starting capital for backtesting",
        )

    with col4:
        fees = st.number_input(
            "Fees (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.3f",
            help="Trading fees per transaction (e.g., 0.1% = 0.001)",
        )

    # Validate parameters
    if fast_window >= slow_window:
        st.error("⚠️ Fast MA window must be smaller than Slow MA window")
        return

    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary", use_container_width=True):
        run_golden_cross_backtest(
            df=df,
            fast_window=fast_window,
            slow_window=slow_window,
            initial_cash=initial_cash,
            fees=fees / 100,  # Convert percentage to decimal
        )


def run_golden_cross_backtest(
    df: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    initial_cash: float,
    fees: float,
) -> None:
    """Execute Golden Cross backtest and display results.

    Args:
        df: OHLCV DataFrame with columns [time, open, high, low, close, volume]
        fast_window: Fast moving average window
        slow_window: Slow moving average window
        initial_cash: Initial portfolio cash
        fees: Trading fees as decimal (e.g., 0.001 for 0.1%)
    """
    logger.info(
        f"Running Golden Cross backtest: fast={fast_window}, slow={slow_window}, "
        f"cash={initial_cash}, fees={fees}"
    )

    with st.spinner("🔄 Calculating indicators and running backtest..."):
        try:
            # Prepare data - ensure proper types
            df_indexed = df.set_index("time").copy()
            close_prices: pd.Series = cast(pd.Series, df_indexed["close"].astype(float))

            # Calculate moving averages using pandas (more stable with Python 3.13)
            fast_ma = pd.Series(
                talib.MA(close_prices.to_numpy(), timeperiod=fast_window),
                index=close_prices.index,
            )
            slow_ma = pd.Series(
                talib.MA(close_prices.to_numpy(), timeperiod=slow_window),
                index=close_prices.index,
            )

            # Generate signals: Buy when fast MA crosses above slow MA
            # Entry: fast MA crosses above slow MA (as Series)
            fast_above = fast_ma > slow_ma
            entries = fast_above & ~fast_above.shift(1, fill_value=False)

            # Exit: fast MA crosses below slow MA (as Series)
            fast_below = fast_ma < slow_ma
            exits = fast_below & ~fast_below.shift(1, fill_value=False)

            # Run portfolio simulation with vectorbt
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices.values,
                entries=entries.values,
                exits=exits.values,
                init_cash=initial_cash,
                fees=fees,
                freq="1D",  # Assume daily frequency for annualization
            )

            # Display results
            display_backtest_results(
                portfolio=portfolio,
                close_prices=close_prices,
                fast_ma=fast_ma,
                slow_ma=slow_ma,
                entries=entries,
                exits=exits,
                fast_window=fast_window,
                slow_window=slow_window,
            )

        except Exception as e:
            st.error(f"❌ Backtest failed: {str(e)}")
            logger.exception("Golden Cross backtest failed")


def display_backtest_results(
    portfolio,
    close_prices: pd.Series,
    fast_ma: pd.Series,
    slow_ma: pd.Series,
    entries: pd.Series,
    exits: pd.Series,
    fast_window: int | None = None,
    slow_window: int | None = None,
) -> None:
    """Display comprehensive backtest results with metrics and visualizations.

    Args:
        portfolio: vectorbt Portfolio object
        close_prices: Series of close prices
        fast_ma: Fast moving average series
        slow_ma: Slow moving average series
        entries: Boolean series indicating entry signals
        exits: Boolean series indicating exit signals
    """
    st.success("✅ Backtest completed successfully!")
    st.subheader("📊 Performance Metrics")

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

    # Additional metrics
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
        st.metric("Strategy Return", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")
    with col2:
        st.metric("Buy & Hold Return", f"{buy_hold_return:.2f}%", delta=f"{buy_hold_return:.2f}%")
    with col3:
        st.metric(
            "Outperformance",
            f"{outperformance:.2f}%",
            delta=f"{outperformance:.2f}%",
            delta_color="normal" if outperformance > 0 else "inverse",
        )

    # Equity curve
    st.subheader("💰 Equity Curve")
    fig_equity = plot_portfolio_equity_from_vectorbt(
        portfolio=portfolio,
        close_prices=close_prices,
        strategy_name="Golden Cross Strategy",
    )
    st.plotly_chart(fig_equity, use_container_width=True)

    # Price chart with signals
    st.subheader("📉 Price Chart with Signals")
    # Build indicators dict with window info if available
    indicators = {}
    if fast_window is not None:
        indicators[f"Fast MA ({fast_window})"] = fast_ma
    else:
        indicators["Fast MA"] = fast_ma

    if slow_window is not None:
        indicators[f"Slow MA ({slow_window})"] = slow_ma
    else:
        indicators["Slow MA"] = slow_ma

    fig_signals = plot_price_with_signals(
        price=close_prices,
        entries=entries,
        exits=exits,
        indicators=indicators,
        title="Price Chart with Golden Cross Signals",
    )
    st.plotly_chart(fig_signals, use_container_width=True)

    # Trades table
    st.subheader("📋 Trade History")
    trades_df = portfolio.trades.records_readable
    if len(trades_df) > 0:
        # Select columns that exist in the dataframe
        available_cols = trades_df.columns.tolist()
        desired_cols = ["Entry Date", "Exit Date", "PnL", "Return", "Duration"]
        display_cols = [col for col in desired_cols if col in available_cols]

        # If no desired columns exist, show all columns
        if not display_cols:
            display_cols = available_cols

        st.dataframe(
            trades_df[display_cols],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("⚠️ No trades were executed during this period")

    # Drawdown chart
    with st.expander("📉 Drawdown Analysis", expanded=False):
        fig_dd = plot_drawdown_from_vectorbt(portfolio)
        st.plotly_chart(fig_dd, use_container_width=True)
