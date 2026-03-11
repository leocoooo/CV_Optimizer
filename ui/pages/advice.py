"""
Page de conseils LLM personnalisés.
"""

import html
import streamlit as st
from ui.utils.api_client import APIClient
from ui.components.cards import gradient_header, metric_card, status_message, info_card
from ui.components.file_helpers import cv_uploader


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de conseils LLM."""
    gradient_header(
        "💡 Conseils personnalisés pour votre CV",
        "Obtenez des recommandations d'un LLM pour optimiser votre CV par rapport à une offre",
        gradient="yellow",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = cv_uploader(key="advice_cv")

    with col2:
        info_card("🎯 Offre ciblée", "", gradient="dark")
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

                    status_message(
                        f"✅ Conseils générés en {result['execution_time']:.2f}s",
                        "success",
                    )

                    # Métriques
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        metric_card("Poste", result["job_title"], "purple")
                    with col2:
                        metric_card("Entreprise", result["company"], "pink")
                    with col3:
                        metric_card(
                            "Modèle LLM", result.get("llm_model", "N/A"), "blue"
                        )

                    st.markdown("---")

                    # Conseils
                    info_card("📝 Conseils personnalisés", "", gradient="yellow")
                    st.markdown(
                        f"""
                        <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 8px; 
                                    border-left: 4px solid #fa709a;'>
                            {html.escape(result["advice"])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")
