"""Shared OHLCV page components for exchange pages."""

from datetime import datetime, timezone
from typing import cast

import streamlit as st

from desk.plotting.candles import plot_candles
from tape.models import Exchange, Instrument
from tape.models.ohlcv import OHLCV


def initialize_candles_session_state():
    """Initialize session state variables for candles."""
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


def datetime_inputs():
    """Render date and time input widgets.

    Returns:
        tuple: (start_timestamp_ms, end_timestamp_ms) in UTC milliseconds
    """
    with st.container(horizontal=True):
        from_date = st.date_input("Start date")
        from_time = st.time_input("Start time")

        to_date = st.date_input("End date")
        to_time = st.time_input("End time")

    # Convert local time inputs to UTC timestamps
    local_tz = datetime.now().astimezone().tzinfo

    start_naive = datetime.combine(from_date, from_time)
    start_local = start_naive.replace(tzinfo=local_tz)
    start_utc = start_local.astimezone(timezone.utc)
    start_dt = int(start_utc.timestamp() * 1000)

    end_naive = datetime.combine(to_date, to_time)
    end_local = end_naive.replace(tzinfo=local_tz)
    end_utc = end_local.astimezone(timezone.utc)
    end_dt = int(end_utc.timestamp() * 1000)

    return start_dt, end_dt


def instrument_timeframe_inputs(exchange: Exchange, exchange_name: str):
    """Render instrument and timeframe selection widgets.

    Args:
        exchange: Exchange instance
        exchange_name: Display name for the exchange

    Returns:
        tuple: (instrument, timeframe)
    """
    instrument = st.selectbox(
        f"{exchange_name} instrument",
        options=fetch_instruments(exchange),
        format_func=lambda i: f"{i.symbol} - {i.type}",
    )

    timeframe = st.selectbox("Timeframe", options=exchange.timeframes)

    return instrument, timeframe


def fetch_and_store_ohlcv(
    exchange: Exchange,
    instrument: Instrument,
    timeframe: str,
    start_dt: int,
    end_dt: int,
):
    """Fetch OHLCV data and store in session state.

    Args:
        exchange: Exchange instance
        instrument: Selected instrument
        timeframe: Selected timeframe
        start_dt: Start timestamp in milliseconds
        end_dt: End timestamp in milliseconds
    """
    candles = OHLCV.fetch(
        exchange,
        symbol=instrument.symbol,
        timeframe=timeframe,
        since=start_dt,
        params={"end": end_dt},
    )

    st.session_state.candles = candles
    st.session_state.instrument = instrument
    st.session_state.start_dt = start_dt
    st.session_state.end_dt = end_dt
    st.session_state.timeframe = timeframe


def render_candles_chart():
    """Render the candlestick chart if data is available in session state."""
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


def render_download_button():
    """Render the download button for OHLCV data as Parquet."""
    if st.button("Download OHLCV", type="primary", width="stretch"):
        # Type cast needed because session_state typing is imprecise
        candles = cast(list[OHLCV], st.session_state.candles)
        OHLCV.to_parquet(
            symbol=st.session_state.instrument.symbol,
            timeframe=st.session_state.timeframe,
            since=st.session_state.start_dt,
            end=st.session_state.end_dt,
            candles=candles,
        )


def candles_expander(exchange: Exchange):
    """Render a complete OHLCV expander with all controls.

    Args:
        exchange: Exchange instance
        exchange_name: Display name for the exchange (used in labels)
        expander_title: Title for the expander
    """
    exchange_name = cast(str, exchange.name)
    with st.expander("OHLVC"):
        initialize_candles_session_state()

        start_dt, end_dt = datetime_inputs()

        with st.container(
            horizontal=True, key=f"{exchange_name}_controls", vertical_alignment="bottom"
        ):
            instrument, timeframe = instrument_timeframe_inputs(exchange, exchange_name)

            if st.button("Fetch OHLCV data", type="primary", key=f"fetch_{exchange_name}"):
                fetch_and_store_ohlcv(
                    exchange=exchange,
                    instrument=instrument,
                    timeframe=timeframe,
                    start_dt=start_dt,
                    end_dt=end_dt,
                )

        render_candles_chart()

        if st.session_state.candles is not None:
            render_download_button()


@st.cache_data(show_spinner="Fetching instruments...")
def fetch_instruments(_exc: Exchange):
    """Fetch and cache instruments for an exchange.

    Args:
        _exc: Exchange instance (underscore prefix prevents streamlit from hashing)

    Returns:
        list[Instrument]: List of available instruments
    """
    return Instrument.fetch_list(_exc)
