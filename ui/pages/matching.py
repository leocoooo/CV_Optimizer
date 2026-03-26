"""
Page de matching CV avec offres d'emploi.
"""

import streamlit as st
import html
from ui.utils.api_client import APIClient
from ui.utils.config import DEFAULT_TOP_N, DEFAULT_DAYS_LIMIT, MAX_TOP_N
from ui.components.cards import gradient_header, metric_card, status_message, info_card
from ui.components.file_helpers import cv_uploader


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de matching CV."""
    gradient_header(
        "🎯 Matching CV avec offres d'emploi",
        "Uploadez votre CV pour trouver les offres les plus pertinentes",
        gradient="purple",
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = cv_uploader(key="matching_cv")

    with col2:
        info_card("⚙️ Paramètres", "", gradient="pink")
        top_n = st.slider(
            "Nombre de résultats", min_value=5, max_value=MAX_TOP_N, value=DEFAULT_TOP_N
        )
        days_limit = st.slider(
            "Offres des N derniers jours",
            min_value=7,
            max_value=365,
            value=DEFAULT_DAYS_LIMIT,
        )

        with st.expander("Filtres avancés"):
            location = st.text_input("Localisation", placeholder="ex: Paris")
            contract_type = st.text_input("Type de contrat", placeholder="ex: CDI")
            experience = st.selectbox(
                "Expérience", ["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"]
            )
            if experience == "Tous":
                experience = None
            else:
                experience = experience[0]

    if st.button(
        "🔍 Lancer le matching",
        type="primary",
        disabled=not uploaded_file or not api_status,
    ):
        if uploaded_file:
            with st.spinner("Analyse du CV en cours..."):
                try:
                    data = api_client.match_cv(
                        file_content=uploaded_file.getvalue(),
                        filename=uploaded_file.name,
                        top_n=top_n,
                        days_limit=days_limit,
                        location=location if location else None,
                        contract_type=contract_type if contract_type else None,
                        experience=experience,
                    )

                    status_message(
                        f"✅ {data['total_matches']} offres trouvées en {data['execution_time']:.2f}s",
                        "success",
                    )

                    # Métriques
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        metric_card(
                            "Offres trouvées", str(data["total_matches"]), "purple"
                        )
                    with col2:
                        metric_card("Caractères CV", f"{data['cv_length']:,}", "pink")
                    with col3:
                        metric_card(
                            "Temps d'exécution",
                            f"{data['execution_time']:.2f}s",
                            "blue",
                        )

                    st.markdown("---")

                    # Affichage des résultats
                    for i, match in enumerate(data["matches"], 1):
                        score = match["similarity_score"]
                        if score > 0.7:
                            score_emoji = "🟢"
                            score_class = "score-high"
                            score_label = "Excellent"
                        elif score > 0.5:
                            score_emoji = "🟡"
                            score_class = "score-medium"
                            score_label = "Bon"
                        else:
                            score_emoji = "🔴"
                            score_class = "score-low"
                            score_label = "Moyen"

                        with st.expander(
                            f"{score_emoji} #{i} - {match['title']} - {match['company'] or 'N/A'} ({match['similarity_score']:.1%})",
                            expanded=(i <= 3),
                        ):
                            # Sanitize user-provided content to prevent XSS
                            safe_title = html.escape(match["title"] or "")
                            safe_company = html.escape(
                                match["company"] or "Non disponible"
                            )

                            st.markdown(
                                f"""
                                <div style='background: linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%); 
                                            padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                                    <h3 style='margin: 0; color: #333; border: none;'>{safe_title}</h3>
                                    <p style='margin: 0.5rem 0 0 0; color: #666;'>
                                        <strong>{safe_company}</strong>
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            col1, col2 = st.columns([3, 1])

                            with col1:
                                info_items = []
                                if match.get("location"):
                                    info_items.append(
                                        f"📍 **Localisation:** {match['location']}"
                                    )
                                if match.get("contract_type"):
                                    info_items.append(
                                        f"📝 **Contrat:** {match['contract_type']}"
                                    )
                                if match.get("required_experience"):
                                    info_items.append(
                                        f"💼 **Expérience:** {match['required_experience']}"
                                    )
                                if match.get("source"):
                                    info_items.append(
                                        f"🔗 **Source:** {match['source']}"
                                    )

                                for item in info_items:
                                    st.markdown(item)

                            with col2:
                                st.markdown(
                                    f"""
                                    <div style='text-align: center; padding: 1rem; 
                                                background: #f8f9fa; border-radius: 8px;'>
                                        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>
                                            {score_emoji}
                                        </div>
                                        <div class='{score_class}' style='font-size: 1.5rem;'>
                                            {match["similarity_score"]:.1%}
                                        </div>
                                        <div style='color: #666; font-size: 0.9rem; margin-top: 0.25rem;'>
                                            {score_label}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                if match.get("url"):
                                    st.link_button(
                                        "🔗 Voir l'offre",
                                        match["url"],
                                        use_container_width=True,
                                    )

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")
