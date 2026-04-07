"""
Page d'architecture et de cadrage du projet.
"""

from __future__ import annotations

import streamlit as st

from ui.components.cards import hero_banner, info_card, section_intro, tag_cloud, timeline


def render() -> None:
    """Affiche la page d'architecture."""
    hero_banner(
        "Une structure de projet lisible, avec des responsabilités bien séparées.",
        (
            "Le but de cette refonte est de clarifier le rôle de chaque couche: "
            "API et données dans `app/`, traitements dans `src/`, expérience utilisateur dans `ui/`."
        ),
        eyebrow="Architecture CV-Optimizer",
        pills=["FastAPI", "PostgreSQL + pgvector", "Streamlit", "Documentation tickets"],
    )

    section_intro(
        "Règle directrice",
        "Les données et endpoints vivent dans l'API, l'interface et le design vivent dans `ui`.",
    )
    timeline(
        [
            (
                "1. `app/`",
                "Expose les routes FastAPI, les schémas Pydantic, la sécurité et l'agrégation dashboard.",
            ),
            (
                "2. `src/`",
                "Contient la collecte, la vectorisation, le matching, le reader PDF et le LLM advisor.",
            ),
            (
                "3. `ui/`",
                "Gère le thème, les composants, la navigation, les pages et les interactions utilisateur.",
            ),
            (
                "4. `doc/`",
                "Trace les tickets de refonte, ce qui a été fait et la manière dont cela a été réalisé.",
            ),
        ]
    )

    grid = st.columns(3)
    with grid[0]:
        info_card(
            "Parcours candidat",
            "Cockpit d'accueil, matching CV, exploration d'offres et conseils IA reliés entre eux.",
            tone="accent",
        )
    with grid[1]:
        info_card(
            "Parcours opérateur",
            "Vue dédiée pour la collecte, la réindexation et la lecture des statistiques de la base.",
            tone="sage",
        )
    with grid[2]:
        info_card(
            "Flux de données",
            "L'interface consomme l'API publique et les routes admin sans déplacer la logique métier vers le frontend.",
            tone="gold",
        )

    section_intro(
        "Technologies déjà en place",
        "La nouvelle interface respecte la stack existante du projet.",
    )
    tag_cloud(
        [
            "FastAPI",
            "SQLAlchemy",
            "PostgreSQL",
            "pgvector",
            "Sentence Transformers",
            "Hugging Face Inference",
            "Streamlit",
        ],
        tone="sage",
    )

    section_intro(
        "Bénéfices de la refonte",
        "La navigation devient plus lisible et chaque page raconte mieux ce qu'elle permet de faire.",
    )
    info_card(
        "Lecture produit",
        "L'accueil sert désormais de cockpit. Les autres vues sont orientées tâches plutôt que simples formulaires isolés.",
        tone="accent",
    )
    info_card(
        "Intégration des usages",
        "Depuis une recherche ou un match, on peut désormais basculer vers les conseils IA avec un job présélectionné.",
        tone="sage",
    )
    info_card(
        "Traçabilité",
        "Le dossier `doc/` sert de journal de tickets pour comprendre ce qui a été modifié et pourquoi.",
        tone="gold",
    )
