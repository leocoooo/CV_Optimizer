"""
Page de conseils LLM personnalisés.
"""

import streamlit as st
from ui.utils.api_client import APIClient


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de conseils LLM."""
    st.header("💡 Conseils personnalisés pour votre CV")
    st.markdown(
        "Obtenez des recommandations d'un LLM pour optimiser votre CV par rapport à une offre"
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choisir un fichier CV (PDF)",
            type=["pdf"],
            help="Formats acceptés: PDF uniquement",
        )

    with col2:
        st.subheader("Offre ciblée")
        job_id = st.text_input(
            "ID de l'offre",
            placeholder="ex: abc123...",
            help="Vous pouvez trouver l'ID dans la page 'Recherche d'offres'",
        )

    if st.button(
        "💡 Obtenir des conseils",
        type="primary",
        disabled=not uploaded_file or not job_id or not api_status,
    ):
        if uploaded_file and job_id:
            with st.spinner(
                "Génération des conseils en cours... (cela peut prendre jusqu'à 60s)"
            ):
                try:
                    result = api_client.get_advice(
                        file_content=uploaded_file.getvalue(),
                        filename=uploaded_file.name,
                        job_id=job_id,
                    )

                    st.success(
                        f"✅ Conseils générés en {result['execution_time']:.2f}s"
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Poste", result["job_title"])
                    col2.metric("Entreprise", result["company"])
                    col3.metric("Modèle LLM", result.get("llm_model", "N/A"))

                    st.markdown("---")

                    st.subheader("📝 Conseils personnalisés")
                    st.markdown(result["advice"])

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")
