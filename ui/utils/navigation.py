"""
Helpers de navigation entre les vues Streamlit.
"""

from __future__ import annotations

import streamlit as st

from ui.utils.config import NAV_ITEMS


def _page_options() -> list[str]:
    """Retourne les pages autorisees."""
    return [item["key"] for item in NAV_ITEMS]


def normalize_page(page_key: str | None) -> str:
    """Valide une page et retourne un fallback si besoin."""
    options = _page_options()
    if page_key in options:
        return str(page_key)
    return "home"


def sync_page_state() -> str:
    """Synchronise simplement la page active avec la session."""
    current_page = normalize_page(st.session_state.get("current_page"))
    st.session_state.current_page = current_page
    return current_page


def go_to_page(page_key: str) -> None:
    """Navigue vers une autre vue dans la meme application."""
    st.session_state.current_page = normalize_page(page_key)
    st.rerun()
