"""ByBit exchange data.

This module contains pydantic models that mirror the ByBit API responses and
convenience helpers to fetch instrument lists from the public API.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import ClassVar, Generic, TypeVar

import httpx
import pandas as pd
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class ByBitResponse(BaseModel, Generic[T]):
    """Top-level response wrapper returned by ByBit."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, validate_by_alias=True
    )

    result: "ByBitResult[T]"


class ByBitCategory(str, Enum):
    """Enumeration of ByBit API categories."""

    SPOT = "spot"
    LINEAR = "linear"
    INVERSE = "inverse"
    OPTION = "option"

    @classmethod
    def from_str(cls, category: str | None) -> "ByBitCategory":
        """Convert a string to a ByBitCategory enum in a case-insensitive way."""
        if category is None:
            return ByBitCategory.SPOT

        return cls(category.lower())


class ByBitResult(BaseModel, Generic[T]):
    """Result container for ByBit API responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, validate_by_alias=True
    )

    category: "ByBitCategory"
    data: list[T] = Field(alias="list")
    symbol: str = Field(default="", alias="symbol")


class ByBitInstrument(BaseModel):
    """Pydantic model that represents a ByBit instrument record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, validate_by_alias=True
    )

    symbol: str
    category: str | None = None
    base_coin: str
    quote_coin: str

    @classmethod
    def fetch(cls, category: "ByBitCategory") -> list["ByBitInstrument"]:
        """Fetch instruments from ByBit API for the requested category.

        Returns a list of ByBitInstrument DTOs built from the API response.
        """
        logger.info(f"ByBit instruments fetch started for {category}")

        endpoint = "https://api.bybit.com/v5/market/instruments-info"
        params = {"category": category.value}

        response = httpx.get(endpoint, params=params)
        response.raise_for_status()

        logger.trace(f"ByBit instruments fetch response: {response.text}")
        result = ByBitResponse["ByBitInstrument"].model_validate(response.json())

        category = result.result.category
        top_category = category.value if hasattr(category, "value") else str(category)

        return [
            cls(
                symbol=d.symbol,
                base_coin=d.base_coin,
                quote_coin=d.quote_coin,
                category=top_category,
            )
            for d in result.result.data
        ]


# TODO: move to a common place.
def _ensure_utc(dt: datetime) -> datetime:
    """Return a UTC-aware datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# TODO: move to a common place.
def _to_milliseconds(value: datetime | int | float | None) -> int | None:
    """Convert datetime or numeric timestamp to ByBit's millisecond resolution."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return int(_ensure_utc(value).timestamp() * 1000)
    return int(value)


def _format_filename_timestamp(dt: datetime) -> str:
    """Format a datetime for safe filename tokens."""
    return _ensure_utc(dt).strftime("%Y%m%dT%H%M%SZ")


INTERVALS = ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"]
OHLCV_FIELDS = ["time", "open", "high", "low", "close", "volume", "turnover"]


class ByBitOHLCV(BaseModel):
    """Pydantic model that represents an OHLCV dataset for a given instrument."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, validate_by_alias=True
    )

    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    turnover: Decimal | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_sequence(cls, data):
        """Allow parsing the raw list payload returned by ByBit."""
        if isinstance(data, (list, tuple)):
            # Keys must match ByBitOHLCV fields in order: time, open, high, low, close, volume, turnover
            extracted = dict(zip(OHLCV_FIELDS, data))
            return extracted
        return data

    @field_validator("time", mode="before")
    @classmethod
    def _parse_time(cls, value):
        if isinstance(value, datetime):
            return _ensure_utc(value)
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)

    @field_validator(*OHLCV_FIELDS, mode="before")
    @classmethod
    def _parse_decimal(cls, value):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @classmethod
    def intervals(cls) -> list[str]:
        """Return a list of supported ByBit KLine intervals."""
        return INTERVALS

    @classmethod
    def fetch(
        cls,
        category: ByBitCategory,
        symbol: str,
        interval: str,
        *,
        start: datetime | int | float | None = None,
        end: datetime | int | float | None = None,
        limit: int | None = None,
    ) -> list["ByBitOHLCV"]:
        """Fetch KLine (OHLCV) data from ByBit for the requested instrument."""
        logger.info(f"ByBit OHLCV fetch started for {symbol} ({category}) on interval {interval}")

        endpoint = "https://api.bybit.com/v5/market/kline"
        params: dict[str, str | int] = {
            "category": category.value,
            "symbol": symbol,
            "interval": interval,
        }

        start_ms = _to_milliseconds(start)
        if start_ms is not None:
            params["start"] = start_ms

        end_ms = _to_milliseconds(end)
        if end_ms is not None:
            params["end"] = end_ms

        if limit is not None:
            params["limit"] = int(limit)

        response = httpx.get(endpoint, params=params)
        response.raise_for_status()

        logger.trace(f"ByBit OHLCV fetch response: {response.text}")

        response = ByBitResponse["ByBitOHLCV"].model_validate(response.json())
        return response.result.data

    @classmethod
    def to_csv(
        cls,
        symbol: str,
        interval: str,
        *,
        start: datetime | int | float | None = None,
        end: datetime | int | float | None = None,
        candles: list["ByBitOHLCV"],
    ):
        start_ms = _to_milliseconds(start)
        end_ms = _to_milliseconds(end)

        path = f"../../data/bybit_ohlcv_{symbol}_{interval}_{start_ms}_{end_ms}.csv"
        pd.DataFrame([c.model_dump() for c in candles]).to_csv(path, index=False)
