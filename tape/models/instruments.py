"""Exchange instrument data models.

This module contains Pydantic models for validating and storing instrument
information from exchange APIs.
"""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from tape.models import Exchange


class Instrument(BaseModel):
    """Validated instrument data from exchange markets.

    This model extracts only the essential fields from the exchange's
    market data, ensuring type safety and data validation.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="ignore",  # Ignore extra fields from exchange response
        populate_by_name=True,
    )

    symbol: str
    type: str
    base: str
    quote: str
    active: bool = True

    # Optional fields that might be useful
    spot: bool = Field(default=False)
    future: bool = Field(default=False)
    option: bool = Field(default=False)
    swap: bool = Field(default=False)

    @classmethod
    def fetch(cls, exchange: Exchange) -> dict[str, "Instrument"]:
        """Fetch and validate all markets from the exchange.

        Args:
            exchange: The exchange instance to fetch markets from.

        Returns:
            Dictionary mapping symbol to validated Instrument instance.
        """
        markets = exchange.load_markets()
        return {symbol: cls.model_validate(market) for symbol, market in markets.items()}

    @classmethod
    def fetch_list(cls, exchange: Exchange) -> list["Instrument"]:
        """Fetch and validate all markets as a list.

        Args:
            exchange: The exchange instance to fetch markets from.

        Returns:
            List of validated Instrument instances.
        """
        instruments = cls.fetch(exchange)
        return list(instruments.values())
