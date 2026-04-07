"""
Page dédiée à la génération de lettre de motivation.
"""

from __future__ import annotations

import base64

import streamlit as st

from ui.components.cards import empty_state, hero_banner, info_card, metric_row, section_intro, status_message, timeline
from ui.components.file_helpers import cv_uploader
from ui.utils.formatters import build_job_label, format_datetime, truncate


def _resolve_selected_job(api_client, selected_job_id: str | None) -> dict | None:
    if not selected_job_id:
        return None
    cache = st.session_state.setdefault("cover_letter_job_cache", {})
    if selected_job_id in cache:
        return cache[selected_job_id]

    try:
        details = api_client.get_job_details(selected_job_id)
        cache[selected_job_id] = details
        return details
    except Exception:
        return None


def render(api_client, api_status: bool) -> None:
    """Affiche la page LM."""
    hero_banner(
        "Générer une lettre de motivation à partir du CV et de l'offre.",
        (
            "Sélectionnez un poste, ajoutez votre CV puis générez une lettre structurée "
            "dans l'esprit de votre modèle LaTeX, avec un aperçu lisible et une version `.tex` exploitable."
        ),
        eyebrow="Lettre de motivation",
        pills=["Offre ciblée", "CV PDF", "Version LaTeX prête à exporter"],
    )

    selected_job_id = st.session_state.get("preselected_job_id")
    if "cover_letter_job_candidates" not in st.session_state:
        st.session_state.cover_letter_job_candidates = []

    search_col, profile_col = st.columns([1.15, 1], gap="large")

    with search_col:
        section_intro(
            "Choisir une offre",
            "Cherchez une offre depuis la base ou réutilisez une offre présélectionnée depuis une autre vue.",
        )
        keywords = st.text_input(
            "Mots-clés",
            value=st.session_state.get("cover_letter_keywords", ""),
            placeholder="Quant trader, data scientist, ML engineer...",
        )
        location = st.text_input(
            "Localisation (optionnelle)",
            value=st.session_state.get("cover_letter_location", ""),
            placeholder="Paris, Londres, Remote...",
        )

        if st.button(
            "Rechercher une offre pour la LM",
            key="cover_letter_search_btn",
            use_container_width=True,
            disabled=not api_status,
        ):
            st.session_state.cover_letter_keywords = keywords
            st.session_state.cover_letter_location = location
            with st.spinner("Recherche des offres..."):
                try:
                    search_result = api_client.search_jobs(
                        keywords=keywords or None,
                        location=location or None,
                        page_size=12,
                        days_limit=60,
                    )
                    st.session_state.cover_letter_job_candidates = search_result.get("jobs", [])
                    st.session_state.cover_letter_error = None
                except Exception as exc:
                    st.session_state.cover_letter_job_candidates = []
                    st.session_state.cover_letter_error = str(exc)

        candidates = st.session_state.get("cover_letter_job_candidates", [])
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
                "Aucune offre sélectionnée",
                "Commencez par rechercher une offre cible ou utilisez une offre transmise depuis le matching ou l'exploration.",
            )

        with st.expander("Entrer un ID d'offre manuellement"):
            manual_job_id = st.text_input("ID d'offre", value=selected_job_id or "")
            if st.button("Utiliser cet ID", key="cover_letter_manual_job_id", use_container_width=True):
                st.session_state.preselected_job_id = manual_job_id.strip() or None
                selected_job_id = st.session_state.preselected_job_id

    with profile_col:
        section_intro(
            "Informations candidat",
            "Ces informations alimentent l'en-tête et la signature de la lettre.",
        )
        form_col1, form_col2 = st.columns(2, gap="medium")
        with form_col1:
            applicant_name = st.text_input(
                "Nom complet",
                value=st.session_state.get("cover_letter_applicant_name", ""),
                placeholder="Pierre QUINTIN de KERCADIO",
            )
            city = st.text_input(
                "Ville",
                value=st.session_state.get("cover_letter_city", ""),
                placeholder="Paris",
            )
            email = st.text_input(
                "Email",
                value=st.session_state.get("cover_letter_email", ""),
                placeholder="prenom.nom@email.com",
            )
        with form_col2:
            phone = st.text_input(
                "Téléphone",
                value=st.session_state.get("cover_letter_phone", ""),
                placeholder="+33 ...",
            )
            letter_language_label = st.selectbox(
                "Langue de la lettre",
                ["English", "Français"],
                index=0 if st.session_state.get("cover_letter_language", "english") == "english" else 1,
            )
            focus_note = st.text_area(
                "Point à mettre en avant (optionnel)",
                value=st.session_state.get("cover_letter_focus_note", ""),
                placeholder="Ex: mon profil quantitatif, mon parcours data + finance, mon expérience en gestion d'actifs...",
                height=100,
            )

        st.session_state.cover_letter_applicant_name = applicant_name
        st.session_state.cover_letter_city = city
        st.session_state.cover_letter_email = email
        st.session_state.cover_letter_phone = phone
        st.session_state.cover_letter_focus_note = focus_note
        letter_language = "english" if letter_language_label == "English" else "french"
        st.session_state.cover_letter_language = letter_language

    selected_job = _resolve_selected_job(api_client, selected_job_id) if api_status else None
    section_intro(
        "Offre actuellement ciblée",
        "Le contexte de l'offre sert de base à la personnalisation de la lettre.",
    )
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
        st.caption(truncate(selected_job.get("description"), limit=260))
    else:
        timeline(
            [
                ("Choisir une offre", "Sélectionnez la cible de la lettre depuis la base."),
                ("Ajouter le CV", "L'API extrait le contenu utile du PDF."),
                ("Générer la LM", "Le LLM produit un brouillon structuré et une version LaTeX."),
            ]
        )

    if st.session_state.get("cover_letter_error"):
        status_message(
            f"Recherche d'offres impossible: {st.session_state['cover_letter_error']}",
            "error",
        )

    section_intro(
        "CV source",
        "Ajoutez maintenant le CV qui servira de base à la lettre.",
    )
    uploaded_file = cv_uploader(key="cover_letter_cv")
    current_cv_signature = None
    if uploaded_file:
        current_cv_signature = f"{uploaded_file.name}:{len(uploaded_file.getvalue())}"

    current_input_signature = "|".join(
        [
            selected_job_id or "",
            current_cv_signature or "",
            applicant_name.strip(),
            city.strip(),
            email.strip(),
            phone.strip(),
            letter_language,
            focus_note.strip(),
        ]
    )
    previous_signature = st.session_state.get("cover_letter_input_signature")
    if current_input_signature != previous_signature:
        st.session_state.cover_letter_input_signature = current_input_signature
        st.session_state.last_cover_letter_result = None
        st.session_state.last_cover_letter_error = None

    if st.button(
        "Générer la lettre de motivation",
        key="generate_cover_letter_btn",
        use_container_width=True,
        disabled=(
            not uploaded_file
            or not selected_job_id
            or not api_status
            or not applicant_name.strip()
        ),
        type="primary",
    ):
        with st.spinner("Le LLM prépare la lettre et la version LaTeX..."):
            try:
                result = api_client.generate_cover_letter(
                    file_content=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    job_id=selected_job_id,
                    applicant_name=applicant_name.strip(),
                    city=city.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    letter_language=letter_language,
                    focus_note=focus_note.strip(),
                )
                st.session_state.last_cover_letter_result = result
                st.session_state.last_cover_letter_error = None
            except Exception as exc:
                st.session_state.last_cover_letter_error = str(exc)

    if st.session_state.get("last_cover_letter_error"):
        status_message(
            f"Erreur de génération LM: {st.session_state['last_cover_letter_error']}",
            "error",
        )

    result = st.session_state.get("last_cover_letter_result")
    if result and selected_job_id and result.get("job_id") != selected_job_id:
        result = None

    if not result:
        info_card(
            "Lettre non générée",
            "Complétez les informations demandées puis lancez la génération pour obtenir l'aperçu et le `.tex`.",
            tone="gold",
        )
        return

    status_message(
        f"Lettre générée en {result['execution_time']:.2f}s pour {result['job_title']}.",
        "success",
    )
    metric_row(
        [
            {
                "label": "Poste visé",
                "value": truncate(result["job_title"], limit=24),
                "detail": result["company"],
                "tone": "accent",
            },
            {
                "label": "Langue",
                "value": "English" if result["language"] == "english" else "Français",
                "detail": "Langue de rédaction",
                "tone": "sage",
            },
            {
                "label": "CV analysé",
                "value": f"{result['cv_length']:,}".replace(",", " "),
                "detail": "Caractères extraits",
                "tone": "gold",
            },
            {
                "label": "Modèle LLM",
                "value": result.get("llm_model", "N/A"),
                "detail": "Service de génération utilisé",
                "tone": "sage",
            },
        ]
    )

    section_intro(
        "Aperçu de la lettre",
        "Relisez le brouillon avant export LaTeX.",
    )
    info_card("Objet", result["subject"], tone="accent")
    preview_lines = [result["greeting"], ""]
    preview_lines.extend(result.get("paragraphs", []))
    preview_lines.extend(["", result["closing"], "", result["signature"]])
    st.markdown("\n\n".join(preview_lines))

    section_intro(
        "Version LaTeX",
        "Structure inspirée de votre modèle, prête à exporter ou adapter.",
    )
    tex_filename = f"lettre_motivation_{result['job_id']}.tex"
    pdf_filename = f"lettre_motivation_{result['job_id']}.pdf"
    download_col1, download_col2 = st.columns(2, gap="medium")
    with download_col1:
        st.download_button(
            "Télécharger le fichier PDF",
            data=base64.b64decode(result["pdf_base64"]),
            file_name=pdf_filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with download_col2:
        st.download_button(
            "Télécharger le fichier .tex",
            data=result["latex_source"],
            file_name=tex_filename,
            mime="text/x-tex",
            use_container_width=True,
        )
    st.code(result["latex_source"], language="latex")
