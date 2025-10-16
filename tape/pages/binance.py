import streamlit as st

from desk.pages.ohlcv import candles_expander
from tape.models import get_exchange


def binance_page():
    exchange = get_exchange("binance")

    st.title("Binance")

    if exchange.has["fetchOHLCV"]:
        candles_expander(exchange=exchange)
