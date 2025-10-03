import streamlit as st

from loguru import logger

from pages.bybit import bybit_page
from pages.gecko import gecko_page

logger.level("DEBUG")
logger.add("tape.log", retention="2 days")


def main():
    logger.info("Tape started")
    st.title("📼 Welcome to my Tape room")

    gecko = st.Page(gecko_page, title="Gecko", icon="🦎", url_path="/")
    bybit = st.Page(bybit_page, title="Gecko", icon="🧠", url_path="/bybit")

    with st.container(horizontal=True):
        st.page_link(gecko, label="Go to Gecko")
        st.page_link(bybit, label="Go to Bybit")

    pages = [gecko, bybit]
    st.navigation(pages, position="hidden").run()


if __name__ == "__main__":
    main()
