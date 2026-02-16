"""
Page de matching CV avec offres d'emploi.
"""

import streamlit as st
from ui.utils.api_client import APIClient
from ui.utils.config import DEFAULT_TOP_N, DEFAULT_DAYS_LIMIT, MAX_TOP_N


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de matching CV."""
    st.header("🎯 Matching CV avec offres d'emploi")
    st.markdown("Uploadez votre CV pour trouver les offres les plus pertinentes")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choisir un fichier CV (PDF)",
            type=["pdf"],
            help="Formats acceptés: PDF uniquement",
        )

    with col2:
        st.subheader("Paramètres")
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

                    st.success(
                        f"✅ {data['total_matches']} offres trouvées en {data['execution_time']:.2f}s"
                    )

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Offres trouvées", data["total_matches"])
                    col2.metric("Caractères CV", data["cv_length"])
                    col3.metric("Temps d'exécution", f"{data['execution_time']:.2f}s")

                    st.markdown("---")

                    for i, match in enumerate(data["matches"], 1):
                        score_color = (
                            "🟢"
                            if match["similarity_score"] > 0.7
                            else "🟡"
                            if match["similarity_score"] > 0.5
                            else "🔴"
                        )

                        with st.expander(
                            f"{score_color} #{i} - {match['title']} - {match['company']} ({match['similarity_score']:.1%})"
                        ):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.markdown(f"**Entreprise:** {match['company']}")
                                if match.get("location"):
                                    st.markdown(
                                        f"**Localisation:** {match['location']}"
                                    )
                                if match.get("contract_type"):
                                    st.markdown(
                                        f"**Contrat:** {match['contract_type']}"
                                    )
                                if match.get("required_experience"):
                                    st.markdown(
                                        f"**Expérience:** {match['required_experience']}"
                                    )
                                if match.get("source"):
                                    st.markdown(f"**Source:** {match['source']}")

                            with col2:
                                st.metric("Score", f"{match['similarity_score']:.1%}")
                                if match.get("url"):
                                    st.link_button("Voir l'offre", match["url"])

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")
