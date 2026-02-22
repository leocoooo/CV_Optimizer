"""
Utilitaires partagés pour les scripts de webscraping.
Single source of truth pour les fonctions communes.
"""

import sys
import re
import unicodedata
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup

from src.database.models import JobOffer


def parse_date(date_str: str):
    """
    Parse une date depuis différents formats possibles.

    Args:
        date_str: Date en string (ex: "22/12/2025", "2025-12-22T10:30:00Z")

    Returns:
        datetime object ou None si parsing échoue
    """
    if not date_str:
        return None

    # Liste des formats possibles
    formats = [
        "%d/%m/%Y",  # HelloWork: 22/12/2025
        "%Y-%m-%dT%H:%M:%SZ",  # WTTJ ISO: 2025-12-22T10:30:00Z
        "%Y-%m-%d",  # Simple: 2025-12-22
        "%d-%m-%Y",  # Alternatif: 22-12-2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.debug(f"Format de date non reconnu : {date_str}")
    return None


def setup_logger(level: str = "DEBUG"):
    """
    Configure le logger loguru avec un format standardisé.
    Appelé une seule fois au démarrage de chaque script.
    """
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=level,
    )
    return logger


def get_existing_ids(db_session) -> set:
    """
    Récupère les IDs déjà présents en base pour éviter les doublons.

    Args:
        db_session: Session SQLAlchemy active

    Returns:
        Set des IDs existants
    """
    return {offer.id for offer in db_session.query(JobOffer.id).all()}


def clean_description(html_text: str) -> str:
    """Nettoie et normalise une description HTML en texte brut pour des offres d'IT.

    La fonction :
        - extrait le texte depuis le HTML,
        - normalise les caractères Unicode (NFC),
        - unifie les différents types d'apostrophes,
        - supprime les caractères de contrôle indésirables,
        - filtre les caractères non pertinents via regex,
        - et nettoie les espaces superflus.

    Args:
        html_text: Contenu HTML de la description à nettoyer. Peut être une chaîne vide ou None.

    Returns:
        str: Description nettoyée en texte brut. Retourne une chaîne vide si l'entrée est vide ou None.
    """

    if not html_text:
        return ""

    # 1. Extraction HTML
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ")

    # 2. Normalisation Unicode (NFC)
    text = unicodedata.normalize("NFC", text)

    # 3. Standardisation des apostrophes
    text = re.sub(r"[’‘`´]", "'", text)

    # 4. Suppression des caractères de contrôle
    text = "".join(
        ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ["\n", "\t"]
    )

    # 5. Filtrage Regex mis à jour : On garde / pour CI/CD et les noms de fichiers
    # Le tiret \- est à la fin pour éviter les erreurs d'intervalle
    text = re.sub(r'[^\w\s.,;:()@\'"&#+\-/]', " ", text)

    # 6. Correction du bégaiement (ex: d ' optimiser -> d'optimiser)
    # Supporte désormais tous les accents français
    text = re.sub(
        r"\b([ldnjmtsqLDNJMTSQ])\s*'\s*(?=[aeiouyâêîôûhéèàëïAEIOUYÂÊÎÔÛHÉÈÀËÏ])",
        r"\1'",
        text,
    )

    # 7. Nettoyage des espaces multiples
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def save_offers_to_db(db_session, offers: list, source_name: str = "Scraping") -> int:
    """
    Persiste les offres scrapées en base de données.
    Fonction générique utilisable par tous les scrapers.

    Args:
        db_session: Session SQLAlchemy active
        offers: Liste de dictionnaires contenant les données des offres
        source_name: Nom de la source pour les logs (ex: "WTTJ", "HelloWork")

    Returns:
        Nombre d'offres insérées
    """
    if not offers:
        logger.info("Aucune offre à insérer.")
        return 0

    new_offers_count = 0

    for offer_data in offers:
        try:
            # Parse les dates si elles sont en string
            creation_date = offer_data.get("creation_date")
            if isinstance(creation_date, str):
                creation_date = parse_date(creation_date)

            actualisation_date = offer_data.get("actualisation_date")
            if isinstance(actualisation_date, str):
                actualisation_date = parse_date(actualisation_date)

            new_offer = JobOffer(
                id=offer_data["id"],
                title=offer_data["title"],
                company=offer_data["company"],
                location=offer_data["location"],
                description=offer_data["description"],
                url=offer_data["url"],
                source=offer_data["source"],
                creation_date=creation_date,
                actualisation_date=actualisation_date,
                contract_type=offer_data.get("contract_type"),
                required_experience=offer_data.get("required_experience"),
                contact=offer_data.get("contact"),
                raw_json=offer_data.get("raw_json"),
            )
            db_session.add(new_offer)
            new_offers_count += 1
        except Exception as e:
            logger.warning(
                f"Erreur lors de la préparation de l'offre {offer_data.get('title')}: {e}"
            )

    try:
        db_session.commit()
        if new_offers_count > 0:
            logger.success(
                f"Insertion : {new_offers_count} nouvelles offres {source_name} ajoutées en base."
            )
    except Exception as e:
        db_session.rollback()
        logger.error(f"Erreur lors de l'insertion en base : {e}")
        return 0

    return new_offers_count
