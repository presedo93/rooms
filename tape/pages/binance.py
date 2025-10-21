import streamlit as st

from desk.pages.ohlcv import candles_expander
from tape.models import get_exchange


def binance_page():
    st.header("📼 ~ 🐝 ~ binance")

    exchange = get_exchange("binance")
    if exchange.has["fetchOHLCV"]:
        candles_expander(exchange=exchange)
