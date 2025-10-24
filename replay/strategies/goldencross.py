"""Golden Cross (DMAC) trading strategy implementation.

This module implements the core logic for the Golden Cross strategy:
- Buy signal: Fast MA crosses above Slow MA
- Sell signal: Fast MA crosses below Slow MA

The strategy is independent of any UI framework and can be used
for backtesting or live trading.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import talib
import vectorbt as vbt
from loguru import logger


class GoldenCrossStrategy:
    """Golden Cross (Dual Moving Average Crossover) trading strategy.

    This strategy generates buy signals when a fast moving average crosses
    above a slow moving average, and sell signals when it crosses below.

    Attributes:
        fast_window: Period for the fast (short-term) moving average
        slow_window: Period for the slow (long-term) moving average
        initial_cash: Starting capital for backtesting
        fees: Trading fees as decimal (e.g., 0.001 for 0.1%)
    """

    def __init__(
        self,
        fast_window: int,
        slow_window: int,
        initial_cash: float = 10_000.0,
        fees: float = 0.001,
    ):
        """Initialize the Golden Cross strategy.

        Args:
            fast_window: Fast moving average window (must be < slow_window)
            slow_window: Slow moving average window
            initial_cash: Initial portfolio cash
            fees: Trading fees as decimal (e.g., 0.001 for 0.1%)

        Raises:
            ValueError: If fast_window >= slow_window
        """
        if fast_window >= slow_window:
            raise ValueError(
                f"Fast window ({fast_window}) must be smaller than slow window ({slow_window})"
            )

        self.fast_window = fast_window
        self.slow_window = slow_window
        self.initial_cash = initial_cash
        self.fees = fees

    def calculate_indicators(self, close_prices: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Calculate fast and slow moving averages.

        Args:
            close_prices: Series of closing prices

        Returns:
            Tuple of (fast_ma, slow_ma) as pandas Series
        """
        fast_ma = pd.Series(
            talib.MA(close_prices.to_numpy(), timeperiod=self.fast_window),
            index=close_prices.index,
        )
        slow_ma = pd.Series(
            talib.MA(close_prices.to_numpy(), timeperiod=self.slow_window),
            index=close_prices.index,
        )
        return fast_ma, slow_ma

    def generate_signals(
        self, fast_ma: pd.Series, slow_ma: pd.Series
    ) -> tuple[pd.Series, pd.Series]:
        """Generate entry and exit signals from moving averages.

        Entry signal: Fast MA crosses above Slow MA
        Exit signal: Fast MA crosses below Slow MA

        Args:
            fast_ma: Fast moving average series
            slow_ma: Slow moving average series

        Returns:
            Tuple of (entries, exits) as boolean pandas Series
        """
        # Entry: fast MA crosses above slow MA
        fast_above = fast_ma > slow_ma
        entries = fast_above & ~fast_above.shift(1, fill_value=False)

        # Exit: fast MA crosses below slow MA
        fast_below = fast_ma < slow_ma
        exits = fast_below & ~fast_below.shift(1, fill_value=False)

        return entries, exits

    def run_backtest(
        self, df: pd.DataFrame
    ) -> tuple[Any, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Execute backtest on OHLCV data.

        Args:
            df: OHLCV DataFrame with columns [time, open, high, low, close, volume]

        Returns:
            Tuple of (portfolio, close_prices, fast_ma, slow_ma, entries, exits)
            - portfolio: vectorbt Portfolio object
            - close_prices: Series of close prices (indexed by time)
            - fast_ma: Fast moving average series
            - slow_ma: Slow moving average series
            - entries: Boolean series indicating entry signals
            - exits: Boolean series indicating exit signals

        Raises:
            Exception: If backtest execution fails
        """
        logger.info(
            f"Running Golden Cross backtest: fast={self.fast_window}, "
            f"slow={self.slow_window}, cash={self.initial_cash}, fees={self.fees}"
        )

        try:
            # Prepare data - ensure proper types
            df_indexed = df.set_index("time").copy()
            close_prices: pd.Series = cast(pd.Series, df_indexed["close"].astype(float))

            # Calculate indicators
            fast_ma, slow_ma = self.calculate_indicators(close_prices)

            # Generate signals
            entries, exits = self.generate_signals(fast_ma, slow_ma)

            # Run portfolio simulation with vectorbt
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices.values,
                entries=entries.values,
                exits=exits.values,
                init_cash=self.initial_cash,
                fees=self.fees,
                freq="1D",  # Assume daily frequency for annualization
            )

            return portfolio, close_prices, fast_ma, slow_ma, entries, exits

        except Exception:
            logger.exception("Golden Cross backtest failed")
            raise


def optimize_golden_cross(
    df: pd.DataFrame,
    fast_range: list[int],
    slow_range: list[int],
    initial_cash: float = 10_000.0,
    fees: float = 0.001,
) -> tuple[Any, pd.DataFrame, list[str]]:
    """Run parameter optimization for Golden Cross strategy.

    Tests all combinations of fast and slow window parameters to find
    the optimal configuration. Uses vectorbt's broadcasting for efficiency.

    Args:
        df: OHLCV DataFrame with columns [time, open, high, low, close, volume]
        fast_range: List of fast MA windows to test
        slow_range: List of slow MA windows to test
        initial_cash: Initial portfolio cash
        fees: Trading fees as decimal (e.g., 0.001 for 0.1%)

    Returns:
        Tuple of (portfolio, results_df, param_labels):
        - portfolio: vectorbt Portfolio object with all parameter combinations
        - results_df: DataFrame with metrics for each combination
        - param_labels: List of parameter combination labels

    Raises:
        ValueError: If no valid parameter combinations found
        Exception: If optimization fails
    """
    logger.info(f"Running Golden Cross optimization: fast={fast_range}, slow={slow_range}")

    try:
        # Prepare data
        df_indexed = df.set_index("time").copy()
        close_prices: pd.Series = cast(pd.Series, df_indexed["close"].astype(float))

        # Calculate signals for all parameter combinations
        all_entries = []
        all_exits = []
        param_labels = []

        for fast_w in fast_range:
            for slow_w in slow_range:
                # Skip invalid combinations (fast >= slow)
                if fast_w >= slow_w:
                    continue

                # Create strategy instance
                strategy = GoldenCrossStrategy(
                    fast_window=fast_w,
                    slow_window=slow_w,
                    initial_cash=initial_cash,
                    fees=fees,
                )

                # Calculate indicators and signals
                fast_ma, slow_ma = strategy.calculate_indicators(close_prices)
                entries, exits = strategy.generate_signals(fast_ma, slow_ma)

                all_entries.append(entries)
                all_exits.append(exits)
                param_labels.append(f"Fast={fast_w}, Slow={slow_w}")

        if not all_entries:
            raise ValueError("No valid parameter combinations found (Fast must be < Slow)")

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

        # Build results DataFrame
        results_data = []
        for idx, label in enumerate(param_labels):
            win_rate = 0.0
            num_trades = int(portfolio.trades.count().iloc[idx])

            if num_trades > 0:
                win_rate = float(portfolio.trades.win_rate().iloc[idx])

            results_data.append({
                "Fast MA": int(label.split(",")[0].split("=")[1]),
                "Slow MA": int(label.split("=")[2]),
                "Total Return (%)": float(portfolio.total_return().iloc[idx]) * 100,
                "Sharpe Ratio": float(portfolio.sharpe_ratio().iloc[idx]),
                "Sortino Ratio": float(portfolio.sortino_ratio().iloc[idx]),
                "Calmar Ratio": float(portfolio.calmar_ratio().iloc[idx]),
                "Max Drawdown (%)": float(portfolio.max_drawdown().iloc[idx]) * 100,
                "Win Rate (%)": win_rate * 100,
                "Num Trades": num_trades,
            })

        results_df = pd.DataFrame(results_data)
        return portfolio, results_df, param_labels

    except Exception:
        logger.exception("Golden Cross optimization failed")
        raise
