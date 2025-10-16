import streamlit as st

from desk.pages.ohlcv import candles_expander
from tape.models import get_exchange


def binance_page():
    exchange = get_exchange("binance")

    st.title("binance Page")
    st.write("Welcome to the binance page!")

    if exchange.has["fetchOHLCV"]:
        candles_expander(exchange=exchange)
