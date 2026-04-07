"""
Barre de navigation principale en haut de l'application.
"""

from __future__ import annotations

import streamlit as st

from ui.utils.config import NAV_ITEMS
from ui.utils.formatters import escape_html
from ui.utils.navigation import go_to_page


def render_top_nav(current_page: str, title: str, api_status: bool) -> str:
    """Affiche une navigation sticky avec direction artistique type landing SaaS."""
    clicked_page = None
    mode_label = "Plateforme disponible" if api_status else "Mode demonstration"
    status_class = "live" if api_status else "demo"

    with st.container(border=True):
        st.markdown('<div class="top-nav-sentinel"></div>', unsafe_allow_html=True)
        st.markdown(
            (
                '<div class="utility-strip">'
                '<span class="utility-item">✓ Matching en quelques secondes</span>'
                '<span class="utility-item">✓ Lecture du marche unifiee</span>'
                '<span class="utility-item">✓ Coach IA integre</span>'
                '<span class="utility-item">✓ LM contextuelle</span>'
                '<span class="utility-item utility-rating">★ 5 modules connectes</span>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        shell_cols = st.columns([1.35, 4.1, 1.3], gap="medium")
        with shell_cols[0]:
            st.markdown(
                (
                    '<div class="brand-wordmark">'
                    '<svg class="brand-wordmark-icon" viewBox="0 0 72 72" aria-hidden="true">'
                    '<defs>'
                    '<linearGradient id="cvOptimizerWarm" x1="0%" y1="0%" x2="100%" y2="100%">'
                    '<stop offset="0%" stop-color="#f7d6b8" />'
                    '<stop offset="100%" stop-color="#efc06d" />'
                    '</linearGradient>'
                    '</defs>'
                    '<path d="M16 14h24l16 16v28c0 3.3-2.7 6-6 6H22c-3.3 0-6-2.7-6-6V20c0-3.3 2.7-6 6-6z" fill="url(#cvOptimizerWarm)" stroke="#e48a49" stroke-width="2.2"/>'
                    '<path d="M40 14v12c0 3.3 2.7 6 6 6h10" fill="none" stroke="#e48a49" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
                    '<path d="M25 41c5-8 10-12 15-12 4 0 8 2 10 6" fill="none" stroke="#547d59" stroke-width="3" stroke-linecap="round"/>'
                    '<path d="M28 49h18" fill="none" stroke="#3d4c45" stroke-width="3" stroke-linecap="round"/>'
                    '<circle cx="56" cy="18" r="7" fill="#fff7ee" stroke="#efc06d" stroke-width="2"/>'
                    '<path d="M56 13v10M51 18h10" stroke="#e48a49" stroke-width="2.2" stroke-linecap="round"/>'
                    '</svg>'
                    '<div class="brand-wordmark-copy">'
                    f'<p class="brand-wordmark-title">{escape_html(title)}</p>'
                    '<p class="brand-wordmark-subtitle">Matching, marche et coach IA</p>'
                    "</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        with shell_cols[1]:
            nav_cols = st.columns(len(NAV_ITEMS), gap="small")
            for column, item in zip(nav_cols, NAV_ITEMS):
                with column:
                    if st.button(
                        item.get("nav_label", item["label"]),
                        key=f"sticky_nav_{item['key']}",
                        use_container_width=True,
                        help=item["description"],
                        type="primary" if item["key"] == current_page else "secondary",
                    ):
                        clicked_page = item["key"]

        with shell_cols[2]:
            st.markdown(
                (
                    f'<div class="top-nav-status {status_class}">'
                    f"{escape_html(mode_label)}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            if st.button(
                "Lancer un matching",
                key="top_nav_cta_matching",
                use_container_width=True,
                type="primary",
            ):
                clicked_page = "matching"

    if clicked_page and clicked_page != current_page:
        go_to_page(clicked_page)

    return clicked_page or current_page
