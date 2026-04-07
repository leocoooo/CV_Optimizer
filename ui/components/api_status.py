"""
Composant d'affichage du statut de l'API.
"""

from ui.components.cards import status_message


def show_api_error() -> None:
    """Affiche une alerte compacte si l'API n'est pas disponible."""
    status_message(
        "Connexion API indisponible. Relancez le backend puis rechargez l'application.",
        "warning",
    )
