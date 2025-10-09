import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from loguru import logger

from tape.pages.bybit import bybit_page
from tape.pages.gecko import gecko_page

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
