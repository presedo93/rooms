"""Golden Cross strategy backtesting page.

This Streamlit page provides UI for backtesting the Golden Cross strategy,
including single backtests and parameter optimization. The actual strategy
logic is implemented in replay.strategies.goldencross.
"""

from __future__ import annotations

from typing import cast

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loguru import logger

from desk.files import upload_ohlcv_parquet_with_preview
from desk.plotting.backtest import (
    plot_drawdown_from_vectorbt,
    plot_portfolio_equity_from_vectorbt,
    plot_price_with_signals,
)
from desk.stats import display_backtest_metrics
from desk.typing.vectorbt import PortfolioProtocol
from replay.strategies.goldencross import GoldenCrossStrategy, optimize_golden_cross


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

    # Mode selection
    st.subheader("🎯 Mode Selection")
    mode = st.radio(
        "Choose mode:",
        options=["Single Backtest", "Parameter Optimization"],
        horizontal=True,
        help="Single: Test one parameter set. Optimization: Find best parameters.",
    )

    if mode == "Single Backtest":
        show_single_backtest_ui(df)
    else:
        show_optimization_ui(df)


def show_single_backtest_ui(df: pd.DataFrame) -> None:
    """Show UI for single backtest with fixed parameters."""
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


def show_optimization_ui(df: pd.DataFrame) -> None:
    """Show UI for parameter optimization."""
    st.subheader("🔍 Optimization Parameters")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Fast MA Window Range**")
        fast_min = st.number_input("Min", min_value=5, max_value=100, value=10, step=5)
        fast_max = st.number_input("Max", min_value=5, max_value=100, value=50, step=5)
        fast_step = st.number_input("Step", min_value=1, max_value=20, value=5, step=1)

    with col2:
        st.markdown("**Slow MA Window Range**")
        slow_min = st.number_input("Min", min_value=20, max_value=500, value=100, step=10)
        slow_max = st.number_input("Max", min_value=20, max_value=500, value=200, step=10)
        slow_step = st.number_input("Step", min_value=1, max_value=50, value=10, step=1)

    col3, col4, col5 = st.columns(3)

    with col3:
        initial_cash = st.number_input(
            "Initial Cash ($)",
            min_value=100,
            max_value=1_000_000,
            value=10_000,
            step=1000,
            help="Starting capital for all backtests",
        )

    with col4:
        fees = st.number_input(
            "Fees (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.01,
            format="%.3f",
        )

    with col5:
        optimize_metric = st.selectbox(
            "Optimize For",
            options=[
                "Sharpe Ratio",
                "Total Return",
                "Calmar Ratio",
                "Sortino Ratio",
                "Win Rate",
            ],
        )

    # Validate ranges
    if fast_min >= fast_max:
        st.error("⚠️ Fast MA min must be less than max")
        return
    if slow_min >= slow_max:
        st.error("⚠️ Slow MA min must be less than max")
        return
    if fast_max >= slow_min:
        st.warning("⚠️ Fast MA max should be less than Slow MA min")

    # Calculate number of combinations
    fast_range = range(fast_min, fast_max + 1, fast_step)
    slow_range = range(slow_min, slow_max + 1, slow_step)
    num_combinations = len(list(fast_range)) * len(list(slow_range))

    st.info(
        f"📊 Will test **{num_combinations}** parameter combinations "
        f"({len(list(fast_range))} fast × {len(list(slow_range))} slow windows)"
    )

    if num_combinations > 1000:
        st.warning("⚠️ Large number of combinations may take significant time to compute.")

    # Run optimization button
    if st.button("🔍 Run Optimization", type="primary", use_container_width=True):
        run_golden_cross_optimization(
            df=df,
            fast_range=list(fast_range),
            slow_range=list(slow_range),
            initial_cash=initial_cash,
            fees=fees / 100,
            optimize_metric=optimize_metric,
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
    with st.spinner("🔄 Calculating indicators and running backtest..."):
        try:
            # Create strategy instance
            strategy = GoldenCrossStrategy(
                fast_window=fast_window,
                slow_window=slow_window,
                initial_cash=initial_cash,
                fees=fees,
            )

            # Run backtest
            portfolio, close_prices, fast_ma, slow_ma, entries, exits = strategy.run_backtest(df)

            # Display results
            # Cast to Protocol type for LSP autocomplete while maintaining runtime compatibility
            display_backtest_results(
                portfolio=cast(PortfolioProtocol, portfolio),
                close_prices=close_prices,
                fast_ma=fast_ma,
                slow_ma=slow_ma,
                entries=entries,
                exits=exits,
                fast_window=fast_window,
                slow_window=slow_window,
            )

        except ValueError as e:
            st.error(f"⚠️ {str(e)}")
        except Exception as e:
            st.error(f"❌ Backtest failed: {str(e)}")
            logger.exception("Golden Cross backtest failed")


def run_golden_cross_optimization(
    df: pd.DataFrame,
    fast_range: list[int],
    slow_range: list[int],
    initial_cash: float,
    fees: float,
    optimize_metric: str,
) -> None:
    """Run parameter optimization to find best MA window combinations.

    Uses vectorbt's broadcasting feature to test all parameter combinations efficiently.

    Args:
        df: OHLCV DataFrame with columns [time, open, high, low, close, volume]
        fast_range: List of fast MA windows to test
        slow_range: List of slow MA windows to test
        initial_cash: Initial portfolio cash
        fees: Trading fees as decimal (e.g., 0.001 for 0.1%)
        optimize_metric: Metric to optimize ('Sharpe Ratio', 'Total Return', etc.)
    """
    with st.spinner("🔄 Running optimization across all parameter combinations..."):
        try:
            # Show progress bar while calculating
            progress_bar = st.progress(0, text="Calculating indicators...")

            # Run optimization using strategy module
            portfolio, results_df, param_labels = optimize_golden_cross(
                df=df,
                fast_range=fast_range,
                slow_range=slow_range,
                initial_cash=initial_cash,
                fees=fees,
            )

            progress_bar.empty()
            st.info(f"🚀 Completed {len(param_labels)} backtests")

            # Display optimization results
            display_optimization_results(
                results_df=results_df,
                optimize_metric=optimize_metric,
                df=df,
                initial_cash=initial_cash,
                fees=fees,
            )

        except ValueError as e:
            st.error(f"⚠️ {str(e)}")
        except Exception as e:
            st.error(f"❌ Optimization failed: {str(e)}")
            logger.exception("Golden Cross optimization failed")


def display_optimization_results(
    results_df: pd.DataFrame,
    optimize_metric: str,
    df: pd.DataFrame,
    initial_cash: float,
    fees: float,
) -> None:
    """Display optimization results with visualizations.

    Args:
        results_df: DataFrame with optimization results
        optimize_metric: Metric that was optimized
        df: Original OHLCV DataFrame
        initial_cash: Initial cash used
        fees: Trading fees used
    """
    st.subheader("📊 Optimization Results")

    # Find best parameters based on selected metric
    metric_column_map = {
        "Sharpe Ratio": "Sharpe Ratio",
        "Total Return": "Total Return (%)",
        "Calmar Ratio": "Calmar Ratio",
        "Sortino Ratio": "Sortino Ratio",
        "Win Rate": "Win Rate (%)",
    }
    sort_column = metric_column_map[optimize_metric]

    # Sort by metric (descending)
    results_df_sorted = results_df.sort_values(sort_column, ascending=False)

    # Display top results
    st.markdown(f"### 🏆 Top 10 Parameter Combinations by {optimize_metric}")
    st.dataframe(
        results_df_sorted.head(10).style.format({
            "Total Return (%)": "{:.2f}",
            "Sharpe Ratio": "{:.2f}",
            "Sortino Ratio": "{:.2f}",
            "Calmar Ratio": "{:.2f}",
            "Max Drawdown (%)": "{:.2f}",
            "Win Rate (%)": "{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Show best parameters
    best_row = results_df_sorted.iloc[0]
    best_fast = int(best_row["Fast MA"])
    best_slow = int(best_row["Slow MA"])

    st.success(
        f"✨ **Best Parameters**: Fast MA = {best_fast}, Slow MA = {best_slow} "
        f"({optimize_metric} = {best_row[sort_column]:.2f})"
    )

    # Visualizations
    with st.expander("📈 Heatmap Visualization", expanded=True):
        # Create pivot table for heatmap
        pivot_data = results_df.pivot(index="Slow MA", columns="Fast MA", values=sort_column)

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale="RdYlGn",
                text=pivot_data.values,
                texttemplate="%{text:.2f}",
                textfont={"size": 10},
                colorbar=dict(title=optimize_metric),
            )
        )

        fig.update_layout(
            title=f"{optimize_metric} Heatmap",
            xaxis_title="Fast MA Window",
            yaxis_title="Slow MA Window",
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Show detailed backtest for best parameters
    with st.expander("🔍 Detailed Backtest for Best Parameters", expanded=False):
        st.markdown(f"**Running detailed backtest with Fast={best_fast}, Slow={best_slow}**")
        run_golden_cross_backtest(
            df=df,
            fast_window=best_fast,
            slow_window=best_slow,
            initial_cash=initial_cash,
            fees=fees,
        )

    # Download results
    st.download_button(
        label="📥 Download Full Results (CSV)",
        data=results_df_sorted.to_csv(index=False),
        file_name="golden_cross_optimization_results.csv",
        mime="text/csv",
    )


def display_backtest_results(
    portfolio: PortfolioProtocol,
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
        fast_window: Fast MA window size (for labeling)
        slow_window: Slow MA window size (for labeling)
    """
    # Display performance metrics using generic function
    display_backtest_metrics(
        portfolio=portfolio,
        close_prices=close_prices,
        strategy_name="Golden Cross Strategy",
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
