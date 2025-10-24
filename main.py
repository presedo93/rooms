import sys
import streamlit as st
from loguru import logger

from lab.main import lab_pages
from replay.pages import goldencross_page
from tape.pages import gecko_page, bybit_page, binance_page

logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add("rooms.log", level="TRACE", rotation="10 MB", compression="zip")


def main():
    st.title("🪙 Welcome to my trading room!")

    # Define all pages
    t_gecko = st.Page(gecko_page, title="Gecko", icon="🦎", url_path="/gecko")
    t_bybit = st.Page(bybit_page, title="Bybit", icon="🐯", url_path="/bybit")
    t_binance = st.Page(binance_page, title="Binance", icon="🐝", url_path="/binance")

    r_gc = st.Page(goldencross_page, title="Golden Cross", icon="🛵", url_path="/goldencross")

    lab_main = st.Page(lab_pages, title="Lab", icon="🧪", url_path="/lab")

    nav = st.navigation(
        {
            "📼 Tape": [t_gecko, t_bybit, t_binance],
            "🕹️ Replay": [r_gc],
            "🧪 Lab": [lab_main],
        },
        position="top",
    )
    nav.run()


if __name__ == "__main__":
    main()
