"""
Helpers d'affichage pour l'interface Streamlit.
"""

from __future__ import annotations

from datetime import datetime
import html
from typing import Any


def escape_html(value: Any) -> str:
    """Échappe une valeur avant injection HTML."""
    return html.escape("" if value is None else str(value))


def display_text(value: Any, fallback: str = "Non renseigné") -> str:
    """Retourne un texte prêt à l'affichage."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def truncate(value: Any, limit: int = 180) -> str:
    """Tronque un texte sans casser l'affichage."""
    text = display_text(value, fallback="")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def parse_datetime(value: Any) -> datetime | None:
    """Parse une date provenant de l'API."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def format_datetime(value: Any, with_time: bool = False) -> str:
    """Formate une date pour l'interface."""
    parsed = parse_datetime(value)
    if not parsed:
        return "Date indisponible"
    return parsed.strftime("%d/%m/%Y %H:%M" if with_time else "%d/%m/%Y")


def format_relative_date(value: Any) -> str:
    """Retourne une date relative lisible."""
    parsed = parse_datetime(value)
    if not parsed:
        return "Date indisponible"

    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    delta_days = (now.date() - parsed.date()).days

    if delta_days <= 0:
        return "Aujourd'hui"
    if delta_days == 1:
        return "Hier"
    if delta_days < 7:
        return f"Il y a {delta_days} jours"
    return format_datetime(parsed)


def format_uptime(seconds: Any) -> str:
    """Transforme un uptime en texte court."""
    if seconds is None:
        return "Indisponible"

    total_seconds = int(float(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def friendly_status_label(
    value: Any,
    ok_label: str = "Disponible",
    warning_label: str = "A verifier",
) -> str:
    """Convertit un statut technique en libelle lisible pour l'interface."""
    if isinstance(value, bool):
        return ok_label if value else warning_label

    text = display_text(value, fallback=warning_label)
    normalized = text.lower()

    ok_markers = ("healthy", "connected", "online", "ready", "ok", "available")
    warning_markers = (
        "error",
        "failed",
        "offline",
        "timeout",
        "could not",
        "refused",
        "unavailable",
        "denied",
    )

    if any(marker in normalized for marker in ok_markers):
        return ok_label
    if any(marker in normalized for marker in warning_markers):
        return warning_label
    return text


def compact_number(value: Any) -> str:
    """Formate un entier avec séparation par espaces."""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def split_csv(value: Any, limit: int = 6) -> list[str]:
    """Transforme une chaîne CSV en liste de tags."""
    text = display_text(value, fallback="")
    if not text:
        return []

    items = [item.strip() for item in text.split(",") if item.strip()]
    return items[:limit]


def score_badge(score: float | None) -> tuple[str, str, str]:
    """Retourne le libellé, la classe CSS et un commentaire pour un score."""
    if score is None:
        return ("Score indisponible", "medium", "Analyse partielle")
    if score >= 0.75:
        return ("Très fort match", "high", "CV très aligné avec la cible")
    if score >= 0.55:
        return ("Match prometteur", "medium", "Quelques ajustements à prévoir")
    return ("Match partiel", "low", "À retravailler avant candidature")


def build_job_label(job: dict[str, Any]) -> str:
    """Construit un libellé synthétique pour un selectbox ou un résumé."""
    title = display_text(job.get("title"))
    company = display_text(job.get("company"))
    location = display_text(job.get("location"), fallback="Lieu non précisé")
    return f"{title} · {company} · {location}"
