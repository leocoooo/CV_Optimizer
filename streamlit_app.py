"""
Frontend Streamlit pour l'API CV-Optimizer - Point d'entrée principal.
"""

import streamlit as st
from ui.utils.config import PAGE_CONFIG, CUSTOM_CSS
from ui.utils.api_client import APIClient
from ui.components.sidebar import render_sidebar
from ui.components.api_status import show_api_error
from ui.pages import matching, jobs, advice, admin, about

# Configuration de la page
st.set_page_config(**PAGE_CONFIG)

# Application du CSS personnalisé
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialisation de l'URL API dans session_state
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# Création du client API
api_client = APIClient(st.session_state.api_url)

# Vérification du statut de l'API
api_status = api_client.check_health()

# Affichage de la sidebar et récupération de la page sélectionnée
page, new_api_url = render_sidebar(st.session_state.api_url, api_status)

# Mise à jour de l'URL si changée
if new_api_url != st.session_state.api_url:
    st.session_state.api_url = new_api_url
    api_client = APIClient(new_api_url)
    api_status = api_client.check_health()
    st.rerun()

# Titre principal avec gradient
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   background-clip: text; font-size: 3rem; margin: 0; border: none;'>
            📄 CV-Optimizer
        </h1>
        <p style='color: #666; font-size: 1.2rem; margin-top: 0.5rem;'>
            Trouvez les meilleures offres d'emploi correspondant à votre profil et peaufiner votre CV
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Affichage d'un message d'erreur si l'API n'est pas disponible
if not api_status:
    show_api_error()

st.markdown("---")

# Routage vers la page appropriée
if page == "🎯 Matching CV":
    matching.render(api_client, api_status)
elif page == "💼 Recherche d'offres":
    jobs.render(api_client, api_status)
elif page == "💡 Conseils LLM":
    advice.render(api_client, api_status)
elif page == "🔧 Admin":
    admin.render(api_client, api_status)
elif page == "ℹ️ À propos":
    about.render()
