"""
Page de pilotage data et administration.
"""

from __future__ import annotations

import requests
import streamlit as st

from ui.components.cards import (
    hero_banner,
    info_card,
    metric_row,
    section_intro,
    status_message,
)
from ui.components.stats_display import display_stats
from ui.utils.formatters import compact_number


def render(api_client, api_status: bool, status_details: dict | None = None) -> None:
    """Affiche la page de pilotage data."""
    hero_banner(
        "Piloter la collecte, l'indexation et la fraîcheur des données.",
        (
            "Cette vue regroupe les actions opératoires et la lecture d'état nécessaire "
            "pour garder la base d'offres exploitable par le matching et le coaching."
        ),
        eyebrow="Pilotage data",
        pills=["Collecte orchestrée", "Réindexation embeddings", "Suivi de la base"],
    )

    health_cols = st.columns(3)
    with health_cols[0]:
        info_card(
            "API",
            "Connectée" if api_status else "Indisponible",
            tone="sage" if api_status else "gold",
        )
    with health_cols[1]:
        database_status = status_details.get("database") if status_details else "Inconnue"
        info_card("Base PostgreSQL", str(database_status), tone="accent")
    with health_cols[2]:
        info_card(
            "Mode d'action",
            "Admin key requise pour collecter et réindexer.",
            tone="gold",
        )

    if "admin_stats" not in st.session_state:
        st.session_state.admin_stats = None

    section_intro(
        "Authentification opérateur",
        "Les actions ci-dessous appellent les endpoints admin protégés du backend.",
    )
    api_key = st.text_input(
        "API key admin",
        type="password",
        help="Valeur attendue dans le header X-API-Key.",
    )

    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:
        section_intro(
            "Collecte d'offres",
            "Préparez un lot de mots-clés puis lancez la collecte API + scraping.",
        )
        keywords_input = st.text_area(
            "Mots-clés",
            value="Data Scientist, Data Engineer, ML Engineer",
            height=130,
            help="Séparez les mots-clés par des virgules.",
        )
        keywords = [item.strip() for item in keywords_input.split(",") if item.strip()]

        controls_a, controls_b = st.columns(2)
        with controls_a:
            max_offers = st.number_input(
                "Max offres / mot-clé / source",
                min_value=1,
                max_value=100,
                value=10,
            )
        with controls_b:
            enable_scraping = st.checkbox(
                "Activer HelloWork + WTTJ",
                value=True,
            )

        sources_count = 1 + (2 if enable_scraping else 0)
        projected_total = len(keywords) * sources_count * int(max_offers)
        metric_row(
            [
                {
                    "label": "Mots-clés",
                    "value": compact_number(len(keywords)),
                    "detail": "Entrées prévues pour la collecte",
                    "tone": "accent",
                },
                {
                    "label": "Sources",
                    "value": compact_number(sources_count),
                    "detail": "API France Travail + scraping optionnel",
                    "tone": "sage",
                },
                {
                    "label": "Volume max",
                    "value": compact_number(projected_total),
                    "detail": "Hors déduplication",
                    "tone": "gold",
                },
            ]
        )

        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button(
                "Lancer la collecte",
                use_container_width=True,
                disabled=not api_key or not keywords or not api_status,
            ):
                with st.spinner("Collecte déclenchée côté backend..."):
                    try:
                        result = api_client.collect_jobs(
                            api_key=api_key,
                            keywords=keywords,
                            max_offers=int(max_offers),
                            enable_scraping=enable_scraping,
                        )
                        status_message(result["message"], "success")
                    except requests.HTTPError as exc:
                        if exc.response.status_code == 403:
                            status_message("API key invalide.", "error")
                        else:
                            status_message(
                                f"Erreur HTTP {exc.response.status_code}: {exc}",
                                "error",
                            )
                    except Exception as exc:
                        status_message(f"Erreur de collecte: {exc}", "error")

        with action_cols[1]:
            if st.button(
                "Réindexer les embeddings",
                use_container_width=True,
                disabled=not api_key or not api_status,
            ):
                with st.spinner("Réindexation déclenchée côté backend..."):
                    try:
                        result = api_client.reindex_embeddings(api_key=api_key)
                        status_message(result["message"], "success")
                    except requests.HTTPError as exc:
                        if exc.response.status_code == 403:
                            status_message("API key invalide.", "error")
                        else:
                            status_message(
                                f"Erreur HTTP {exc.response.status_code}: {exc}",
                                "error",
                            )
                    except Exception as exc:
                        status_message(f"Erreur de réindexation: {exc}", "error")

    with right_col:
        section_intro(
            "Mode opératoire",
            "Rappel des impacts des actions admin sur le reste du produit.",
        )
        info_card(
            "Collecte",
            "Alimente la base depuis France Travail, puis optionnellement via HelloWork et Welcome to the Jungle.",
            tone="accent",
        )
        info_card(
            "Déduplication",
            "Les offres sont filtrées pour éviter les doublons avant l'insertion en base.",
            tone="sage",
        )
        info_card(
            "Embeddings",
            "La réindexation remet la base au niveau pour le matching sémantique.",
            tone="gold",
        )

    st.markdown("")
    section_intro(
        "Statistiques de la base",
        "Le backend admin expose un résumé utile pour vérifier la qualité de la collecte.",
    )

    if st.button(
        "Charger les statistiques admin",
        disabled=not api_key or not api_status,
        use_container_width=True,
    ):
        try:
            st.session_state.admin_stats = api_client.get_stats(api_key=api_key)
        except requests.HTTPError as exc:
            if exc.response.status_code == 403:
                status_message("API key invalide.", "error")
            else:
                status_message(f"Erreur HTTP {exc.response.status_code}: {exc}", "error")
        except Exception as exc:
            status_message(f"Erreur lors du chargement des statistiques: {exc}", "error")

    if st.session_state.admin_stats:
        display_stats(st.session_state.admin_stats)

