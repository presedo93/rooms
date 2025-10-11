import streamlit as st
from loguru import logger

from tape.pages.bybit import bybit_page
from tape.pages.gecko import gecko_page


def tape_pages():
    logger.debug("Tape visited")
    st.header("📼 ~ tape room")

    gecko = st.Page(gecko_page, title="Gecko", icon="🦎", url_path="/")
    bybit = st.Page(bybit_page, title="Bybit", icon="🧠", url_path="/bybit")

    with st.container(horizontal=True):
        st.page_link(gecko, label="Go to Gecko")
        st.page_link(bybit, label="Go to Bybit")

    pages = [gecko, bybit]
    st.navigation(pages, position="hidden").run()


if __name__ == "__main__":
    tape_pages()
