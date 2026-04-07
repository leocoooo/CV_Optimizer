"""
Page de recherche et d'exploration des offres.
"""

from __future__ import annotations

import streamlit as st

from ui.components.cards import (
    empty_state,
    hero_banner,
    info_card,
    metric_row,
    section_intro,
    status_message,
)
from ui.utils.config import DEFAULT_DAYS_LIMIT, DEFAULT_PAGE_SIZE
from ui.utils.formatters import compact_number, format_datetime, split_csv, truncate
from ui.utils.navigation import go_to_page


def _default_job_filters() -> dict[str, str | int]:
    return {
        "keywords": st.session_state.get("jobs_prefill_keywords", ""),
        "location": "",
        "contract_type": "",
        "experience": "Tous",
        "source": "Toutes",
        "sector": "",
        "remote_mode": "",
        "company": "",
        "required_education": "",
        "page": 1,
        "page_size": DEFAULT_PAGE_SIZE,
        "days_limit": DEFAULT_DAYS_LIMIT,
    }


def _run_search(api_client, filters: dict[str, str | int]) -> tuple[dict | None, str | None]:
    experience = filters["experience"]
    if experience == "Tous":
        experience = None
    elif isinstance(experience, str):
        experience = experience[:1]

    source = filters["source"]
    if source == "Toutes":
        source = None

    try:
        data = api_client.search_jobs(
            page=int(filters["page"]),
            page_size=int(filters["page_size"]),
            keywords=str(filters["keywords"]).strip() or None,
            location=str(filters["location"]).strip() or None,
            contract_type=str(filters["contract_type"]).strip() or None,
            experience=experience,
            source=source,
            sector=str(filters["sector"]).strip() or None,
            remote_mode=str(filters["remote_mode"]).strip() or None,
            company=str(filters["company"]).strip() or None,
            required_education=str(filters["required_education"]).strip() or None,
            days_limit=int(filters["days_limit"]),
        )
        return data, None
    except Exception as exc:
        return None, str(exc)


def _render_job_result(job: dict) -> None:
    """Affiche une offre en layout natif Streamlit."""
    meta = [
        job.get("location") or "Lieu non precise",
        job.get("contract_type") or "Contrat non precise",
        job.get("source") or "Source inconnue",
        format_datetime(job.get("date_publication")),
    ]
    tags = (
        split_csv(job.get("hard_skills"))
        + split_csv(job.get("soft_skills"), limit=3)
        + split_csv(job.get("languages"), limit=2)
    )

    with st.container(border=True):
        summary_col, action_col = st.columns([1.55, 0.85], gap="large")

        with summary_col:
            st.caption(job.get("company", "Entreprise"))
            st.markdown(f"#### {job.get('title', 'Offre')}")
            st.caption(" · ".join(item for item in meta if item))

            description = truncate(job.get("description"), limit=240)
            if description:
                st.write(description)

            if tags:
                st.caption("Competences reperees")
                st.write(" · ".join(tags[:8]))

        with action_col:
            st.caption("Actions")
            if job.get("url"):
                st.link_button(
                    "Voir l'offre source",
                    job["url"],
                    use_container_width=True,
                )
            if st.button(
                "Analyser avec le coach IA",
                key=f"jobs_advice_{job['id']}",
                use_container_width=True,
            ):
                st.session_state.preselected_job_id = job["id"]
                go_to_page("advice")

        with st.expander(f"Details de l'offre · {job['id']}"):
            detail_col1, detail_col2 = st.columns([1.35, 1], gap="large")
            with detail_col1:
                st.markdown(f"**Entreprise**: {job.get('company', 'Non renseignee')}")
                st.markdown(f"**Localisation**: {job.get('location', 'Non renseignee')}")
                st.markdown(f"**Teletravail**: {job.get('remote_mode', 'Non renseigne')}")
                st.markdown(f"**Salaire**: {job.get('salary', 'Non renseigne')}")
                st.markdown(
                    f"**Experience**: {job.get('required_experience', 'Non renseignee')}"
                )
                st.markdown(
                    f"**Etudes**: {job.get('required_education', 'Non renseigne')}"
                )
                st.markdown(f"**Publication**: {format_datetime(job.get('date_publication'))}")

            with detail_col2:
                st.markdown("**Source et actions**")
                st.write(job.get("source") or "Source inconnue")
                if job.get("url"):
                    st.link_button(
                        "Ouvrir la fiche source",
                        job["url"],
                        use_container_width=True,
                    )
                if st.button(
                    "Envoyer au coach IA",
                    key=f"jobs_advice_detail_{job['id']}",
                    use_container_width=True,
                ):
                    st.session_state.preselected_job_id = job["id"]
                    go_to_page("advice")

            st.markdown("**Description**")
            st.write(job.get("description", "Description indisponible"))


def render(api_client, api_status: bool) -> None:
    """Affiche la page Explorer."""
    hero_banner(
        "Explorer les offres avec une lecture plus claire du marché.",
        (
            "Filtres avancés, résultats mieux hiérarchisés et passerelles directes "
            "vers le coaching IA pour transformer une offre en cible de candidature."
        ),
        eyebrow="Explorer le marché",
        pills=["Filtres structurés", "Lecture rapide des signaux", "Pont direct vers les conseils IA"],
    )

    if "jobs_filters" not in st.session_state:
        st.session_state.jobs_filters = _default_job_filters()
    prefill_keywords = st.session_state.pop("jobs_prefill_keywords", None)
    if prefill_keywords:
        st.session_state.jobs_filters["keywords"] = prefill_keywords
    if "jobs_results" not in st.session_state and api_status:
        data, error = _run_search(api_client, st.session_state.jobs_filters)
        if data:
            st.session_state.jobs_results = data
        elif error:
            st.session_state.jobs_error = error

    filters = st.session_state.jobs_filters

    with st.form("jobs_search_form"):
        section_intro(
            "Filtres de recherche",
            "Gardez une recherche large ou resserrez progressivement le marché.",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            keywords = st.text_input("Mots-clés", value=str(filters["keywords"]))
            location = st.text_input("Localisation", value=str(filters["location"]))
            sector = st.text_input("Secteur", value=str(filters["sector"]))
        with col2:
            contract_type = st.text_input(
                "Type de contrat", value=str(filters["contract_type"])
            )
            experience = st.selectbox(
                "Niveau d'expérience",
                ["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"],
                index=["Tous", "D (Débutant)", "E (Expérimenté)", "S (Senior)"].index(
                    str(filters["experience"])
                ),
            )
            remote_mode = st.text_input(
                "Télétravail", value=str(filters["remote_mode"])
            )
        with col3:
            source = st.selectbox(
                "Source",
                ["Toutes", "France Travail", "HelloWork", "Welcome to the Jungle"],
                index=[
                    "Toutes",
                    "France Travail",
                    "HelloWork",
                    "Welcome to the Jungle",
                ].index(str(filters["source"])),
            )
            company = st.text_input("Entreprise", value=str(filters["company"]))
            required_education = st.text_input(
                "Études requises", value=str(filters["required_education"])
            )

        page_col, size_col, days_col = st.columns([1, 1, 2])
        with page_col:
            page = st.number_input("Page", min_value=1, value=int(filters["page"]))
        with size_col:
            page_size = st.selectbox(
                "Résultats / page",
                [12, 24, 36, 48],
                index=[12, 24, 36, 48].index(int(filters["page_size"])),
            )
        with days_col:
            days_limit = st.slider(
                "Offres des N derniers jours",
                min_value=7,
                max_value=365,
                value=int(filters["days_limit"]),
            )

        submit = st.form_submit_button(
            "Actualiser l'exploration",
            use_container_width=True,
            disabled=not api_status,
        )

    if submit and api_status:
        st.session_state.jobs_filters = {
            "keywords": keywords,
            "location": location,
            "contract_type": contract_type,
            "experience": experience,
            "source": source,
            "sector": sector,
            "remote_mode": remote_mode,
            "company": company,
            "required_education": required_education,
            "page": int(page),
            "page_size": int(page_size),
            "days_limit": int(days_limit),
        }
        with st.spinner("Exploration des offres en cours..."):
            data, error = _run_search(api_client, st.session_state.jobs_filters)
        if data:
            st.session_state.jobs_results = data
            st.session_state.jobs_error = None
        else:
            st.session_state.jobs_error = error
    elif prefill_keywords and api_status:
        with st.spinner("Chargement des offres liées au contexte sélectionné..."):
            data, error = _run_search(api_client, st.session_state.jobs_filters)
        if data:
            st.session_state.jobs_results = data
            st.session_state.jobs_error = None
        else:
            st.session_state.jobs_error = error

    if not api_status:
        info_card(
            "Exploration indisponible",
            "La recherche sera réactivée dès que l'API pourra répondre aux appels `/api/jobs`.",
            tone="gold",
        )
        return

    if st.session_state.get("jobs_error"):
        status_message(f"Erreur API: {st.session_state['jobs_error']}", "error")

    data = st.session_state.get("jobs_results")
    if not data:
        empty_state(
            "Aucun résultat chargé",
            "Lancez une recherche pour voir remonter les offres disponibles dans la base.",
        )
        return

    status_message(f"{data['total']} offres correspondent aux filtres actifs.", "success")
    metric_row(
        [
            {
                "label": "Résultats trouvés",
                "value": compact_number(data["total"]),
                "detail": "Volume total correspondant",
                "tone": "accent",
            },
            {
                "label": "Page courante",
                "value": f"{data['page']} / {max(data['total_pages'], 1)}",
                "detail": "Pagination active",
                "tone": "sage",
            },
            {
                "label": "Fenêtre temporelle",
                "value": f"{st.session_state.jobs_filters['days_limit']} jours",
                "detail": "Période d'exploration",
                "tone": "gold",
            },
        ]
    )

    active_tags = []
    for key in [
        "keywords",
        "location",
        "contract_type",
        "sector",
        "remote_mode",
        "company",
        "required_education",
    ]:
        value = st.session_state.jobs_filters.get(key)
        if value:
            active_tags.append(f"{key.replace('_', ' ')}: {value}")
    if str(st.session_state.jobs_filters.get("experience")) != "Tous":
        active_tags.append(f"expérience: {st.session_state.jobs_filters['experience']}")
    if str(st.session_state.jobs_filters.get("source")) != "Toutes":
        active_tags.append(f"source: {st.session_state.jobs_filters['source']}")

    if active_tags:
        section_intro("Filtres actifs", "Les critères actuellement appliqués à la base.")
        st.caption(" · ".join(active_tags))

    section_intro(
        "Résultats",
        "Chaque carte peut être utilisée comme point d'entrée vers un matching ciblé ou un diagnostic IA.",
    )

    if data["total"] == 0:
        empty_state(
            "Aucune offre trouvée",
            "Élargissez la période ou retirez quelques filtres pour retrouver plus de volume.",
        )
        return

    for job in data["jobs"]:
        _render_job_result(job)
        st.markdown("")
