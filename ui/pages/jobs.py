"""
Page de recherche d'offres d'emploi.
"""

import streamlit as st
from datetime import datetime
from ui.utils.api_client import APIClient
from ui.utils.config import DEFAULT_PAGE_SIZE, DEFAULT_DAYS_LIMIT
from ui.components.cards import gradient_header, metric_card, status_message


def render(api_client: APIClient, api_status: bool):
    """Affiche la page de recherche d'offres."""
    gradient_header(
        "💼 Recherche d'offres d'emploi",
        "Parcourez et filtrez les offres disponibles dans la base de données",
        gradient="blue",
    )

    # Message d'aide pour l'utilisateur
    st.info(
        """
        💡 **Comment utiliser la recherche :**
        - Laissez tous les champs vides pour voir toutes les offres récentes
        - Ajoutez des filtres pour affiner votre recherche
        - Utilisez les mots-clés pour rechercher dans les titres et descriptions
        - Le filtre "Offres des N derniers jours" s'applique à la **date de publication** (ou date de collecte si date de pub. manquante)
        """
    )

    # === FILTRES PRINCIPAUX ===
    col1, col2, col3 = st.columns(3)

    with col1:
        keywords = st.text_input("Mots-clés", placeholder="ex: Python, Data")
        location = st.text_input("Localisation", placeholder="ex: Paris")

    with col2:
        contract_type = st.text_input("Type de contrat", placeholder="ex: CDI")
        experience = st.selectbox(
            "Expérience",
            ["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"],
        )
        if experience == "Tous":
            experience = None
        else:
            experience = experience[0]

    with col3:
        source = st.selectbox(
            "Source",
            ["Aucune filter", "France Travail", "HelloWork", "Welcome to the Jungle"],
        )
        if source == "Aucune filter":
            source = None

        days_limit = st.slider(
            "Offres des N derniers jours",
            min_value=7,
            max_value=365,
            value=DEFAULT_DAYS_LIMIT,
        )

    # === FILTRES AVANCÉS ===
    # Initialisation des valeurs par défaut
    sector = None
    remote_mode = None
    company = None
    education = None

    with st.expander("⚙️ Filtres avancés"):
        col1, col2 = st.columns(2)

        with col1:
            sector = st.text_input("Secteur d'activité", placeholder="ex: IT, Finance")
            if not sector:
                sector = None
            company = st.text_input("Entreprise", placeholder="ex: Google")
            if not company:
                company = None

        with col2:
            remote_mode = st.text_input(
                "Mode télétravail", placeholder="ex: Hybride, 100% remote"
            )
            if not remote_mode:
                remote_mode = None
            education = st.text_input("Niveau d'études", placeholder="ex: Bac+5")
            if not education:
                education = None

    # === PAGINATION ===
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
                    sector=sector if sector else None,
                    remote_mode=remote_mode if remote_mode else None,
                    company=company if company else None,
                    required_education=education if education else None,
                    days_limit=days_limit,
                )

                # Gestion du cas "0 résultats"
                if data["total"] == 0:
                    st.warning(
                        "🔍 Aucune offre ne correspond à vos critères de recherche."
                    )

                    # Suggestions pour améliorer la recherche
                    st.info(
                        """
                        💡 **Suggestions pour améliorer votre recherche :**
                        - Essayez d'élargir la période de recherche (augmentez le nombre de jours)
                        - Retirez certains filtres pour obtenir plus de résultats
                        - Vérifiez l'orthographe de vos mots-clés
                        - Essayez des termes plus généraux (ex: "Data" au lieu de "Data Scientist")
                        """
                    )
                else:
                    status_message(f"✅ {data['total']} offres trouvées", "success")

                    # Métriques
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        metric_card("Total", str(data["total"]), "purple")
                    with col2:
                        metric_card(
                            "Page", f"{data['page']}/{data['total_pages']}", "pink"
                        )
                    with col3:
                        metric_card("Résultats", str(len(data["jobs"])), "blue")

                    st.markdown("---")

                    for i, job in enumerate(data["jobs"], 1):
                        with st.expander(
                            f"#{(page_num - 1) * page_size + i} · {job['title']} · {job['company']}"
                        ):
                            # En-tête avec infos essentielles
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                            with col1:
                                st.markdown(f"### {job['company']}")
                                if job.get("company_size"):
                                    st.caption(
                                        f"Taille: {job.get('company_size', 'N/A')}"
                                    )

                            with col2:
                                if job.get("contract_type"):
                                    st.markdown(f"**{job['contract_type']}**")

                            with col3:
                                if job.get("salary"):
                                    st.markdown(f"💰 {job['salary']}")

                            with col4:
                                if job.get("source"):
                                    st.caption(f"📍 {job['source']}")

                            st.divider()

                            # Infos localisation et profil
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if job.get("location"):
                                    st.markdown(
                                        f"**📍 Localisation**\n{job['location']}"
                                    )

                            with col2:
                                if job.get("required_experience"):
                                    st.markdown(
                                        f"**📈 Expérience**\n{job['required_experience']}"
                                    )

                            with col3:
                                if job.get("remote_mode"):
                                    st.markdown(
                                        f"**🏠 Télétravail**\n{job['remote_mode']}"
                                    )
                                if job.get("sector"):
                                    st.markdown(f"**🏢 Secteur**\n{job['sector']}")
                                if job.get("required_education"):
                                    st.markdown(
                                        f"**🎓 Études**\n{job['required_education']}"
                                    )

                            st.divider()

                            # Compétences et langues
                            if (
                                job.get("competences")
                                or job.get("soft_skills")
                                or job.get("languages")
                            ):
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if job.get("competences"):
                                        st.markdown("**🔧 Compétences techniques**")
                                        st.caption(
                                            job["competences"][:200]
                                            + (
                                                "..."
                                                if len(job.get("competences", "")) > 200
                                                else ""
                                            )
                                        )

                                with col2:
                                    if job.get("soft_skills"):
                                        st.markdown("**💬 Soft skills**")
                                        st.caption(
                                            job["soft_skills"][:200]
                                            + (
                                                "..."
                                                if len(job.get("soft_skills", "")) > 200
                                                else ""
                                            )
                                        )

                                with col3:
                                    if job.get("languages"):
                                        st.markdown("**🗣️ Langues**")
                                        st.caption(job["languages"])

                                st.divider()

                            # Description du poste
                            if job.get("description"):
                                st.markdown("**📝 Description du poste**")
                                st.markdown(
                                    job["description"][:500]
                                    + (
                                        "..."
                                        if len(job.get("description", "")) > 500
                                        else ""
                                    )
                                )

                            # Profil demandé
                            if job.get("job_profile"):
                                st.markdown("**👤 Profil demandé**")
                                st.markdown(
                                    job["job_profile"][:300]
                                    + (
                                        "..."
                                        if len(job.get("job_profile", "")) > 300
                                        else ""
                                    )
                                )

                            st.divider()

                            # Dates et actions
                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                if job.get("date_publication"):
                                    date_pub = job["date_publication"]
                                    if isinstance(date_pub, str):
                                        date_pub = datetime.fromisoformat(
                                            date_pub.replace("Z", "+00:00")
                                        )
                                    st.caption(
                                        f"📅 Pub: {date_pub.strftime('%d/%m/%Y')}"
                                    )

                            with col2:
                                if job.get("date_scraping"):
                                    date_scrap = job["date_scraping"]
                                    if isinstance(date_scrap, str):
                                        date_scrap = datetime.fromisoformat(
                                            date_scrap.replace("Z", "+00:00")
                                        )
                                    st.caption(
                                        f"📥 Ajout: {date_scrap.strftime('%d/%m/%Y')}"
                                    )

                            with col3:
                                st.caption(f"🆔 `{job['id'][:8]}...`")

                            with col4:
                                if job.get("url"):
                                    st.link_button(
                                        "🔗 Voir l'offre",
                                        job["url"],
                                        use_container_width=True,
                                    )

            except Exception as e:
                st.error(f"❌ Erreur lors de la requête: {str(e)}")
