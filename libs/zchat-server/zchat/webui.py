import os
import sys
sys.path.append(os.getcwd())

import streamlit as st
import streamlit_antd_components as sac

from zchat import __version__
from zchat.webui_pages.dialogue.dialogue import dialogue_page
from zchat.webui_pages.utils import *


api = ApiRequest(base_url=api_address())


if __name__ == "__main__":
    st.set_page_config(
        "Langchain-zchat WebUI",
        initial_sidebar_state="expanded",
        layout="centered",
    )
    
    # use the following code to set the app to wide mode and the html markdown to increase the sidebar width
    st.markdown(
        """
        <style>
        [data-testid="stSidebarUserContent"] {
            padding-top: 20px;
        }
        .block-container {
            padding-top: 25px;
        }
        [data-testid="stBottomBlockContainer"] {
            padding-bottom: 20px;
        }
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.caption(
            f"""<p align="right">当前版本：{__version__}</p>""",
            unsafe_allow_html=True,
        )

        selected_page = sac.menu(
            [
                sac.MenuItem("多功能对话", icon="chat"),
                sac.MenuItem("RAG 对话", icon="database"),
                sac.MenuItem("知识库管理", icon="hdd-stack"),
            ],
            key="selected_page",
            open_index=0,
        )

        sac.divider()
    
    dialogue_page(api)