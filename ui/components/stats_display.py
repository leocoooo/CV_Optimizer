"""
Composant d'affichage des statistiques.
"""

import streamlit as st
from typing import Dict, Any


def display_stats(stats: Dict[str, Any]):
    """
    Affiche les statistiques de la base de données.

    Args:
        stats: Dictionnaire contenant les statistiques
    """
    col1, col2, col3, col4 = st.columns(4)

    # Statistiques principales
    col1.metric("Total offres", stats.get("total_jobs", 0))

    embeddings_data = stats.get("embeddings", {})
    col2.metric("Avec embeddings", embeddings_data.get("with_embeddings", 0))
    col3.metric("Sans embeddings", embeddings_data.get("without_embeddings", 0))
    col4.metric(
        "Taux d'indexation",
        f"{embeddings_data.get('percentage_indexed', 0):.1f}%",
    )

    # Répartition par source
    if "by_source" in stats:
        st.markdown("---")
        st.markdown("**📊 Répartition par source :**")

        source_cols = st.columns(len(stats["by_source"]))
        for idx, (source, count) in enumerate(stats["by_source"].items()):
            source_cols[idx].metric(source, count)
