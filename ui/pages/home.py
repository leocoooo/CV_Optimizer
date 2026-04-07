"""
Page d'accueil orientee produit.
"""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from ui.components.cards import (
    empty_state,
    info_card,
    job_card,
    marketing_hero,
    metric_row,
    section_intro,
    status_message,
    tag_cloud,
    timeline,
)
from ui.utils.formatters import (
    compact_number,
    format_datetime,
    format_relative_date,
    friendly_status_label,
)
from ui.utils.navigation import go_to_page


def _labels_from_breakdown(items: Sequence[dict], limit: int = 4) -> list[str]:
    """Construit des tags lisibles depuis une repartition dashboard."""
    return [
        f"{item.get('label', 'Non precise')} · {compact_number(item.get('value', 0))}"
        for item in items[:limit]
        if item.get("label")
    ]


def _offer_description(job: dict) -> str:
    """Construit une phrase courte pour une offre recente."""
    details = [
        value
        for value in (
            job.get("salary"),
            job.get("remote_mode"),
            job.get("required_experience"),
        )
        if value
    ]
    if details:
        return " · ".join(details)
    return "Offre recente prete a analyser dans la plateforme."


def _platform_labels(api_status: bool, status_details: dict | None) -> tuple[str, str]:
    """Retourne des statuts lisibles pour l'accueil."""
    service_label = "Disponible" if api_status else "Indisponible"
    database_label = friendly_status_label(
        status_details.get("database") if status_details else None,
        ok_label="Synchronisee",
        warning_label="A verifier",
    )
    return service_label, database_label


def render(api_client, api_status: bool, status_details: dict | None = None) -> None:
    """Affiche l'accueil principal de CV-Optimizer."""
    marketing_hero(
        eyebrow="Plateforme CV-Optimizer",
        title_lead="Faites passer votre candidature",
        title_highlight="au niveau superieur",
        title_tail=".",
        subtitle=(
            "Explorez le marche, comparez vos competences aux offres cibles et "
            "activez un coach IA pour produire une candidature plus claire, plus convaincante et plus rapide a finaliser grace a l'IA."
        ),
        pills=[
            "Lecture du marche en continu",
            "Matching CV oriente offre",
            "Coach IA actionnable",
        ],
    )

    st.markdown('<div class="marketing-actions-sentinel"></div>', unsafe_allow_html=True)
    action_columns = st.columns([1.1, 1.25, 1.1], gap="medium")
    with action_columns[0]:
        if st.button(
            "Explorer les offres d'emploi",
            key="home_marketing_jobs",
            use_container_width=True,
        ):
            go_to_page("jobs")
    with action_columns[1]:
        if st.button(
            "Lancer un matching",
            key="home_marketing_matching",
            use_container_width=True,
            type="primary",
        ):
            go_to_page("matching")
    with action_columns[2]:
        if st.button(
            "Ouvrir le coach IA",
            key="home_marketing_advice",
            use_container_width=True,
        ):
            go_to_page("advice")

    if not api_status:
        info_card(
            "Mode demonstration",
            (
                "L'interface reste accessible pour presenter le parcours, mais les "
                "donnees en direct reviendront des que la plateforme sera joignable."
            ),
            tone="gold",
        )
        timeline(
            [
                ("Relancer le service", "Demarrez le backend pour reactiver l'exploration et le matching."),
                ("Verifier la base", "Assurez-vous que la source de donnees repond correctement."),
                ("Actualiser la page", "Rechargez l'accueil pour retrouver les indicateurs en direct."),
            ]
        )
        return

    dashboard = None
    try:
        dashboard = api_client.get_dashboard()
    except Exception:
        status_message(
            "Les indicateurs du marche sont temporairement indisponibles.",
            "warning",
        )

    service_label, database_label = _platform_labels(api_status, status_details)
    total_jobs = compact_number(dashboard.get("total_jobs", 0)) if dashboard else "0"
    indexed_jobs = compact_number(dashboard.get("indexed_jobs", 0)) if dashboard else "0"
    indexing_rate = f"{dashboard.get('indexing_rate', 0):.1f}%" if dashboard else "0%"
    active_sources = str(dashboard.get("active_sources", 0)) if dashboard else "0"
    last_ingested_at = dashboard.get("last_ingested_at") if dashboard else None
    freshness = format_relative_date(last_ingested_at) if last_ingested_at else "En attente"

    metric_row(
        [
            {
                "label": "Opportunites actives",
                "value": total_jobs,
                "detail": "Postes deja consultables dans la plateforme",
                "tone": "accent",
            },
            {
                "label": "Base analysable",
                "value": indexed_jobs,
                "detail": "Offres deja exploitables pour le matching",
                "tone": "sage",
            },
            {
                "label": "Couverture IA",
                "value": indexing_rate,
                "detail": "Taux d'indexation pret pour l'analyse",
                "tone": "gold",
            },
            {
                "label": "Derniere actualisation",
                "value": freshness,
                "detail": f"Sources actuellement suivies : {active_sources}",
                "tone": "sage",
            },
        ]
    )

    left_col, right_col = st.columns([1.55, 1], gap="large")

    with left_col:
        section_intro(
            "Un parcours simple pour aller du CV a la candidature ciblee",
            "Chaque etape a ete pensee pour rester lisible et actionnable.",
        )
        timeline(
            [
                (
                    "Importer un CV",
                    "Ajoutez un PDF puis laissez la plateforme extraire le contenu utile.",
                ),
                (
                    "Comparer avec le marche",
                    "Reperez rapidement les offres les plus proches de votre profil.",
                ),
                (
                    "Ajuster la candidature",
                    "Passez dans le coach IA pour retravailler vos messages et vos sections.",
                ),
            ]
        )

        section_intro(
            "Opportunites recentes a suivre",
            "Une selection directe pour passer rapidement a l'analyse ou au coaching.",
        )
        recent_jobs = dashboard.get("recent_jobs", []) if dashboard else []
        if recent_jobs:
            for job in recent_jobs[:3]:
                meta = [
                    job.get("location") or "Lieu non precise",
                    job.get("contract_type") or "Contrat non precise",
                    job.get("source") or "Source non precise",
                    format_relative_date(job.get("date_publication") or job.get("date_scraping")),
                ]
                job_card(
                    job.get("title", "Offre"),
                    job.get("company", "Entreprise"),
                    meta,
                    description=_offer_description(job),
                )
                action_a, action_b = st.columns([1, 1])
                with action_a:
                    if st.button(
                        "Analyser avec le coach IA",
                        key=f"home_advice_{job['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.preselected_job_id = job["id"]
                        go_to_page("advice")
                with action_b:
                    if st.button(
                        "Explorer des offres proches",
                        key=f"home_jobs_{job['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.jobs_prefill_keywords = job.get("title", "")
                        go_to_page("jobs")
        else:
            empty_state(
                "Aucune opportunite recente disponible",
                "Une fois la collecte alimentee, cette zone affichera les offres les plus pertinentes du moment.",
            )

    with right_col:
        section_intro(
            "Vue rapide de la plateforme",
            "L'essentiel du service, presente de facon claire et sans details techniques.",
        )
        info_card(
            "Disponibilite du service",
            (
                f"Plateforme {service_label.lower()} pour l'exploration, le matching et le coach IA.\n"
                f"Base de donnees {database_label.lower()}."
            ),
            tone="sage",
        )

        dynamism_lines = [f"{total_jobs} opportunites accessibles actuellement."]
        if last_ingested_at:
            dynamism_lines.append(
                f"Derniere actualisation : {format_datetime(last_ingested_at, with_time=True)}."
            )
        else:
            dynamism_lines.append("Actualisation des flux en attente.")
        dynamism_lines.append(f"{active_sources} sources sont deja suivies dans la plateforme.")
        info_card("Dynamique du marche", "\n".join(dynamism_lines), tone="accent")

        if dashboard and dashboard.get("top_hard_skills"):
            info_card(
                "Analyse de marche sur les offres d'emploi",
                "Les competences techniques qui ressortent le plus dans les offres deja collectees.",
                tone="accent",
            )
            tag_cloud(_labels_from_breakdown(dashboard["top_hard_skills"], limit=8), tone="accent")

        if dashboard and dashboard.get("source_breakdown"):
            info_card(
                "Sources les plus actives",
                "Les principaux canaux de diffusion deja visibles dans la base.",
                tone="gold",
            )
            tag_cloud(_labels_from_breakdown(dashboard["source_breakdown"]), tone="gold")

        if dashboard and dashboard.get("region_breakdown"):
            info_card(
                "Zones les plus representees",
                "Les bassins d'emploi qui remontent le plus dans les recherches recentes.",
                tone="sage",
            )
            tag_cloud(_labels_from_breakdown(dashboard["region_breakdown"]), tone="sage")

        if dashboard and dashboard.get("contract_breakdown"):
            info_card(
                "Mix des contrats",
                "Un apercu rapide des formats de poste les plus presents.",
                tone="accent",
            )
            tag_cloud(_labels_from_breakdown(dashboard["contract_breakdown"]), tone="accent")

    st.markdown("")
    section_intro(
        "Pourquoi cette version est plus facile a utiliser",
        "Une page d'accueil orientee action, pensee comme une vitrine produit.",
    )
    value_columns = st.columns(3)
    with value_columns[0]:
        info_card(
            "Vision immediate",
            "Reperez en quelques secondes le volume d'opportunites, la fraicheur des donnees et les zones actives.",
            tone="accent",
        )
    with value_columns[1]:
        info_card(
            "Matching plus concret",
            "Passez d'un CV a une shortlist exploitable sans changer d'ecran ni perdre le fil.",
            tone="sage",
        )
    with value_columns[2]:
        info_card(
            "Coaching plus utile",
            "Transformez une offre en cible de candidature avec une aide IA guidee par les competences.",
            tone="gold",
        )

    st.markdown("")
    section_intro(
        "Actions rapides",
        "Choisissez le point d'entree qui correspond a votre besoin du moment.",
    )
    quick_cols = st.columns(3)
    with quick_cols[0]:
        info_card(
            "Matching CV",
            "Ideal pour obtenir une shortlist de postes a partir d'un PDF deja pret.",
            tone="accent",
        )
        if st.button("Ouvrir Matching CV", key="home_nav_matching", use_container_width=True):
            go_to_page("matching")
    with quick_cols[1]:
        info_card(
            "Opportunites",
            "Parfait pour balayer le marche, filtrer les offres et choisir une cible.",
            tone="sage",
        )
        if st.button("Ouvrir les opportunites", key="home_nav_jobs", use_container_width=True):
            go_to_page("jobs")
    with quick_cols[2]:
        info_card(
            "Coach IA",
            "Utile pour retravailler le positionnement, les competences et les formulations du CV.",
            tone="gold",
        )
        if st.button("Ouvrir le coach IA", key="home_nav_advice", use_container_width=True):
            go_to_page("advice")
