"""Golden Cross backtesting strategy using vectorbt.

This module implements a classic Golden Cross (DMAC) strategy where:
- Buy signal: Fast MA crosses above Slow MA
- Sell signal: Fast MA crosses below Slow MA

The strategy uses vectorbt for efficient backtesting and portfolio analysis.
Supports parameter optimization to find the best MA window combinations.
"""

from typing import Any, cast

import numpy as np
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
from desk.stats import display_backtest_metrics
from desk.typing.vectorbt import PortfolioProtocol


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
    logger.info(
        f"Running Golden Cross optimization: fast={fast_range}, slow={slow_range}, "
        f"metric={optimize_metric}"
    )

    with st.spinner("🔄 Running optimization across all parameter combinations..."):
        try:
            # Prepare data
            df_indexed = df.set_index("time").copy()
            close_prices: pd.Series = cast(pd.Series, df_indexed["close"].astype(float))

            # Create parameter grids using meshgrid
            fast_windows_grid, slow_windows_grid = np.meshgrid(
                fast_range, slow_range, indexing="ij"
            )

            # Calculate all MAs for all window combinations
            # Create a DataFrame where each column is a different parameter combination
            all_entries = []
            all_exits = []
            param_labels = []

            progress_bar = st.progress(0, text="Calculating indicators...")
            total_combinations = len(fast_range) * len(slow_range)

            for i, fast_w in enumerate(fast_range):
                for j, slow_w in enumerate(slow_range):
                    # Skip invalid combinations (fast >= slow)
                    if fast_w >= slow_w:
                        continue

                    # Calculate MAs
                    fast_ma = pd.Series(
                        talib.MA(close_prices.to_numpy(), timeperiod=fast_w),
                        index=close_prices.index,
                    )
                    slow_ma = pd.Series(
                        talib.MA(close_prices.to_numpy(), timeperiod=slow_w),
                        index=close_prices.index,
                    )

                    # Generate signals
                    fast_above = fast_ma > slow_ma
                    entries = fast_above & ~fast_above.shift(1, fill_value=False)

                    fast_below = fast_ma < slow_ma
                    exits = fast_below & ~fast_below.shift(1, fill_value=False)

                    all_entries.append(entries)
                    all_exits.append(exits)
                    param_labels.append(f"Fast={fast_w}, Slow={slow_w}")

                    # Update progress
                    progress = (i * len(slow_range) + j + 1) / total_combinations
                    progress_bar.progress(
                        progress, text=f"Calculating indicators... {int(progress * 100)}%"
                    )

            if not all_entries:
                st.error("❌ No valid parameter combinations found (Fast must be < Slow)")
                return

            progress_bar.empty()

            # Convert to DataFrames for vectorbt broadcasting
            entries_df = pd.DataFrame(
                {label: series for label, series in zip(param_labels, all_entries)},
                index=close_prices.index,
            )
            exits_df = pd.DataFrame(
                {label: series for label, series in zip(param_labels, all_exits)},
                index=close_prices.index,
            )

            # Run vectorbt simulation for all combinations at once
            st.info(f"🚀 Running {len(param_labels)} backtests in parallel...")

            # Broadcast close prices to match number of parameter combinations
            close_array = np.array(close_prices.values)
            close_broadcasted = np.broadcast_to(
                close_array.reshape(-1, 1), (len(close_prices), len(param_labels))
            )

            portfolio: Any = vbt.Portfolio.from_signals(
                close=close_broadcasted,
                entries=entries_df.values,
                exits=exits_df.values,
                init_cash=initial_cash,
                fees=fees,
                freq="1D",
            )

            # Extract metrics for all combinations
            st.subheader("📊 Optimization Results")

            # Get all metrics at once (returns Series when multiple columns)
            total_returns = portfolio.total_return()
            sharpe_ratios = portfolio.sharpe_ratio()
            sortino_ratios = portfolio.sortino_ratio()
            calmar_ratios = portfolio.calmar_ratio()
            max_drawdowns = portfolio.max_drawdown()
            trade_counts = portfolio.trades.count()
            win_rates = portfolio.trades.win_rate()

            # Build results DataFrame
            results_data = []
            for idx, label in enumerate(param_labels):
                # Extract parameters from label
                fast_w = int(label.split(",")[0].split("=")[1])
                slow_w = int(label.split("=")[2])

                # Get metrics for this parameter combination
                total_return = float(total_returns.iloc[idx])
                sharpe = float(sharpe_ratios.iloc[idx])
                max_dd = float(max_drawdowns.iloc[idx])
                num_trades = int(trade_counts.iloc[idx])

                # Safe access to win rate
                win_rate = 0.0
                if num_trades > 0:
                    win_rate = float(win_rates.iloc[idx])

                sortino = float(sortino_ratios.iloc[idx])
                calmar = float(calmar_ratios.iloc[idx])

                results_data.append({
                    "Fast MA": fast_w,
                    "Slow MA": slow_w,
                    "Total Return (%)": total_return * 100,
                    "Sharpe Ratio": sharpe,
                    "Sortino Ratio": sortino,
                    "Calmar Ratio": calmar,
                    "Max Drawdown (%)": max_dd * 100,
                    "Win Rate (%)": win_rate * 100,
                    "Num Trades": num_trades,
                })

            results_df = pd.DataFrame(results_data)

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
                pivot_data = results_df.pivot(
                    index="Slow MA", columns="Fast MA", values=sort_column
                )

                import plotly.graph_objects as go

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
                st.markdown(
                    f"**Running detailed backtest with Fast={best_fast}, Slow={best_slow}**"
                )
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

        except Exception as e:
            st.error(f"❌ Optimization failed: {str(e)}")
            logger.exception("Golden Cross optimization failed")


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
