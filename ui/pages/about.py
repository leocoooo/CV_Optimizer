"""
Page à propos de l'application.
"""

import streamlit as st
from ui.components.cards import gradient_header, info_card


def render():
    """Affiche la page à propos."""
    gradient_header(
        "ℹ️ À propos de CV-Optimizer",
        "Votre assistant intelligent pour optimiser votre recherche d'emploi",
        gradient="pastel",
    )

    # Fonctionnalités
    info_card("🎯 Fonctionnalités", "", gradient="purple")
    st.markdown("""
    **CV-Optimizer** est une application qui vous aide à optimiser votre recherche d'emploi en utilisant l'IA :

    - **Matching CV** : Trouvez automatiquement les offres les plus pertinentes pour votre profil
    - **Recherche d'offres** : Parcourez et filtrez les offres disponibles
    - **Conseils LLM** : Obtenez des recommandations personnalisées pour améliorer votre CV
    """)

    # Technologies
    info_card("🛠️ Technologies", "", gradient="pink")
    st.markdown("""
    - **Backend** : FastAPI + PostgreSQL + pgvector
    - **Frontend** : Streamlit
    - **Vectorisation** : sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
    - **LLM** : Qwen 2.5 via Hugging Face Inference API
    - **Sources de données** : France Travail API, HelloWork, Welcome to the Jungle
    """)

    # Démarrage rapide
    info_card("🚀 Démarrage rapide", "", gradient="blue")
    st.markdown("""
    1. Assurez-vous que l'API est démarrée :
       ```bash
       uvicorn app.main:app --reload
       ```

    2. Lancez l'application Streamlit :
       ```bash
       streamlit run streamlit_app_new.py
       ```
    """)

    # Documentation
    info_card("📚 Documentation API", "", gradient="yellow")
    st.markdown(
        """
        Consultez la documentation interactive de l'API : 
        [http://localhost:8000/docs](http://localhost:8000/docs)
        """
    )

    st.markdown("---")
    st.info(
        "💡 **Astuce** : Vous pouvez modifier l'URL de l'API dans la barre latérale si elle est hébergée ailleurs."
    )
