"""
Page de conseils LLM personnalisés.
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
    tag_cloud,
    timeline,
)
from ui.components.file_helpers import cv_uploader
from ui.utils.formatters import build_job_label, format_datetime, truncate


def _resolve_selected_job(api_client, selected_job_id: str | None) -> dict | None:
    if not selected_job_id:
        return None
    cache = st.session_state.setdefault("advice_job_cache", {})
    if selected_job_id in cache:
        return cache[selected_job_id]

    try:
        details = api_client.get_job_details(selected_job_id)
        cache[selected_job_id] = details
        return details
    except Exception:
        return None


def render(api_client, api_status: bool) -> None:
    """Affiche la page de conseils LLM."""
    hero_banner(
        "Obtenir un diagnostic IA sur un couple CV + offre ciblée.",
        (
            "Choisissez une offre provenant soit du matching soit de l'exploration, "
            "ajoutez votre CV puis laissez le LLM proposer les axes d'amélioration les plus utiles."
        ),
        eyebrow="Conseils IA",
        pills=["Sélection d'offre assistée", "CV PDF", "Conseils directement exploitables"],
    )

    selected_job_id = st.session_state.get("preselected_job_id")
    if "advice_job_candidates" not in st.session_state:
        st.session_state.advice_job_candidates = []
    if "llm_chat_messages" not in st.session_state:
        st.session_state.llm_chat_messages = []

    if st.session_state.get("llm_chat_job_id") != selected_job_id:
        st.session_state.llm_chat_job_id = selected_job_id
        st.session_state.llm_chat_messages = []
        st.session_state.llm_chat_error = None

    search_col, preview_col = st.columns([1.2, 1], gap="large")

    with search_col:
        section_intro(
            "Trouver une offre cible",
            "Cherchez un poste depuis la base ou utilisez un job déjà sélectionné depuis une autre vue.",
        )
        advice_keywords = st.text_input(
            "Mots-clés de l'offre",
            value=st.session_state.get("advice_keywords", ""),
            placeholder="Data engineer, ML engineer, analyste BI...",
        )
        advice_location = st.text_input(
            "Localisation (optionnelle)",
            value=st.session_state.get("advice_location", ""),
            placeholder="Paris, Remote, Lyon...",
        )

        if st.button("Rechercher des offres cibles", use_container_width=True, disabled=not api_status):
            st.session_state.advice_keywords = advice_keywords
            st.session_state.advice_location = advice_location
            with st.spinner("Recherche d'offres compatibles..."):
                try:
                    search_result = api_client.search_jobs(
                        keywords=advice_keywords or None,
                        location=advice_location or None,
                        page_size=12,
                        days_limit=60,
                    )
                    st.session_state.advice_job_candidates = search_result.get("jobs", [])
                    st.session_state.advice_error = None
                except Exception as exc:
                    st.session_state.advice_job_candidates = []
                    st.session_state.advice_error = str(exc)

        candidates = st.session_state.get("advice_job_candidates", [])
        if candidates:
            options = {build_job_label(job): job["id"] for job in candidates}
            default_label = next(
                (label for label, job_id in options.items() if job_id == selected_job_id),
                next(iter(options)),
            )
            selected_label = st.selectbox(
                "Offre sélectionnée",
                list(options.keys()),
                index=list(options.keys()).index(default_label),
            )
            selected_job_id = options[selected_label]
            st.session_state.preselected_job_id = selected_job_id
        elif selected_job_id:
            info_card(
                "Offre déjà présélectionnée",
                f"Le job `{selected_job_id}` a été transmis depuis une autre page.",
                tone="gold",
            )
        else:
            empty_state(
                "Aucune offre cible chargée",
                "Utilisez la recherche ci-dessus ou passez par le matching / l'exploration pour préremplir cette vue.",
            )

        with st.expander("Entrer un ID manuellement"):
            manual_job_id = st.text_input("ID d'offre", value=selected_job_id or "")
            if st.button("Utiliser cet ID", key="manual_job_id_btn", use_container_width=True):
                st.session_state.preselected_job_id = manual_job_id.strip() or None
                selected_job_id = st.session_state.preselected_job_id

    with preview_col:
        section_intro(
            "Offre actuellement ciblée",
            "Le contexte métier affiché ici sert de point de départ avant l'analyse LLM.",
        )
        selected_job = _resolve_selected_job(api_client, selected_job_id) if api_status else None
        if selected_job:
            info_card(
                selected_job.get("title", "Offre"),
                (
                    f"{selected_job.get('company', 'Entreprise inconnue')}\n"
                    f"{selected_job.get('location', 'Lieu non renseigné')} · "
                    f"{selected_job.get('contract_type', 'Contrat non renseigné')} · "
                    f"{format_datetime(selected_job.get('date_publication'))}"
                ),
                tone="sage",
            )
            if selected_job.get("salary") or selected_job.get("remote_mode"):
                info_card(
                    "Contexte de l'offre",
                    (
                        f"Salaire: {selected_job.get('salary', 'Non renseigné')}\n"
                        f"Télétravail: {selected_job.get('remote_mode', 'Non renseigné')}"
                    ),
                    tone="gold",
                )
            st.caption(truncate(selected_job.get("description"), limit=220))
        else:
            timeline(
                [
                    ("Choisir une offre", "Depuis la recherche ou le matching."),
                    ("Déposer le CV", "Le backend extrait le texte du PDF."),
                    ("Lancer le coaching", "Le LLM produit des conseils directement actionnables."),
                ]
            )

    if st.session_state.get("advice_error"):
        status_message(f"Recherche d'offres impossible: {st.session_state['advice_error']}", "error")

    st.markdown("")
    section_intro(
        "Document candidat",
        "Ajoutez maintenant le CV à comparer avec l'offre sélectionnée.",
    )
    uploaded_file = cv_uploader(key="advice_cv")
    current_cv_signature = None
    if uploaded_file:
        current_cv_signature = (
            f"{uploaded_file.name}:{len(uploaded_file.getvalue())}"
        )

    previous_cv_signature = st.session_state.get("advice_cv_signature")
    if current_cv_signature != previous_cv_signature:
        st.session_state.advice_cv_signature = current_cv_signature
        st.session_state.last_skill_comparison = None
        st.session_state.last_skill_comparison_error = None
        st.session_state.last_advice_result = None
        st.session_state.last_advice_error = None
        st.session_state.llm_chat_messages = []
        st.session_state.llm_chat_error = None

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button(
            "Comparer les compétences",
            use_container_width=True,
            disabled=not uploaded_file or not selected_job_id or not api_status,
        ):
            with st.spinner("Comparaison des compétences en cours..."):
                try:
                    comparison = api_client.compare_skills(
                        file_content=uploaded_file.getvalue(),
                        filename=uploaded_file.name,
                        job_id=selected_job_id,
                    )
                    st.session_state.last_skill_comparison = comparison
                    st.session_state.last_skill_comparison_error = None
                except Exception as exc:
                    st.session_state.last_skill_comparison_error = str(exc)

    with action_col2:
        if st.button(
            "Générer les conseils IA",
            use_container_width=True,
            disabled=not uploaded_file or not selected_job_id or not api_status,
        ):
            with st.spinner("Le LLM prépare ses recommandations..."):
                try:
                    result = api_client.get_advice(
                        file_content=uploaded_file.getvalue(),
                        filename=uploaded_file.name,
                        job_id=selected_job_id,
                    )
                    st.session_state.last_advice_result = result
                    st.session_state.last_advice_error = None
                except Exception as exc:
                    st.session_state.last_advice_error = str(exc)

    if st.session_state.get("last_skill_comparison_error"):
        status_message(
            f"Erreur de comparaison: {st.session_state['last_skill_comparison_error']}",
            "error",
        )

    comparison = st.session_state.get("last_skill_comparison")
    if comparison and selected_job_id and comparison.get("job_id") != selected_job_id:
        comparison = None
    if comparison:
        status_message(
            (
                f"Comparaison chargée pour {comparison['job_title']} avec un score "
                f"d'alignement de {comparison['overall_score']:.1f}%."
            ),
            "success",
        )
        metric_row(
            [
                {
                    "label": "Score d'alignement",
                    "value": f"{comparison['overall_score']:.1f}%",
                    "detail": comparison["fit_label"],
                    "tone": "accent",
                },
                {
                    "label": "Compétences couvertes",
                    "value": str(comparison["matched_count"]),
                    "detail": "Demandées et visibles dans le CV",
                    "tone": "sage",
                },
                {
                    "label": "À renforcer",
                    "value": str(comparison["missing_count"]),
                    "detail": "Demandées mais non visibles",
                    "tone": "gold",
                },
                {
                    "label": "Atouts bonus",
                    "value": str(comparison["bonus_count"]),
                    "detail": "Compétences additionnelles détectées",
                    "tone": "sage",
                },
            ]
        )

        section_intro(
            "Comparaison compétences",
            "Lecture de ce qui est bien visible dans le CV et de ce qui reste à renforcer.",
        )
        info_card("Synthèse", comparison["summary"], tone="accent")

        signal_col, watch_col = st.columns(2, gap="large")
        with signal_col:
            section_intro("Ce qui est bien", "Les signaux positifs repérés dans le CV.")
            if comparison.get("positive_signals"):
                for item in comparison["positive_signals"]:
                    st.markdown(f"- {item}")
            else:
                empty_state(
                    "Pas encore de signal fort",
                    "Le CV ne fait pas encore ressortir de points d'alignement clairs.",
                )

        with watch_col:
            section_intro(
                "Ce qui est à renforcer",
                "Les points qui paraissent manquants ou peu visibles.",
            )
            if comparison.get("watchouts"):
                for item in comparison["watchouts"]:
                    st.markdown(f"- {item}")
            else:
                empty_state(
                    "Pas d'alerte majeure",
                    "Aucun manque saillant n'a été détecté sur cette comparaison.",
                )

        section_intro(
            "Détail par catégorie",
            "Les compétences demandées sont regroupées pour mieux voir les écarts.",
        )
        for group in comparison.get("groups", []):
            with st.expander(group["label"], expanded=True):
                info_card(
                    group["label"],
                    f"{len(group['matched'])}/{len(group['required'])} compétence(s) demandée(s) visibles dans le CV.",
                    tone="sage",
                )
                st.markdown("**Demandées dans l'offre**")
                if group.get("required"):
                    tag_cloud(group["required"], tone="gold")
                else:
                    st.caption(
                        "Aucune compétence structurée détectée dans cette catégorie."
                    )

                st.markdown("**Déjà visibles dans le CV**")
                if group.get("matched"):
                    tag_cloud(group["matched"], tone="sage")
                else:
                    st.caption("Aucun signal repéré dans le CV pour cette catégorie.")

                st.markdown("**À expliciter ou renforcer**")
                if group.get("missing"):
                    tag_cloud(group["missing"], tone="accent")
                else:
                    st.caption("Aucun manque détecté dans cette catégorie.")

        if comparison.get("bonus_skills"):
            section_intro(
                "Compétences bonus du candidat",
                "Atouts visibles dans le CV même lorsqu'ils ne sont pas explicitement demandés.",
            )
            tag_cloud(comparison["bonus_skills"], tone="sage")

        if comparison.get("detected_candidate_skills"):
            with st.expander("Compétences détectées dans le CV"):
                tag_cloud(comparison["detected_candidate_skills"], tone="gold")

    if st.session_state.get("last_advice_error"):
        status_message(f"Erreur de génération: {st.session_state['last_advice_error']}", "error")

    result = st.session_state.get("last_advice_result")
    if result and selected_job_id and result.get("job_id") != selected_job_id:
        result = None
    if result:
        status_message(
            f"Conseils générés en {result['execution_time']:.2f}s pour {result['job_title']}.",
            "success",
        )
        metric_row(
            [
                {
                    "label": "Poste visé",
                    "value": truncate(result["job_title"], limit=26),
                    "detail": result["company"],
                    "tone": "accent",
                },
                {
                    "label": "Taille du CV",
                    "value": f"{result['cv_length']:,}".replace(",", " "),
                    "detail": "Caractères analysés",
                    "tone": "sage",
                },
                {
                    "label": "Modèle LLM",
                    "value": result.get("llm_model", "N/A"),
                    "detail": "Service de recommandation utilisé",
                    "tone": "gold",
                },
            ]
        )

        section_intro(
            "Restitution",
            "Les conseils ci-dessous viennent directement de l'endpoint `/api/advice`.",
        )
        st.markdown(result["advice"])
    else:
        info_card(
            "Conseils IA non générés",
            "Le chat reste disponible même sans lancer la restitution complète.",
            tone="sage",
        )

    st.markdown("")
    section_intro(
        "Chat avec le coach LLM",
        "Discutez directement des modifications que vous voulez apporter au CV pour cette offre.",
    )
    info_card(
        "Utilisation recommandée",
        (
            "Demandez par exemple une nouvelle accroche, une réécriture de bullets, "
            "une meilleure mise en avant des compétences ou une reformulation plus orientée offre."
        ),
        tone="gold",
    )

    quick_prompt = None
    quick_cols = st.columns(3)
    with quick_cols[0]:
        if st.button(
            "Réécris mon accroche",
            key="chat_prompt_hook",
            use_container_width=True,
            disabled=not uploaded_file or not selected_job_id or not api_status,
        ):
            quick_prompt = (
                "Réécris mon accroche de CV pour cette offre en 2 ou 3 phrases, "
                "sans inventer de compétences."
            )
    with quick_cols[1]:
        if st.button(
            "Quels bullets changer ?",
            key="chat_prompt_bullets",
            use_container_width=True,
            disabled=not uploaded_file or not selected_job_id or not api_status,
        ):
            quick_prompt = (
                "Dis-moi quels bullets d'expérience je devrais modifier en priorité "
                "et propose des versions plus convaincantes."
            )
    with quick_cols[2]:
        if st.button(
            "Mieux montrer mes compétences",
            key="chat_prompt_skills",
            use_container_width=True,
            disabled=not uploaded_file or not selected_job_id or not api_status,
        ):
            quick_prompt = (
                "Quelles compétences de mon CV dois-je mieux expliciter pour cette offre "
                "et comment les formuler ?"
            )

    if st.session_state.get("llm_chat_error"):
        status_message(f"Erreur du chat: {st.session_state['llm_chat_error']}", "error")

    chat_messages = st.session_state.get("llm_chat_messages", [])
    if not chat_messages:
        empty_state(
            "Conversation non démarrée",
            "Chargez un CV, sélectionnez une offre puis lancez une première demande au coach LLM.",
        )

    for message in chat_messages:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"])

    typed_prompt = st.chat_input(
        "Décrivez la modification que vous voulez apporter au CV...",
        disabled=not uploaded_file or not selected_job_id or not api_status,
    )

    prompt_to_send = quick_prompt or typed_prompt
    if prompt_to_send and uploaded_file and selected_job_id and api_status:
        history_payload = chat_messages[-8:]
        st.session_state.llm_chat_messages.append(
            {"role": "user", "content": prompt_to_send}
        )
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        with st.spinner("Le coach LLM prépare une proposition..."):
            try:
                response = api_client.chat_with_llm(
                    file_content=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    job_id=selected_job_id,
                    message=prompt_to_send,
                    history=history_payload,
                )
                assistant_reply = response["reply"]
                st.session_state.llm_chat_messages.append(
                    {"role": "assistant", "content": assistant_reply}
                )
                st.session_state.llm_chat_error = None
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
                    st.caption(
                        f"Réponse générée en {response['execution_time']:.2f}s via {response.get('llm_model', 'LLM')}."
                    )
            except Exception as exc:
                st.session_state.llm_chat_error = str(exc)
                status_message(f"Erreur du chat: {exc}", "error")
