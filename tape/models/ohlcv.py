"""OHLCV (Open, High, Low, Close, Volume) data model for candlestick data.

This module provides a Pydantic model for working with OHLCV data from cryptocurrency
exchanges via CCXT. It handles data validation, type conversion, and persistence.
"""

import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from tape.models import Exchange
from loguru import logger
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# Standard OHLCV field names expected from CCXT exchange responses
OHLCV_FIELDS = ["time", "open", "high", "low", "close", "volume"]


class OHLCV(BaseModel):
    """OHLCV candlestick data model.

    Represents a single candlestick with Open, High, Low, Close prices and Volume.
    Uses Decimal for precise price handling and timezone-aware datetime for timestamps.

    Attributes:
        time: Candlestick timestamp (UTC timezone-aware)
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Trading volume during the period

    Examples:
        Create from a dictionary:
        >>> ohlcv = OHLCV(
        ...     time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ...     open=Decimal("42000.50"),
        ...     high=Decimal("42500.00"),
        ...     low=Decimal("41800.00"),
        ...     close=Decimal("42300.75"),
        ...     volume=Decimal("125.5")
        ... )

        Create from CCXT array format:
        >>> raw_data = [1704067200000, 42000.5, 42500, 41800, 42300.75, 125.5]
        >>> ohlcv = OHLCV.model_validate(raw_data)
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @model_validator(mode="before")
    @classmethod
    def _from_sequence(cls, data):
        """Allow parsing the raw list payload returned by exchanges.

        CCXT returns OHLCV data as arrays: [timestamp, open, high, low, close, volume].
        This validator converts them to dictionaries for Pydantic validation.
        """
        if isinstance(data, (list, tuple)):
            # Handle arrays with 6+ elements (timestamp, O, H, L, C, V, [optional fields])
            extracted = dict(zip(OHLCV_FIELDS, data))
            return extracted
        return data

    @field_validator("time", mode="before")
    @classmethod
    def _parse_time(cls, value):
        """Parse timestamp to datetime.

        CCXT returns timestamps in milliseconds since epoch.
        """
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)

    @field_validator("open", "high", "low", "close", "volume", mode="before")
    @classmethod
    def _parse_decimal(cls, value):
        """Parse numeric values to Decimal for precision."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @classmethod
    def fetch(
        cls,
        exchange: Exchange,
        *,
        symbol: str,
        timeframe: str = "1m",
        since: int | None = None,
        limit: int | None = None,
        params: dict[str, Any] = {},
    ) -> Sequence["OHLCV"]:
        """Fetch OHLCV candlestick data from an exchange.

        Args:
            exchange: CCXT exchange instance to fetch data from
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            timeframe: Candlestick timeframe (e.g., "1m", "5m", "1h", "1d")
                Must be one of the timeframes supported by the exchange.
            since: Start time in milliseconds since Unix epoch (UTC)
                If None, fetches the most recent candles.
            limit: Maximum number of candles to fetch
                If None, uses the exchange's default limit.
            params: Additional exchange-specific parameters
                Common parameters:
                - "end" (Bybit): End time in milliseconds
                - "endTime" (Binance): End time in milliseconds
                - "until" (some exchanges): End time in milliseconds

        Returns:
            Sequence of validated OHLCV instances, ordered by time (oldest first)

        Raises:
            ccxt.ExchangeError: If the exchange API returns an error
            pydantic.ValidationError: If the data doesn't match the expected format

        Examples:
            Fetch last 100 1-hour candles:
            >>> exchange = ccxt.binance()
            >>> candles = OHLCV.fetch(
            ...     exchange,
            ...     symbol="BTC/USDT",
            ...     timeframe="1h",
            ...     limit=100
            ... )

            Fetch candles for a specific time range:
            >>> from datetime import datetime, timezone
            >>> start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            >>> end = datetime(2024, 1, 2, tzinfo=timezone.utc)
            >>> candles = OHLCV.fetch(
            ...     exchange,
            ...     symbol="BTC/USDT",
            ...     timeframe="1h",
            ...     since=int(start.timestamp() * 1000),
            ...     params={"endTime": int(end.timestamp() * 1000)}
            ... )

            Fetch with exchange-specific parameters:
            >>> # Bybit example
            >>> exchange = ccxt.bybit()
            >>> candles = OHLCV.fetch(
            ...     exchange,
            ...     symbol="BTC/USDT:USDT",
            ...     timeframe="15m",
            ...     since=1704067200000,
            ...     params={"end": 1704153600000, "category": "linear"}
            ... )
        """
        logger.info(
            f"Fetching OHLCV data for {symbol} on {timeframe} timeframe "
            f"(since={since}, limit={limit})"
        )

        raw_data = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
            params=params,
        )

        # Validate and convert raw data to OHLCV model instances
        v_data = [cls.model_validate(candle) for candle in raw_data]
        logger.info(f"Successfully fetched and validated {len(v_data)} candles")

        return v_data

    @classmethod
    def to_parquet(
        cls,
        symbol: str,
        timeframe: str | None,
        *,
        exchange: Exchange | None = None,
        since: int | None = None,
        end: int | None = None,
        limit: int | None = None,
        candles: list["OHLCV"],
    ) -> None:
        """Save OHLCV data to a Parquet file.

        Exports candlestick data to a compressed Parquet file in the data/ohlcv directory.
        The file is named using the format: {exchange}_{symbol}_{timeframe}_{since}_{end_or_limit}.parquet

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
                Forward slashes are removed from the filename.
            timeframe: Candlestick timeframe (e.g., "1m", "5m", "1h", "1d")
                Used in the filename to identify the data granularity.
            exchange: Exchange instance (optional)
                If provided, uses exchange.id for the filename prefix.
                If None, defaults to "unknown" prefix.
            since: Start timestamp in milliseconds (used in filename)
            end: End timestamp in milliseconds (used in filename)
            limit: Number of candles limit (used in filename if end is None)
            candles: List of OHLCV instances to export

        Side Effects:
            - Creates data/ohlcv directory if it doesn't exist
            - Writes a Parquet file with ZSTD compression
            - Logs the output path at DEBUG level

        File Format:
            - Engine: PyArrow
            - Compression: ZSTD (high compression ratio, good performance)
            - Columns: time, open, high, low, close, volume
            - Index: True (uses pandas default index)

        Examples:
            Save fetched candles with exchange prefix:
            >>> exchange = ccxt.binance()
            >>> candles = OHLCV.fetch(
            ...     exchange,
            ...     symbol="BTC/USDT",
            ...     timeframe="1h",
            ...     since=1704067200000,
            ...     params={"endTime": 1704153600000}
            ... )
            >>> OHLCV.to_parquet(
            ...     exchange=exchange,
            ...     symbol="BTC/USDT",
            ...     timeframe="1h",
            ...     since=1704067200000,
            ...     end=1704153600000,
            ...     candles=candles
            ... )
            # Creates: data/ohlcv/binance_BTCUSDT_1h_1704067200000_1704153600000.parquet

            Save with limit instead of end time:
            >>> exchange = ccxt.bybit()
            >>> OHLCV.to_parquet(
            ...     exchange=exchange,
            ...     symbol="ETH/USDT",
            ...     timeframe="5m",
            ...     since=1704067200000,
            ...     limit=100,
            ...     candles=candles
            ... )
            # Creates: data/ohlcv/bybit_ETHUSDT_5m_1704067200000_100.parquet

            Save without exchange (defaults to "unknown" prefix):
            >>> OHLCV.to_parquet(
            ...     symbol="SOL/USDT",
            ...     timeframe="15m",
            ...     since=1704067200000,
            ...     end=1704153600000,
            ...     candles=candles
            ... )
            # Creates: data/ohlcv/unknown_SOLUSDT_15m_1704067200000_1704153600000.parquet

        Notes:
            - The filename prefix is derived from exchange.id (lowercased)
            - If no exchange is provided, defaults to "unknown" prefix
            - Parquet format is ideal for time-series data and integrates well with
              pandas, polars, and other data analysis tools
            - ZSTD compression typically achieves 10-20x compression for OHLCV data
        """
        base_dir = Path(__file__).resolve().parents[2]
        output_dir = base_dir / "data" / "ohlcv"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get exchange prefix from exchange.id or default to "unknown"
        exchange_prefix = str(exchange.id).lower() if exchange and exchange.id else "unknown"
        symbol = symbol.replace("/", "")
        path = output_dir / f"{exchange_prefix}_{symbol}_{timeframe}_{since}_{end or limit}.parquet"
        logger.debug(f"Writing OHLCV data to {path}")

        pd.DataFrame([c.model_dump() for c in candles]).to_parquet(
            path,
            engine="pyarrow",
            compression="zstd",
            index=True,
        )
