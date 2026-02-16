"""
Composant sidebar avec navigation et configuration.
"""

import streamlit as st
from ui.utils.config import PAGES


def render_sidebar(api_url: str, api_status: bool) -> tuple[str, str]:
    """
    Affiche la sidebar avec navigation et statut API.

    Args:
        api_url: URL de l'API
        api_status: Statut de l'API (True si connectée)

    Returns:
        Tuple (page_selectionnée, api_url)
    """
    st.sidebar.title("📄 CV-Optimizer")
    st.sidebar.markdown("---")

    # Configuration API
    st.sidebar.subheader("⚙️ Configuration")
    api_url = st.sidebar.text_input("URL de l'API", value=api_url)

    # Statut API
    if api_status:
        st.sidebar.success("✅ API connectée")
    else:
        st.sidebar.error("❌ API non disponible")

    st.sidebar.markdown("---")

    # Navigation
    st.sidebar.subheader("📍 Navigation")
    page = st.sidebar.radio(
        "Choisir une page", list(PAGES.keys()), label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # Footer
    st.sidebar.markdown("**CV-Optimizer** v1.0.0")
    st.sidebar.markdown("Made with ❤️ using Streamlit")

    return page, api_url
