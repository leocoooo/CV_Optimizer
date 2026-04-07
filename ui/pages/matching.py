"""
Page de matching CV avec offres d'emploi.
"""

from __future__ import annotations

import streamlit as st

from ui.components.cards import (
    empty_state,
    hero_banner,
    info_card,
    job_card,
    metric_row,
    section_intro,
    status_message,
    timeline,
)
from ui.components.file_helpers import cv_uploader
from ui.utils.config import DEFAULT_DAYS_LIMIT, DEFAULT_TOP_N, MAX_TOP_N
from ui.utils.formatters import format_datetime, score_badge
from ui.utils.navigation import go_to_page


def render(api_client, api_status: bool) -> None:
    """Affiche la page de matching CV."""
    hero_banner(
        "Transformez un CV en shortlist exploitable.",
        (
            "Chargez un PDF, affinez le périmètre de recherche et obtenez les postes "
            "les plus pertinents pour votre profil sans quitter l'interface."
        ),
        eyebrow="Matching CV",
        pills=["Upload PDF", "Scoring sémantique", "Passerelle vers les conseils IA"],
    )

    left_col, right_col = st.columns([1.45, 1], gap="large")

    with left_col:
        section_intro(
            "Document candidat",
            "Le fichier envoyé est relu par l'API puis comparé aux embeddings de la base.",
        )
        uploaded_file = cv_uploader(key="matching_cv")

    with right_col:
        section_intro(
            "Périmètre d'analyse",
            "Réduisez le bruit si vous ciblez une zone ou un type de contrat précis.",
        )
        top_n = st.slider(
            "Nombre de résultats",
            min_value=5,
            max_value=MAX_TOP_N,
            value=DEFAULT_TOP_N,
        )
        days_limit = st.slider(
            "Offres des N derniers jours",
            min_value=7,
            max_value=365,
            value=DEFAULT_DAYS_LIMIT,
        )
        location = st.text_input("Localisation", placeholder="Paris, Lyon, Remote")
        contract_type = st.text_input("Type de contrat", placeholder="CDI, Stage, Alternance")
        experience = st.selectbox(
            "Expérience",
            ["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"],
        )

        info_card(
            "Ce que fait le moteur",
            "Extraction du texte, recherche vectorielle, filtres optionnels puis tri par score de similarité.",
            tone="sage",
        )

    if st.button(
        "Lancer le matching",
        use_container_width=True,
        disabled=not uploaded_file or not api_status,
    ):
        selected_experience = None if experience == "Tous" else experience[:1]
        with st.spinner("Analyse du CV et recherche des meilleures offres..."):
            try:
                result = api_client.match_cv(
                    file_content=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    top_n=top_n,
                    days_limit=days_limit,
                    location=location or None,
                    contract_type=contract_type or None,
                    experience=selected_experience,
                )
                st.session_state.last_match_result = result
                st.session_state.last_match_error = None
            except Exception as exc:
                st.session_state.last_match_error = str(exc)

    if st.session_state.get("last_match_error"):
        status_message(f"Erreur de matching: {st.session_state['last_match_error']}", "error")

    data = st.session_state.get("last_match_result")
    if not data:
        if not api_status:
            info_card(
                "Matching indisponible",
                "Le service de matching reviendra dès que l'API sera joignable.",
                tone="gold",
            )
            return

        timeline(
            [
                ("Ajoutez un CV", "Le moteur lit le PDF et extrait le texte exploitable."),
                ("Cadrez votre recherche", "Filtrez par fraîcheur, lieu ou type de contrat."),
                ("Analysez les matches", "Passez ensuite une offre prometteuse dans les conseils IA."),
            ]
        )
        return

    status_message(
        f"{data['total_matches']} offres trouvées en {data['execution_time']:.2f}s.",
        "success",
    )
    metric_row(
        [
            {
                "label": "Matches retournés",
                "value": str(data["total_matches"]),
                "detail": "Top résultats renvoyés par l'API",
                "tone": "accent",
            },
            {
                "label": "Taille du CV",
                "value": f"{data['cv_length']:,}".replace(",", " "),
                "detail": "Nombre de caractères exploités",
                "tone": "sage",
            },
            {
                "label": "Temps d'exécution",
                "value": f"{data['execution_time']:.2f}s",
                "detail": "Temps total côté backend",
                "tone": "gold",
            },
        ]
    )

    section_intro(
        "Shortlist recommandée",
        "Chaque résultat peut devenir une cible immédiate pour les conseils IA.",
    )

    if not data["matches"]:
        empty_state(
            "Aucun match exploitable",
            "Essayez d'élargir la période ou de retirer des filtres trop stricts.",
        )
        return

    for index, match in enumerate(data["matches"], start=1):
        label, css_class, interpretation = score_badge(match.get("similarity_score"))
        meta = [
            match.get("location") or "Lieu non précisé",
            match.get("contract_type") or "Contrat non précisé",
            match.get("source") or "Source inconnue",
            format_datetime(match.get("date_publication")),
        ]
        job_card(
            f"#{index} · {match.get('title', 'Offre')}",
            match.get("company", "Entreprise"),
            meta,
            description=interpretation,
            score_label=f"{label} · {match.get('similarity_score', 0):.0%}",
            score_class=css_class,
        )

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            if match.get("url"):
                st.link_button(
                    "Voir l'offre source",
                    match["url"],
                    use_container_width=True,
                )
        with btn_col2:
            if st.button(
                "Envoyer vers les conseils IA",
                key=f"matching_advice_{match['job_id']}",
                use_container_width=True,
            ):
                st.session_state.preselected_job_id = match["job_id"]
                go_to_page("advice")

        with st.expander(f"Lire le contexte du match #{index}"):
            st.markdown(f"**Score**: {match.get('similarity_score', 0):.1%}")
            st.markdown(f"**Lecture**: {interpretation}")
            st.markdown(
                f"**Expérience demandée**: {match.get('required_experience', 'Non renseignée')}"
            )
