from datetime import datetime

import streamlit as st
from models.bybit import ByBitCategory, ByBitInstrument, ByBitOHLCV


def bybit_page():
    st.title("Bybit Page")
    st.write("Welcome to the Bybit page!")

    with st.expander("ByBit OHLCV Data"):
        with st.container(horizontal=True):
            from_date = st.date_input("Start date")
            from_time = st.time_input("Start time")

            to_date = st.date_input("End date")
            to_time = st.time_input("End time")

        with st.container(horizontal=True, vertical_alignment="bottom"):
            instrument = st.selectbox(
                "ByBit instrument",
                options=fetch_instruments(),
                format_func=lambda i: f"{i.symbol} - {i.category}",
            )

            interval = st.selectbox(
                "Interval",
                options=ByBitOHLCV.intervals(),
            )

            if st.button("Fetch OHLCV data", type="primary"):
                start_dt = datetime.combine(from_date, from_time)
                end_dt = datetime.combine(to_date, to_time)

                st.write(
                    f"Selected instrument: {instrument.symbol}, Category: {instrument.category}, From: {start_dt}, To: {end_dt}"
                )

                candles = ByBitOHLCV.fetch(
                    ByBitCategory.from_str(instrument.category),
                    instrument.symbol,
                    interval,
                    start=start_dt,
                    end=end_dt,
                )
                st.write(f"Fetched {len(candles)} candles.")


@st.cache_data(show_spinner="Fetching ByBit instruments...")
def fetch_instruments():
    return ByBitInstrument.fetch(ByBitCategory.from_str("spot"))
