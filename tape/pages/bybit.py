from datetime import datetime, timezone
from typing import cast

import streamlit as st

from desk.plotting.candles import plot_candles

from tape.models import get_exchange, Exchange, Instrument
from tape.models.ohlcv import OHLCV


def bybit_page():
    exchange = get_exchange("bybit")

    st.title("Bybit Page")
    st.write("Welcome to the Bybit page!")

    if exchange.has["fetchOHLCV"]:
        candles_expander(exchange)


def candles_expander(exchange: Exchange):
    with st.expander("ByBit OHLCV"):
        if "candles" not in st.session_state:
            st.session_state.candles = None
        if "instrument" not in st.session_state:
            st.session_state.instrument = None
        if "start_dt" not in st.session_state:
            st.session_state.start_dt = None
        if "end_dt" not in st.session_state:
            st.session_state.end_dt = None
        if "timeframe" not in st.session_state:
            st.session_state.timeframe = None

        with st.container(horizontal=True):
            from_date = st.date_input("Start date")
            from_time = st.time_input("Start time")

            to_date = st.date_input("End date")
            to_time = st.time_input("End time")

        with st.container(horizontal=True, vertical_alignment="bottom"):
            instrument = st.selectbox(
                "ByBit instrument",
                options=fetch_instruments(exchange),
                format_func=lambda i: f"{i.symbol} - {i.type}",
            )

            timeframe = st.selectbox("timeframe", options=exchange.timeframes)

            if st.button("Fetch OHLCV data", type="primary"):
                # Convert local time inputs to UTC timestamps
                local_tz = datetime.now().astimezone().tzinfo
                start_naive = datetime.combine(from_date, from_time)
                start_local = start_naive.replace(tzinfo=local_tz)
                start_utc = start_local.astimezone(timezone.utc)
                start_dt = start_utc.timestamp()

                end_naive = datetime.combine(to_date, to_time)
                end_local = end_naive.replace(tzinfo=local_tz)
                end_utc = end_local.astimezone(timezone.utc)
                end_dt = end_utc.timestamp()

                candles = OHLCV.fetch(
                    exchange,
                    symbol=instrument.symbol,
                    timeframe=timeframe,
                    since=int(start_dt * 1000),
                    params={"end": int(end_dt * 1000)},
                )

                st.session_state.candles = candles
                st.session_state.instrument = instrument
                st.session_state.start_dt = int(start_dt * 1000)
                st.session_state.end_dt = int(end_dt * 1000)
                st.session_state.timeframe = timeframe

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
                    # Type cast needed because session_state typing is imprecise
                    candles = cast(list[OHLCV], st.session_state.candles)
                    OHLCV.to_parquet(
                        symbol=st.session_state.instrument.symbol,
                        timeframe=st.session_state.timeframe,
                        since=st.session_state.start_dt,
                        end=st.session_state.end_dt,
                        candles=candles,
                    )


@st.cache_data(show_spinner="Fetching ByBit instruments...")
def fetch_instruments(_exc: Exchange):
    return Instrument.fetch_list(_exc)
