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
        if "candles" not in st.session_state:
            st.session_state.candles = None
        if "instrument" not in st.session_state:
            st.session_state.instrument = None
        if "start_dt" not in st.session_state:
            st.session_state.start_dt = None
        if "end_dt" not in st.session_state:
            st.session_state.end_dt = None
        if "interval" not in st.session_state:
            st.session_state.interval = None

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

                st.session_state.candles = ByBitOHLCV.fetch(
                    ByBitCategory.from_str(instrument.category),
                    instrument.symbol,
                    interval,
                    start=start_dt,
                    end=end_dt,
                )

                st.session_state.instrument = instrument
                st.session_state.start_dt = start_dt
                st.session_state.end_dt = end_dt
                st.session_state.interval = interval

        if st.session_state.candles is not None and st.session_state.instrument is not None:
            with st.container(border=True):
                st.plotly_chart(
                    plot_candles(
                        x=[candle.time for candle in st.session_state.candles],
                        open=[candle.open for candle in st.session_state.candles],
                        high=[candle.high for candle in st.session_state.candles],
                        low=[candle.low for candle in st.session_state.candles],
                        close=[candle.close for candle in st.session_state.candles],
                        symbol=st.session_state.instrument.symbol,
                    ),
                    use_container_width=True,
                )

                if st.button("Download OHLCV data as Parquet", type="primary", width="stretch"):
                    ByBitOHLCV.to_parquet(
                        symbol=st.session_state.instrument.symbol,
                        interval=st.session_state.interval,
                        start=st.session_state.start_dt,
                        end=st.session_state.end_dt,
                        candles=st.session_state.candles,
                    )


@st.cache_data(show_spinner="Fetching ByBit instruments...")
def fetch_instruments():
    return ByBitInstrument.fetch(ByBitCategory.SPOT)
