"""
Page d'administration - Collecte de données.
"""

import streamlit as st
import requests
from ui.utils.api_client import APIClient
from ui.components.stats_display import display_stats
from ui.components.cards import info_card, status_message


def render(api_client: APIClient, api_status: bool):
    """Affiche la page d'administration."""
    st.header("🔧 Administration - Collecte de données")
    st.markdown("Lancez la collecte d'offres depuis différentes sources")

    # API Key
    info_card(
        "🔑 Authentification",
        "Entrez votre clé API admin pour accéder aux fonctionnalités de collecte",
        gradient="purple",
    )
    api_key = st.text_input(
        "API Key Admin",
        type="password",
        help="Clé API définie dans votre fichier .env (API_KEY_ADMIN)",
        label_visibility="collapsed",
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
            "Nombre max d'offres par mot-clé et par source",
            min_value=1,
            max_value=100,
            value=10,
            help="Limite le nombre d'offres collectées",
        )

        enable_scraping = st.checkbox(
            "Activer le web scraping",
            value=True,
            help="Active HelloWork et Welcome to the Jungle (plus lent)",
        )

    # Aperçu avec card stylisée
    sources_count = 1 + (2 if enable_scraping else 0)
    total_max = len(keywords) * sources_count * max_offers

    st.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 12px; margin: 1rem 0;'>
            <h4 style='color: white; margin: 0 0 0.5rem 0; border: none;'>📊 Aperçu de la collecte</h4>
            <p style='color: white; margin: 0; font-size: 1.1rem;'>
                <strong>{len(keywords)}</strong> mot(s)-clé × 
                <strong>{sources_count}</strong> source(s) × 
                <strong>{max_offers}</strong> offres = 
                <strong>~{total_max}</strong> offres max (hors doublons)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Boutons de collecte
    st.subheader("🚀 Lancer la collecte")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🚀 Collecter",
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

                    status_message(f"✅ {data['message']}", "success")
                    st.info(
                        "💡 La collecte s'exécute en arrière-plan (collecte → homogénisation → enrichissement IA → embeddings). "
                        "Consultez les logs de l'API pour suivre la progression."
                    )

                except requests.HTTPError as e:
                    if e.response.status_code == 403:
                        status_message("❌ API Key invalide", "error")
                    else:
                        status_message(
                            f"❌ Erreur HTTP {e.response.status_code}: {str(e)}",
                            "error",
                        )
                except requests.RequestException as e:
                    status_message(f"❌ Erreur de connexion: {str(e)}", "error")
                except Exception as e:
                    status_message(f"❌ Erreur inattendue: {str(e)}", "error")

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

                    status_message(f"✅ {data['message']}", "success")
                    st.info("💡 La réindexation s'exécute en arrière-plan.")

                except requests.HTTPError as e:
                    if e.response.status_code == 403:
                        status_message("❌ API Key invalide", "error")
                    else:
                        status_message(
                            f"❌ Erreur HTTP {e.response.status_code}: {str(e)}",
                            "error",
                        )
                except requests.RequestException as e:
                    status_message(f"❌ Erreur de connexion: {str(e)}", "error")
                except Exception as e:
                    status_message(f"❌ Erreur inattendue: {str(e)}", "error")

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
        4. **Homogénisation des données** (colonnes `cleaned_*` : titres, contrats, localisations normalisés)
        5. **Enrichissement IA** (NER + Classification → colonnes `ai_*` : entités, compétences, missions)
        6. Génération automatique des embeddings

        **Temps estimé :**
        - API seule : ~2-3 min pour 30 offres (avec homogénisation + enrichissement IA)
        - API + Scraping : ~5-10 min pour 30 offres (selon les sites + enrichissement IA)
        """)

    st.markdown("---")

    # Statistiques de la base
    st.subheader("📊 Statistiques de la base de données")

    if st.button("🔍 Afficher les stats", disabled=not api_key or not api_status):
        try:
            stats = api_client.get_stats(api_key=api_key)
            display_stats(stats)

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                status_message("❌ API Key invalide", "error")
            else:
                status_message(
                    f"❌ Erreur HTTP {e.response.status_code}: {str(e)}", "error"
                )
        except requests.RequestException as e:
            status_message(f"❌ Erreur de connexion: {str(e)}", "error")
        except Exception as e:
            status_message(f"❌ Erreur inattendue: {str(e)}", "error")

    st.markdown("---")
    st.warning(
        "⚠️ **Attention** : La collecte peut prendre plusieurs minutes selon le nombre de mots-clés et les sources activées."
    )
