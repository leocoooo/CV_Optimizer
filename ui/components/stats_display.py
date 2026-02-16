"""
Composant d'affichage des statistiques.
"""

import streamlit as st
import html
from typing import Dict, Any
from ui.utils.config import GRADIENTS


def display_stats(stats: Dict[str, Any]):
    """
    Affiche les statistiques de la base de données avec des cards colorées.

    Args:
        stats: Dictionnaire contenant les statistiques
    """
    # Statistiques principales avec cards colorées
    col1, col2, col3, col4 = st.columns(4)

    embeddings_data = stats.get("embeddings", {})

    with col1:
        st.markdown(
            f"""
            <div style='background: {GRADIENTS["purple"]}; 
                        padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    Total offres
                </div>
                <div style='color: white; font-size: 2rem; font-weight: 600;'>
                    {stats.get("total_jobs", 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style='background: {GRADIENTS["pink"]}; 
                        padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    Avec embeddings
                </div>
                <div style='color: white; font-size: 2rem; font-weight: 600;'>
                    {embeddings_data.get("with_embeddings", 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style='background: {GRADIENTS["blue"]}; 
                        padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    Sans embeddings
                </div>
                <div style='color: white; font-size: 2rem; font-weight: 600;'>
                    {embeddings_data.get("without_embeddings", 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        percentage = embeddings_data.get("percentage_indexed", 0)
        st.markdown(
            f"""
            <div style='background: {GRADIENTS["yellow"]}; 
                        padding: 1.5rem; border-radius: 12px; text-align: center;'>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                    Taux d'indexation
                </div>
                <div style='color: white; font-size: 2rem; font-weight: 600;'>
                    {percentage:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Répartition par source
    if "by_source" in stats and stats["by_source"]:
        st.markdown("---")
        st.markdown(
            f"""
            <div style='background: {GRADIENTS["dark"]}; 
                        padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
                <h4 style='color: white; margin: 0; border: none;'>📊 Répartition par source</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        source_cols = st.columns(len(stats["by_source"]))
        gradient_list = ["purple", "pink", "blue", "yellow"]

        for idx, (source, count) in enumerate(stats["by_source"].items()):
            gradient_key = gradient_list[idx % len(gradient_list)]
            gradient = GRADIENTS[gradient_key]

            # Sanitize source name to prevent XSS
            safe_source = html.escape(source)

            with source_cols[idx]:
                st.markdown(
                    f"""
                    <div style='background: {gradient}; 
                                padding: 1rem; border-radius: 12px; text-align: center;'>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.85rem; margin-bottom: 0.5rem;'>
                            {safe_source}
                        </div>
                        <div style='color: white; font-size: 1.5rem; font-weight: 600;'>
                            {count}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
