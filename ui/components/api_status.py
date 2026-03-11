"""
Composant d'affichage du statut de l'API.
"""

import streamlit as st
from ui.utils.config import ERROR_MESSAGES


def show_api_error():
    """Affiche un message d'erreur si l'API n'est pas disponible."""
    st.error(ERROR_MESSAGES["api_unavailable"])
    st.info("💡 **Pour démarrer l'API :** `uvicorn app.main:app --reload`")
