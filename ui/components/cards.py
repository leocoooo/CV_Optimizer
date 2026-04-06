"""
Composants de cards réutilisables pour l'interface.
"""

import streamlit as st
import html
from ui.utils.config import GRADIENTS


def gradient_header(title: str, subtitle: str, gradient: str = "purple"):
    """
    Affiche un header avec gradient.

    Args:
        title: Titre principal
        subtitle: Sous-titre
        gradient: Type de gradient (purple, pink, blue, yellow, pastel, dark)
    """
    gradient_css = GRADIENTS.get(gradient, GRADIENTS["purple"])
    text_color = "white" if gradient != "pastel" else "#333"

    # Sanitize user inputs to prevent XSS
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)

    subtitle_color = (
        "rgba(255,255,255,0.9)" if gradient != "pastel" else "rgba(51,51,51,0.85)"
    )

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 2rem; border-radius: 12px; margin-bottom: 2rem;'>
            <h1 style='color: {text_color}; margin: 0; border: none;'>{safe_title}</h1>
            <p style='color: {subtitle_color}; margin: 0.5rem 0 0 0; font-size: 1.1rem;'>
                {safe_subtitle}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, gradient: str = "purple"):
    """
    Affiche une métrique dans une card colorée.

    Args:
        label: Label de la métrique
        value: Valeur à afficher
        gradient: Type de gradient (purple, pink, blue, yellow, pastel, dark)
    """
    gradient_css = GRADIENTS.get(gradient, GRADIENTS["purple"])

    # Sanitize user inputs to prevent XSS
    safe_label = html.escape(label)
    safe_value = html.escape(value)

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 1.5rem; border-radius: 12px; text-align: center;'>
            <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                {safe_label}
            </div>
            <div style='color: white; font-size: 2rem; font-weight: 600;'>
                {safe_value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, content: str, gradient: str = "purple"):
    """
    Affiche une card d'information avec titre et contenu.

    Args:
        title: Titre de la card
        content: Contenu de la card (peut être vide)
        gradient: Type de gradient (purple, pink, blue, yellow, pastel, dark)
    """
    gradient_css = GRADIENTS.get(gradient, GRADIENTS["purple"])

    # Sanitize user input to prevent XSS
    safe_title = html.escape(title)

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; border: none;'>{safe_title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_message(message: str, status: str = "success"):
    """
    Affiche un message de statut stylisé.

    Args:
        message: Message à afficher
        status: Type de statut (success, error, warning)
    """
    # Sanitize user input to prevent XSS
    safe_message = html.escape(message)

    st.markdown(
        f"""
        <div class='status-badge status-{status}' style='padding: 1rem; font-size: 1rem; margin: 1rem 0;'>
            {safe_message}
        </div>
        """,
        unsafe_allow_html=True,
    )
