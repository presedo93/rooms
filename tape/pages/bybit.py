from datetime import datetime

import streamlit as st

from desk.plotting.candles import plot_candles
from tape.models.bybit import ByBitCategory, ByBitInstrument, ByBitOHLCV


def bybit_page():
    st.title("Bybit Page")
    st.write("Welcome to the Bybit page!")

    candles_expander()


def candles_expander():
    with st.expander("ByBit OHLCV"):
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

                candles = ByBitOHLCV.fetch(
                    ByBitCategory.from_str(instrument.category),
                    instrument.symbol,
                    interval,
                    start=start_dt,
                    end=end_dt,
                )

                fig = plot_candles(
                    x=[candle.time for candle in candles],
                    open=[candle.open for candle in candles],
                    high=[candle.high for candle in candles],
                    low=[candle.low for candle in candles],
                    close=[candle.close for candle in candles],
                    symbol=instrument.symbol,
                )
                st.plotly_chart(fig, use_container_width=True)

                # if st.button("Download OHLCV data as CSV"):
                #     ByBitOHLCV.to_csv(
                #         symbol=instrument.symbol,
                #         interval=interval,
                #         start=start_dt,
                #         end=end_dt,
                #         candles=candles,
                #     )


@st.cache_data(show_spinner="Fetching ByBit instruments...")
def fetch_instruments():
    return ByBitInstrument.fetch(ByBitCategory.SPOT)
