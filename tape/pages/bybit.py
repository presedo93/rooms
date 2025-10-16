import streamlit as st

from desk.pages.ohlcv import candles_expander
from tape.models import get_exchange


def bybit_page():
    exchange = get_exchange("bybit")

    st.title("ByBit")

    if exchange.has["fetchOHLCV"]:
        candles_expander(exchange=exchange)
