"""
Composants de présentation réutilisables pour l'interface.
"""

from __future__ import annotations

from collections.abc import Sequence
from textwrap import dedent

import streamlit as st

from ui.utils.formatters import escape_html


def _render_html(markup: str) -> None:
    """Rend un bloc HTML sans indentation parasite."""
    cleaned = dedent(markup).strip()
    normalized = "\n".join(
        line.strip() if line.strip() else "" for line in cleaned.splitlines()
    )
    st.markdown(normalized, unsafe_allow_html=True)


def render_app_topbar(title: str, subtitle: str) -> None:
    """Affiche le bandeau léger en haut de page."""
    _render_html(
        f"""
        <div class="app-topbar-shell">
            <div class="app-topbar">
                <div class="brand-lockup">
                    <p class="brand-kicker">Workspace candidat</p>
                    <p class="brand-title">{escape_html(title)}</p>
                    <p class="brand-copy">{escape_html(subtitle)}</p>
                </div>
                <div class="brand-badge">Interface professionnelle</div>
            </div>
        </div>
        """
    )


def marketing_hero(
    eyebrow: str,
    title_lead: str,
    title_highlight: str,
    title_tail: str,
    subtitle: str,
    pills: Sequence[str] | None = None,
) -> None:
    """Affiche un hero centre de style landing page."""
    pill_markup = ""
    if pills:
        pill_markup = "".join(
            f'<span class="hero-badge">{escape_html(pill)}</span>' for pill in pills if pill
        )

    _render_html(
        f"""
        <section class="marketing-hero">
            <p class="marketing-eyebrow">{escape_html(eyebrow)}</p>
            <h1 class="marketing-title">
                {escape_html(title_lead)}
                <span>{escape_html(title_highlight)}</span>
                {escape_html(title_tail)}
            </h1>
            <p class="marketing-copy">{escape_html(subtitle)}</p>
            {"<div class='marketing-badges'>" + pill_markup + "</div>" if pill_markup else ""}
        </section>
        """
    )


def hero_banner(
    title: str,
    subtitle: str,
    eyebrow: str = "CV-Optimizer",
    pills: Sequence[str] | None = None,
) -> None:
    """Affiche un hero principal."""
    pill_markup = ""
    if pills:
        pill_markup = "".join(
            f'<span class="pill">{escape_html(pill)}</span>' for pill in pills if pill
        )

    _render_html(
        f"""
        <section class="hero-panel">
            <p class="hero-eyebrow">{escape_html(eyebrow)}</p>
            <h1 class="hero-title">{escape_html(title)}</h1>
            <p class="hero-copy">{escape_html(subtitle)}</p>
            {"<div class='pill-row'>" + pill_markup + "</div>" if pill_markup else ""}
        </section>
        """
    )


def section_intro(title: str, subtitle: str = "") -> None:
    """Affiche un titre de section compact."""
    _render_html(
        f"""
        <div class="section-heading">
            <h2 class="section-title">{escape_html(title)}</h2>
            {f"<p class='section-copy'>{escape_html(subtitle)}</p>" if subtitle else ""}
        </div>
        """
    )


def metric_card(label: str, value: str, detail: str = "", tone: str = "") -> None:
    """Affiche une carte de métrique."""
    tone_class = f" {tone}" if tone else ""
    _render_html(
        f"""
        <div class="metric-card{tone_class}">
            <p class="metric-label">{escape_html(label)}</p>
            <p class="metric-value">{escape_html(value)}</p>
            {f"<p class='metric-detail'>{escape_html(detail)}</p>" if detail else ""}
        </div>
        """
    )


def metric_row(metrics: Sequence[dict[str, str]]) -> None:
    """Affiche une ligne de métriques."""
    if not metrics:
        return

    columns = st.columns(len(metrics))
    for column, metric in zip(columns, metrics):
        with column:
            metric_card(
                metric.get("label", ""),
                metric.get("value", ""),
                metric.get("detail", ""),
                metric.get("tone", ""),
            )


def info_card(title: str, content: str, tone: str = "sage") -> None:
    """Affiche un bloc d'information."""
    body = escape_html(content).replace("\n", "<br>")
    _render_html(
        f"""
        <div class="info-card {escape_html(tone)}">
            <p class="info-title">{escape_html(title)}</p>
            {f"<p class='info-body'>{body}</p>" if content else ""}
        </div>
        """
    )


def status_message(message: str, status: str = "success") -> None:
    """Affiche une bannière de statut."""
    css_class = {
        "success": "status-success",
        "warning": "status-warning",
        "error": "status-error",
    }.get(status, "status-success")

    _render_html(
        f"""
        <div class="status-banner {css_class}">
            {escape_html(message)}
        </div>
        """
    )


def tag_cloud(tags: Sequence[str], tone: str = "") -> None:
    """Affiche un nuage de tags."""
    items = [tag for tag in tags if tag]
    if not items:
        return

    tone_class = f" {tone}" if tone else ""
    tag_markup = "".join(
        f'<span class="tag{tone_class}">{escape_html(tag)}</span>' for tag in items
    )
    _render_html(f'<div class="tag-cloud">{tag_markup}</div>')


def timeline(steps: Sequence[tuple[str, str]]) -> None:
    """Affiche une timeline verticale."""
    if not steps:
        return

    step_markup: list[str] = []
    for index, (title, copy) in enumerate(steps, start=1):
        step_markup.append(
            "<div class='timeline-step'>"
            f"<div class='timeline-index'>{index}</div>"
            "<div class='timeline-content'>"
            f"<p class='timeline-title'>{escape_html(title)}</p>"
            f"<p class='timeline-copy'>{escape_html(copy)}</p>"
            "</div>"
            "</div>"
        )

    _render_html(
        "<div class='surface-card timeline-shell'>"
        "<div class='timeline'>"
        + "".join(step_markup)
        + "</div></div>"
    )


def empty_state(title: str, copy: str) -> None:
    """Affiche un état vide."""
    info_card(title, copy, tone="gold")


def job_card(
    title: str,
    company: str,
    meta: Sequence[str],
    description: str = "",
    score_label: str | None = None,
    score_class: str = "high",
) -> None:
    """Affiche une carte d'offre synthétique."""
    meta_markup = "".join(
        f'<span class="tag">{escape_html(item)}</span>' for item in meta if item
    )
    score_markup = ""
    if score_label:
        css_class = "score-pill"
        if score_class == "medium":
            css_class += " medium"
        if score_class == "low":
            css_class += " low"
        score_markup = f'<div class="{css_class}">{escape_html(score_label)}</div>'

    body_parts = [
        "<div class='surface-card job-card'>",
        "<div class='job-header'>",
        "<div class='job-main'>",
        f"<p class='job-company'>{escape_html(company)}</p>",
        f"<h3 class='job-title'>{escape_html(title)}</h3>",
        "</div>",
        score_markup,
        "</div>",
    ]

    if meta_markup:
        body_parts.append(f"<div class='tag-cloud job-meta-row'>{meta_markup}</div>")
    if description:
        body_parts.append(f"<p class='job-description'>{escape_html(description)}</p>")

    body_parts.append("</div>")
    _render_html("".join(body_parts))
