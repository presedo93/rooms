import streamlit as st

from tape.pages.binance import binance_page
from tape.pages.bybit import bybit_page
from tape.pages.gecko import gecko_page


def tape_pages():
    st.header("📼 ~ tape room")

    gecko = st.Page(gecko_page, title="Gecko", icon="🦎", url_path="/")
    bybit = st.Page(bybit_page, title="Bybit", icon="🧠", url_path="/bybit")
    binance = st.Page(binance_page, title="Binance", icon="💸", url_path="/binance")

    with st.container(horizontal=True):
        st.page_link(gecko, label="Go to Gecko")
        st.page_link(bybit, label="Go to Bybit")
        st.page_link(binance, label="Go to Binance")

    pages = [gecko, bybit, binance]
    st.navigation(pages, position="hidden").run()


if __name__ == "__main__":
    tape_pages()
