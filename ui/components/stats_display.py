"""
Composant d'affichage des statistiques.
"""

from typing import Any

import streamlit as st

from ui.components.cards import info_card, metric_row, section_intro, tag_cloud
from ui.utils.formatters import compact_number, format_datetime


def display_stats(stats: dict[str, Any]) -> None:
    """Affiche les statistiques de la base de données."""
    embeddings = stats.get("embeddings", {})
    section_intro(
        "Photo de la base",
        "Vue consolidée sur le volume, l'indexation et la fraîcheur des données.",
    )

    metric_row(
        [
            {
                "label": "Offres en base",
                "value": compact_number(stats.get("total_jobs", 0)),
                "detail": "Toutes sources confondues",
                "tone": "accent",
            },
            {
                "label": "Vectorisées",
                "value": compact_number(embeddings.get("with_embeddings", 0)),
                "detail": "Embeddings disponibles pour le matching",
                "tone": "sage",
            },
            {
                "label": "À indexer",
                "value": compact_number(embeddings.get("without_embeddings", 0)),
                "detail": "Offres en attente de vectorisation",
                "tone": "gold",
            },
            {
                "label": "Taux d'indexation",
                "value": f"{embeddings.get('percentage_indexed', 0):.1f}%",
                "detail": "Couverture des embeddings",
                "tone": "sage",
            },
        ]
    )

    if stats.get("by_source"):
        info_card(
            "Répartition par source",
            "Le volume collecté permet de suivre la diversité du marché couvert.",
            tone="sage",
        )
        tag_cloud(
            [f"{source} · {count}" for source, count in stats["by_source"].items()],
            tone="accent",
        )

    latest_job = stats.get("latest_job")
    if latest_job:
        st.markdown("")
        info_card(
            "Dernière offre ingérée",
            (
                f"{latest_job.get('title', 'Offre récente')} chez "
                f"{latest_job.get('company', 'Entreprise inconnue')} · "
                f"{format_datetime(latest_job.get('date'), with_time=True)}"
            ),
            tone="gold",
        )
