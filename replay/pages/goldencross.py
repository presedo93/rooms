import streamlit as st

from desk.files import upload_ohlcv_parquet_with_preview


def goldencross_page():
    st.header("🕹️ ~ 🛵 ~ golden cross")

    df = upload_ohlcv_parquet_with_preview()
