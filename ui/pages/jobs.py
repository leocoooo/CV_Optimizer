"""
Page de recherche d'offres d'emploi.
"""

import streamlit as st
from ui.utils.api_client import APIClient
from ui.utils.config import DEFAULT_PAGE_SIZE, DEFAULT_DAYS_LIMIT


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de recherche d'offres."""
    st.header("💼 Recherche d'offres d'emploi")
    st.markdown("Parcourez et filtrez les offres disponibles dans la base de données")

    col1, col2, col3 = st.columns(3)

    with col1:
        keywords = st.text_input("Mots-clés", placeholder="ex: Python, Data")
        location = st.text_input("Localisation", placeholder="ex: Paris")

    with col2:
        contract_type = st.text_input("Type de contrat", placeholder="ex: CDI")
        experience = st.selectbox(
            "Expérience", ["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"]
        )
        if experience == "Tous":
            experience = None
        else:
            experience = experience[0]

    with col3:
        source = st.text_input("Source", placeholder="ex: France Travail")
        days_limit = st.slider(
            "Offres des N derniers jours",
            min_value=7,
            max_value=365,
            value=DEFAULT_DAYS_LIMIT,
        )

    col1, col2 = st.columns([1, 3])
    with col1:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col2:
        page_size = st.slider(
            "Résultats par page",
            min_value=10,
            max_value=100,
            value=DEFAULT_PAGE_SIZE,
            step=10,
        )

    if st.button("🔍 Rechercher", type="primary", disabled=not api_status):
        with st.spinner("Recherche en cours..."):
            try:
                data = api_client.search_jobs(
                    page=page_num,
                    page_size=page_size,
                    keywords=keywords if keywords else None,
                    location=location if location else None,
                    contract_type=contract_type if contract_type else None,
                    experience=experience,
                    source=source if source else None,
                    days_limit=days_limit,
                )

                st.success(f"✅ {data['total']} offres trouvées")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total", data["total"])
                col2.metric("Page", f"{data['page']}/{data['total_pages']}")
                col3.metric("Résultats", len(data["jobs"]))

                st.markdown("---")

                for i, job in enumerate(data["jobs"], 1):
                    with st.expander(
                        f"#{(page_num - 1) * page_size + i} - {job['title']} - {job['company']}"
                    ):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"**Entreprise:** {job['company']}")
                            if job.get("location"):
                                st.markdown(f"**Localisation:** {job['location']}")
                            if job.get("contract_type"):
                                st.markdown(f"**Contrat:** {job['contract_type']}")
                            if job.get("required_experience"):
                                st.markdown(
                                    f"**Expérience:** {job['required_experience']}"
                                )
                            if job.get("description"):
                                st.markdown(
                                    f"**Description:** {job['description'][:200]}..."
                                )
                            if job.get("source"):
                                st.markdown(f"**Source:** {job['source']}")

                        with col2:
                            st.markdown(f"**ID:** `{job['id'][:8]}...`")
                            if job.get("url"):
                                st.link_button("Voir l'offre", job["url"])

            except Exception as e:
                st.error(f"❌ Erreur lors de la requête: {str(e)}")
