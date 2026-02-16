"""
Page d'administration - Collecte de données.
"""

import streamlit as st
from ui.utils.api_client import APIClient
from ui.components.stats_display import display_stats


def render(api_client: APIClient, api_status: bool):
    """Affiche la page d'administration."""
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
    sources_count = 1 + (2 if enable_scraping else 0)
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
                    data = api_client.collect_jobs(
                        api_key=api_key,
                        keywords=keywords,
                        max_offers=max_offers,
                        enable_scraping=enable_scraping,
                    )

                    st.success(f"✅ {data['message']}")
                    st.info(
                        "💡 La collecte s'exécute en arrière-plan. Consultez les logs de l'API pour suivre la progression."
                    )

                except Exception as e:
                    if "403" in str(e):
                        st.error("❌ API Key invalide")
                    else:
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
                    data = api_client.reindex_embeddings(api_key=api_key)

                    st.success(f"✅ {data['message']}")
                    st.info("💡 La réindexation s'exécute en arrière-plan.")

                except Exception as e:
                    if "403" in str(e):
                        st.error("❌ API Key invalide")
                    else:
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
            stats = api_client.get_stats(api_key=api_key)
            display_stats(stats)

        except Exception as e:
            if "403" in str(e):
                st.error("❌ API Key invalide")
            else:
                st.error(f"❌ Erreur: {str(e)}")

    st.markdown("---")
    st.warning(
        "⚠️ **Attention** : La collecte peut prendre plusieurs minutes selon le nombre de mots-clés et les sources activées."
    )
