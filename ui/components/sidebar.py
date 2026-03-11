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
    # Header avec logo et titre
    st.sidebar.markdown(
        """
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #1f77b4; margin: 0; border: none;'>📄 CV-Optimizer</h1>
            <p style='color: #666; font-size: 0.9rem; margin-top: 0.5rem;'>
                Votre assistant intelligent pour la recherche d'emploi
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    # Configuration API avec statut visuel
    st.sidebar.subheader("⚙️ Configuration")
    api_url = st.sidebar.text_input("URL de l'API", value=api_url)

    # Statut API avec badge stylisé
    if api_status:
        st.sidebar.markdown(
            '<div class="status-badge status-success">✅ API connectée</div>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<div class="status-badge status-error">❌ API non disponible</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")

    # Navigation
    st.sidebar.subheader("📍 Navigation")
    page = st.sidebar.radio(
        "Choisir une page", list(PAGES.keys()), label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # Informations utiles
    with st.sidebar.expander("ℹ️ Aide rapide"):
        st.markdown(
            """
        **🎯 Matching CV**
        Uploadez votre CV pour trouver les offres les plus pertinentes
        
        **💼 Recherche d'offres**
        Recherchez des offres par mots-clés
        
        **💡 Conseils LLM**
        Obtenez des conseils personnalisés
        
        **🔧 Admin**
        Collectez de nouvelles offres
        """
        )

    # Footer avec version et info
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.85rem;'>
            <strong>CV-Optimizer</strong> v1.0.0<br>
            Made with ❤️ using Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )

    return page, api_url
