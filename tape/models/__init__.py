import ccxt
from ccxt.binance import binance
from ccxt.bybit import bybit

type Exchange = bybit | binance

from tape.models.instruments import Instrument  # noqa: E402
from tape.models.ohlcv import OHLCV  # noqa: E402


def get_exchange(name: str) -> Exchange:
    match name.lower():
        case "bybit":
            return ccxt.bybit()
        case "binance":
            return ccxt.binance()
        case _:
            raise ValueError(f"Unsupported exchange: {name}")


__all__ = ["Exchange", "get_exchange", "Instrument", "OHLCV"]
