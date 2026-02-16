"""
Composants de cards réutilisables pour l'interface.
"""

import streamlit as st


def gradient_header(title: str, subtitle: str, gradient: str = "purple"):
    """
    Affiche un header avec gradient.

    Args:
        title: Titre principal
        subtitle: Sous-titre
        gradient: Type de gradient (purple, pink, blue, yellow, pastel)
    """
    gradients = {
        "purple": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "blue": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "yellow": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "pastel": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        "dark": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
    }

    gradient_css = gradients.get(gradient, gradients["purple"])
    text_color = "white" if gradient != "pastel" else "#333"

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 2rem; border-radius: 12px; margin-bottom: 2rem;'>
            <h1 style='color: {text_color}; margin: 0; border: none;'>{title}</h1>
            <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;'>
                {subtitle}
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
        gradient: Type de gradient
    """
    gradients = {
        "purple": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "blue": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    }

    gradient_css = gradients.get(gradient, gradients["purple"])

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 1.5rem; border-radius: 12px; text-align: center;'>
            <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; margin-bottom: 0.5rem;'>
                {label}
            </div>
            <div style='color: white; font-size: 2rem; font-weight: 600;'>
                {value}
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
        content: Contenu de la card
        gradient: Type de gradient
    """
    gradients = {
        "purple": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "blue": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "yellow": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "dark": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)",
    }

    gradient_css = gradients.get(gradient, gradients["purple"])

    st.markdown(
        f"""
        <div style='background: {gradient_css}; 
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; border: none;'>{title}</h3>
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
    st.markdown(
        f"""
        <div class='status-badge status-{status}' style='padding: 1rem; font-size: 1rem; margin: 1rem 0;'>
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )
