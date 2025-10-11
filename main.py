import streamlit as st
from loguru import logger

from lab.main import lab_pages
from replay.main import replay_pages
from tape.main import tape_pages

logger.level("DEBUG")
logger.add("rooms.log", retention="2 days")


def main():
    st.title("🪙 Welcome to my trading room!")
    tape = st.Page(tape_pages, title="Tape", icon="📼", url_path="/")
    replay = st.Page(replay_pages, title="Replay", icon="🕹️", url_path="/replay")
    lab = st.Page(lab_pages, title="Lab", icon="🧪", url_path="/lab")

    with st.container(horizontal=True):
        st.page_link(tape, label="Go to tape", width="stretch")
        st.page_link(replay, label="Go to replay", width="stretch")
        st.page_link(lab, label="Go to lab", width="stretch")

    st.navigation([tape, replay, lab], position="hidden").run()


if __name__ == "__main__":
    main()
