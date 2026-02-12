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
    ["🎯 Matching CV", "💼 Recherche d'offres", "💡 Conseils LLM", "ℹ️ À propos"],
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
# PAGE 4: À PROPOS
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
