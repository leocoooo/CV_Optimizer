"""
Composant sidebar avec navigation et configuration.
"""

import streamlit as st

from ui.utils.config import DEFAULT_API_URL, NAV_ITEMS, PAGE_META
from ui.utils.formatters import format_uptime, friendly_status_label


def render_sidebar(
    api_url: str, api_status: bool, status_details: dict | None = None
) -> tuple[str, str]:
    """
    Affiche la sidebar avec navigation, configuration API et statut.

    Returns:
        Tuple (page_selectionnee, api_url)
    """
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    page_options = [item["key"] for item in NAV_ITEMS]
    if st.session_state.current_page not in page_options:
        st.session_state.current_page = "home"

    st.sidebar.markdown(
        """
        <div style="padding: 0.4rem 0 0.8rem 0;">
            <p style="margin:0; font-size:0.78rem; letter-spacing:0.16em; text-transform:uppercase; color:rgba(111,118,104,0.78);">
                Plateforme candidature
            </p>
            <h1 style="margin:0.28rem 0 0 0; border:none; color:#e48a49; font-size:1.5rem;">
                CV-Optimizer
            </h1>
            <p style="margin:0.45rem 0 0 0; color:rgba(61,76,69,0.86); line-height:1.55; font-size:0.92rem;">
                Matching CV, lecture du marche et coaching cible dans une seule experience.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Connexion plateforme")
    new_api_url = st.sidebar.text_input("URL API", value=api_url or DEFAULT_API_URL)

    if api_status:
        st.sidebar.success("Plateforme disponible")
        if status_details:
            uptime = format_uptime(status_details.get("uptime_seconds"))
            database_label = friendly_status_label(
                status_details.get("database"),
                ok_label="Synchronisee",
                warning_label="A verifier",
            )
            st.sidebar.caption(
                f"Base: {database_label} · Uptime: {uptime}"
            )
    else:
        st.sidebar.error("Service indisponible")
        st.sidebar.caption("La navigation reste accessible pendant l'interruption.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Vue active")
    active_meta = PAGE_META[st.session_state.current_page]
    st.sidebar.markdown(
        f"**{active_meta['icon']} {active_meta['label']}**"
    )
    st.sidebar.caption(active_meta["description"])

    st.sidebar.markdown("---")
    st.sidebar.caption("Usage")
    st.sidebar.markdown(
        """
        - navigation fixe en haut
        - panneau lateral reserve au contexte
        - actions disponibles dans chaque vue
        """
    )

    return st.session_state.current_page, new_api_url
