import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from tape.models import Exchange
from loguru import logger
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

OHLCV_FIELDS = ["time", "open", "high", "low", "close", "volume"]


class OHLCV(BaseModel):
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
        since: int | None = None,
        end: int | None = None,
        limit: int | None = None,
        candles: list["OHLCV"],
    ):
        base_dir = Path(__file__).resolve().parents[2]
        output_dir = base_dir / "data" / "ohlcv"
        output_dir.mkdir(parents=True, exist_ok=True)

        symbol = symbol.replace("/", "")
        path = output_dir / f"bybit_{symbol}_{timeframe}_{since}_{end or limit}.parquet"
        logger.debug(f"Writing OHLCV data to {path}")

        pd.DataFrame([c.model_dump() for c in candles]).to_parquet(
            path,
            engine="pyarrow",
            compression="zstd",
            index=True,
        )
