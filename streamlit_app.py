"""
Frontend Streamlit principal pour CV-Optimizer.
"""

import streamlit as st

from ui.components.api_status import show_api_error
from ui.components.sidebar import render_sidebar
from ui.components.top_nav import render_top_nav
from ui.pages import admin, advice, home, jobs, matching
from ui.utils.api_client import APIClient
from ui.utils.config import CUSTOM_CSS, DEFAULT_API_URL, PAGE_CONFIG
from ui.utils.navigation import sync_page_state


st.set_page_config(**PAGE_CONFIG)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

current_page = sync_page_state()

api_client = APIClient(st.session_state.api_url)
api_status = api_client.check_health()

status_details = None
if api_status:
    try:
        status_details = api_client.get_status()
    except Exception:
        status_details = None

page, new_api_url = render_sidebar(
    st.session_state.api_url, api_status, status_details=status_details
)

if new_api_url != st.session_state.api_url:
    st.session_state.api_url = new_api_url
    st.rerun()

page = render_top_nav(
    current_page=current_page,
    title="CV-Optimizer",
    api_status=api_status,
)

if not api_status:
    show_api_error()

if page == "home":
    home.render(api_client, api_status, status_details=status_details)
elif page == "matching":
    matching.render(api_client, api_status)
elif page == "jobs":
    jobs.render(api_client, api_status)
elif page == "advice":
    advice.render(api_client, api_status)
elif page == "admin":
    admin.render(api_client, api_status, status_details=status_details)
