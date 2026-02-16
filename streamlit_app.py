"""
Frontend Streamlit pour l'API CV-Optimizer
"""

import streamlit as st
import requests

# Configuration de la page
st.set_page_config(
    page_title="CV-Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# URL de l'API (modifiable)
API_URL = st.sidebar.text_input("URL de l'API", value="http://localhost:8000")

# Titre principal
st.title("📄 CV-Optimizer")
st.markdown("**Trouvez les meilleures offres d'emploi correspondant à votre CV**")

# Sidebar - Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une page",
    [
        "🎯 Matching CV",
        "💼 Recherche d'offres",
        "💡 Conseils LLM",
        "🔧 Admin",
        "ℹ️ À propos",
    ],
)


# Fonction helper pour vérifier la santé de l'API
def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


# Afficher le statut de l'API
api_status = check_api_health()
if api_status:
    st.sidebar.success("✅ API connectée")
else:
    st.sidebar.error("❌ API non disponible")
    st.error("⚠️ L'API n'est pas accessible. Vérifiez que le serveur est démarré.")

# ============================================================================
# PAGE 1: MATCHING CV
# ============================================================================
if page == "🎯 Matching CV":
    st.header("🎯 Matching CV avec offres d'emploi")
    st.markdown("Uploadez votre CV pour trouver les offres les plus pertinentes")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Upload du CV
        uploaded_file = st.file_uploader(
            "Choisir un fichier CV (PDF)",
            type=["pdf"],
            help="Formats acceptés: PDF uniquement",
        )

    with col2:
        # Paramètres de recherche
        st.subheader("Paramètres")
        top_n = st.slider("Nombre de résultats", min_value=5, max_value=50, value=10)
        days_limit = st.slider(
            "Offres des N derniers jours", min_value=7, max_value=365, value=30
        )

        # Filtres optionnels
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

    # Bouton de matching
    if st.button(
        "🔍 Lancer le matching",
        type="primary",
        disabled=not uploaded_file or not api_status,
    ):
        if uploaded_file:
            with st.spinner("Analyse du CV en cours..."):
                try:
                    # Préparer les paramètres
                    params = {"top_n": top_n, "days_limit": days_limit}
                    if location:
                        params["location"] = location
                    if contract_type:
                        params["contract_type"] = contract_type
                    if experience:
                        params["experience"] = experience

                    # Envoyer la requête
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }
                    response = requests.post(
                        f"{API_URL}/api/match", files=files, params=params, timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Afficher les résultats
                        st.success(
                            f"✅ {data['total_matches']} offres trouvées en {data['execution_time']:.2f}s"
                        )

                        # Statistiques
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Offres trouvées", data["total_matches"])
                        col2.metric("Caractères CV", data["cv_length"])
                        col3.metric(
                            "Temps d'exécution", f"{data['execution_time']:.2f}s"
                        )

                        st.markdown("---")

                        # Afficher les offres
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
                                    st.metric(
                                        "Score", f"{match['similarity_score']:.1%}"
                                    )
                                    if match.get("url"):
                                        st.link_button("Voir l'offre", match["url"])

                    else:
                        st.error(f"❌ Erreur: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")

# ============================================================================
# PAGE 2: RECHERCHE D'OFFRES
# ============================================================================
elif page == "💼 Recherche d'offres":
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
            "Offres des N derniers jours", min_value=7, max_value=365, value=30
        )

    # Pagination
    col1, col2 = st.columns([1, 3])
    with col1:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col2:
        page_size = st.slider(
            "Résultats par page", min_value=10, max_value=100, value=20, step=10
        )

    if st.button("🔍 Rechercher", type="primary", disabled=not api_status):
        with st.spinner("Recherche en cours..."):
            try:
                # Préparer les paramètres
                params = {
                    "page": page_num,
                    "page_size": page_size,
                    "days_limit": days_limit,
                }
                if keywords:
                    params["keywords"] = keywords
                if location:
                    params["location"] = location
                if contract_type:
                    params["contract_type"] = contract_type
                if experience:
                    params["experience"] = experience
                if source:
                    params["source"] = source

                # Envoyer la requête
                response = requests.get(
                    f"{API_URL}/api/jobs", params=params, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()

                    # Afficher les statistiques
                    st.success(f"✅ {data['total']} offres trouvées")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total", data["total"])
                    col2.metric("Page", f"{data['page']}/{data['total_pages']}")
                    col3.metric("Résultats", len(data["jobs"]))

                    st.markdown("---")

                    # Afficher les offres
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

                else:
                    st.error(f"❌ Erreur: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"❌ Erreur lors de la requête: {str(e)}")

# ============================================================================
# PAGE 3: CONSEILS LLM
# ============================================================================
elif page == "💡 Conseils LLM":
    st.header("💡 Conseils personnalisés pour votre CV")
    st.markdown(
        "Obtenez des recommandations d'un LLM pour optimiser votre CV par rapport à une offre"
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        # Upload du CV
        uploaded_file = st.file_uploader(
            "Choisir un fichier CV (PDF)",
            type=["pdf"],
            help="Formats acceptés: PDF uniquement",
        )

    with col2:
        # ID de l'offre
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
                    # Envoyer la requête
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }
                    data = {"job_id": job_id}

                    response = requests.post(
                        f"{API_URL}/api/advice", files=files, data=data, timeout=70
                    )

                    if response.status_code == 200:
                        result = response.json()

                        # Afficher les informations
                        st.success(
                            f"✅ Conseils générés en {result['execution_time']:.2f}s"
                        )

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Poste", result["job_title"])
                        col2.metric("Entreprise", result["company"])
                        col3.metric("Modèle LLM", result.get("llm_model", "N/A"))

                        st.markdown("---")

                        # Afficher les conseils
                        st.subheader("📝 Conseils personnalisés")
                        st.markdown(result["advice"])

                    else:
                        st.error(f"❌ Erreur: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"❌ Erreur lors de la requête: {str(e)}")

# ============================================================================
# PAGE 4: ADMIN
# ============================================================================
elif page == "🔧 Admin":
    st.header("🔧 Administration - Collecte de données")
    st.markdown("Lancez la collecte d'offres depuis différentes sources")

    # API Key
    st.subheader("🔑 Authentification")
    api_key = st.text_input(
        "API Key Admin",
        type="password",
        help="Clé API définie dans votre fichier .env (API_KEY_ADMIN)",
    )

    st.markdown("---")

    # Configuration de la collecte
    st.subheader("⚙️ Configuration de la collecte")

    col1, col2 = st.columns(2)

    with col1:
        keywords_input = st.text_area(
            "Mots-clés (séparés par des virgules)",
            value="Data Scientist, Data Engineer, ML Engineer",
            height=150,
            help="Entrez les mots-clés séparés par des virgules",
        )
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

    with col2:
        max_offers = st.number_input(
            "Nombre max d'offres par mot-clé",
            min_value=1,
            max_value=100,
            value=10,
            help="Limite le nombre d'offres collectées par mot-clé",
        )

        enable_scraping = st.checkbox(
            "Activer le web scraping",
            value=True,
            help="Active HelloWork et Welcome to the Jungle (plus lent)",
        )

    # Aperçu
    sources_count = 1 + (2 if enable_scraping else 0)  # API + (HW + WTTJ si scraping)
    total_max = len(keywords) * sources_count * max_offers

    st.info(
        f"📊 Configuration : {len(keywords)} mot(s)-clé × {sources_count} source(s) × {max_offers} offres = ~{total_max} offres max (hors doublons)"
    )

    st.markdown("---")

    # Boutons de collecte
    st.subheader("🚀 Lancer la collecte")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🚀 Collecte Complète (API + Scraping)",
            type="primary",
            disabled=not api_key or not keywords or not api_status,
            help="Collecte depuis toutes les sources : API France Travail + HelloWork + Welcome to the Jungle",
            use_container_width=True,
        ):
            with st.spinner(
                "Collecte complète en cours... (peut prendre plusieurs minutes)"
            ):
                try:
                    headers = {"X-API-Key": api_key}
                    payload = {
                        "keywords": keywords,
                        "max_offers": max_offers,
                        "enable_scraping": enable_scraping,
                    }

                    response = requests.post(
                        f"{API_URL}/api/admin/collect",
                        json=payload,
                        headers=headers,
                        timeout=300,
                    )

                    if response.status_code == 202:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        st.info(
                            "💡 La collecte s'exécute en arrière-plan. Consultez les logs de l'API pour suivre la progression."
                        )
                    elif response.status_code == 403:
                        st.error("❌ API Key invalide")
                    else:
                        st.error(f"❌ Erreur: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

    with col2:
        if st.button(
            "🔄 Réindexer les embeddings",
            type="secondary",
            disabled=not api_key or not api_status,
            help="Régénère les embeddings pour toutes les offres sans embedding",
            use_container_width=True,
        ):
            with st.spinner("Réindexation en cours..."):
                try:
                    headers = {"X-API-Key": api_key}

                    response = requests.post(
                        f"{API_URL}/api/admin/reindex",
                        headers=headers,
                        timeout=300,
                    )

                    if response.status_code == 202:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        st.info("💡 La réindexation s'exécute en arrière-plan.")
                    elif response.status_code == 403:
                        st.error("❌ API Key invalide")
                    else:
                        st.error(f"❌ Erreur: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

    st.markdown("---")

    # Options avancées
    with st.expander("⚙️ Options avancées"):
        hw_icon = "✅" if enable_scraping else "❌"
        hw_status = "Activé" if enable_scraping else "Désactivé"
        wttj_icon = "✅" if enable_scraping else "❌"
        wttj_status = "Activé" if enable_scraping else "Désactivé"

        st.markdown(f"""
        **Sources de collecte :**
        - ✅ **API France Travail** : Toujours activée (officielle, rapide, fiable)
        - {hw_icon} **HelloWork** : {hw_status} (scraping web)
        - {wttj_icon} **Welcome to the Jungle** : {wttj_status} (scraping web)
        
        **Processus de collecte :**
        1. Collecte des offres depuis les sources sélectionnées
        2. Vérification des doublons (par URL)
        3. Insertion en base de données
        4. Génération automatique des embeddings
        
        **Temps estimé :**
        - API seule : ~30s pour 30 offres
        - API + Scraping : ~2-5 min pour 30 offres (selon les sites)
        """)

    st.markdown("---")

    # Statistiques de la base
    st.subheader("📊 Statistiques de la base de données")

    if st.button("🔍 Afficher les stats", disabled=not api_key or not api_status):
        try:
            headers = {"X-API-Key": api_key}
            response = requests.get(
                f"{API_URL}/api/admin/stats", headers=headers, timeout=10
            )

            if response.status_code == 200:
                stats = response.json()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total offres", stats.get("total_jobs", 0))

                # L'API retourne une structure imbriquée pour les embeddings
                embeddings_data = stats.get("embeddings", {})
                col2.metric(
                    "Avec embeddings", embeddings_data.get("with_embeddings", 0)
                )
                col3.metric(
                    "Sans embeddings", embeddings_data.get("without_embeddings", 0)
                )
                col4.metric(
                    "Taux d'indexation",
                    f"{embeddings_data.get('percentage_indexed', 0):.1f}%",
                )

                # Répartition par source
                if "by_source" in stats:
                    st.markdown("**Répartition par source :**")
                    for source, count in stats["by_source"].items():
                        st.write(f"- {source}: {count} offres")

            elif response.status_code == 403:
                st.error("❌ API Key invalide")
            else:
                st.error(f"❌ Erreur: {response.status_code}")

        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")

    st.markdown("---")
    st.warning(
        "⚠️ **Attention** : La collecte peut prendre plusieurs minutes selon le nombre de mots-clés et les sources activées."
    )

# ============================================================================
# PAGE 5: À PROPOS
# ============================================================================
elif page == "ℹ️ À propos":
    st.header("ℹ️ À propos de CV-Optimizer")

    st.markdown("""
    ### 🎯 Fonctionnalités
    
    **CV-Optimizer** est une application qui vous aide à optimiser votre recherche d'emploi en utilisant l'IA :
    
    - **Matching CV** : Trouvez automatiquement les offres les plus pertinentes pour votre profil
    - **Recherche d'offres** : Parcourez et filtrez les offres disponibles
    - **Conseils LLM** : Obtenez des recommandations personnalisées pour améliorer votre CV
    
    ### 🛠️ Technologies
    
    - **Backend** : FastAPI + PostgreSQL + pgvector
    - **Frontend** : Streamlit
    - **Vectorisation** : sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
    - **LLM** : Qwen 2.5 via Hugging Face Inference API
    - **Sources de données** : France Travail API, HelloWork, Welcome to the Jungle
    
    ### 🚀 Démarrage rapide
    
    1. Assurez-vous que l'API est démarrée :
       ```bash
       uvicorn app.main:app --reload
       ```
    
    2. Lancez l'application Streamlit :
       ```bash
       streamlit run streamlit_app.py
       ```
    
    ### 📚 Documentation API
    
    Consultez la documentation interactive de l'API : [http://localhost:8000/docs](http://localhost:8000/docs)
    """)

    st.markdown("---")
    st.info(
        "💡 **Astuce** : Vous pouvez modifier l'URL de l'API dans la barre latérale si elle est hébergée ailleurs."
    )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**CV-Optimizer** v1.0.0")
st.sidebar.markdown("Made with ❤️ using Streamlit")
