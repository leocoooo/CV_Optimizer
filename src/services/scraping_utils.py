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
        date_str: Date en string (ex: "22/12/2025", "2025-12-22T10:30:00Z", "2026-03-06T09:25:56.076Z")

    Returns:
        datetime object ou None si parsing échoue
    """
    if not date_str:
        return None

    # Liste des formats possibles (ordre de priorité: plus spécifique en premier)
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # France Travail ISO: 2026-03-06T09:25:56.076Z
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO avec millisecondes (Python isoformat): 2026-03-08T14:37:41.628093
        "%Y-%m-%dT%H:%M:%SZ",  # WTTJ ISO: 2025-12-22T10:30:00Z
        "%d/%m/%Y",  # HelloWork: 22/12/2025
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

    # 3. Suppression des boutons "Voir plus/moins" et "Show more/less"
    text = re.sub(
        r"\b(Voir plus|Voir moins|Show more|Show less)\b", "", text, flags=re.IGNORECASE
    )

    # 4. Standardisation des apostrophes
    text = re.sub(r"[''`´]", "'", text)

    # 5. Suppression des caractères de contrôle
    text = "".join(
        ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ["\n", "\t"]
    )

    # 5. Filtrage Regex mis à jour : On garde / pour CI/CD et les noms de fichiers
    # Le tiret \- est à la fin pour éviter les erreurs d'intervalle
    text = re.sub(r'[^\w\s.,;:()@\'"&#+\-/]', " ", text)

    # 7. Correction du bégaiement (ex: d ' optimiser -> d'optimiser)
    # Supporte désormais tous les accents français
    text = re.sub(
        r"\b([ldnjmtsqLDNJMTSQ])\s*'\s*(?=[aeiouyâêîôûhéèàëïAEIOUYÂÊÎÔÛHÉÈÀËÏ])",
        r"\1'",
        text,
    )

    # 8. Nettoyage des espaces multiples
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def save_offers_to_db(db_session, offers: list, source_name: str = "Scraping") -> int:
    """
    Persiste les offres scrapées en base de données (NOUVEAU SCHÉMA UNIFIÉ).
    Fonction générique utilisable par ALL les scrapers (WTTJ, HelloWork, France Travail).

    Gère automatiquement le mapping entre les champs des scrapers et le modèle BD.
    Tous les champs nouveaux sont maintenant supportés: sector, remote_mode, salary,
    languages, soft_skills, competences, etc.

    Vérifie automatiquement les doublons avant insertion pour éviter les violations
    de contraintes d'unicité.

    Args:
        db_session: Session SQLAlchemy active
        offers: Liste de dictionnaires contenant les données des offres
                Peut venir de WTTJ, HelloWork ou France Travail - tous supportés
        source_name: Nom de la source pour les logs (ex: "WTTJ", "HelloWork", "France Travail")

    Returns:
        Nombre d'offres insérées
    """
    if not offers:
        logger.info("Aucune offre à insérer.")
        return 0

    # Vérifier les IDs existants une seule fois au début
    existing_ids = get_existing_ids(db_session)
    new_offers_count = 0

    for offer_data in offers:
        try:
            offer_id = offer_data.get("id")

            # Vérifier si l'offre existe déjà (doublon)
            if offer_id in existing_ids:
                logger.debug(f"Offre {offer_id} déjà en base, ignorée")
                continue

            # Parse les dates si elles sont en string (support backward-compatibility)
            date_publication = offer_data.get("date_publication")
            if isinstance(date_publication, str):
                date_publication = parse_date(date_publication)

            date_scraping = offer_data.get("date_scraping")
            if isinstance(date_scraping, str):
                date_scraping = parse_date(date_scraping)

            # Backward-compatibility: Si date_publication n'existe pas, essayer creation_date
            if date_publication is None:
                creation_date = offer_data.get("creation_date")
                if isinstance(creation_date, str):
                    date_publication = parse_date(creation_date)

            new_offer = JobOffer(
                # ===== IDs et URLs =====
                id=offer_data["id"],
                url=offer_data["url"],
                source=offer_data["source"],
                # ===== DATES =====
                date_publication=date_publication,
                date_scraping=date_scraping,
                # ===== POSTE =====
                title=offer_data["title"],
                sector=offer_data.get("sector"),
                contract_type=offer_data.get("contract_type"),
                remote_mode=offer_data.get("remote_mode"),
                # ===== LOCALISATION =====
                city=offer_data.get("city")
                or offer_data.get(
                    "location"
                ),  # Fallback to location for backward compatibility
                department=offer_data.get("department"),
                region=offer_data.get("region"),
                location_address=offer_data.get("location_address"),
                # ===== ENTREPRISE =====
                company=offer_data["company"],
                company_size=offer_data.get("company_size"),
                # ===== PROFIL DEMANDÉ =====
                required_experience=offer_data.get("required_experience"),
                required_education=offer_data.get("required_education"),
                competences=offer_data.get("competences"),
                # ===== RÉMUNÉRATION =====
                salary=offer_data.get("salary"),
                # ===== CONTENU TEXTUEL =====
                description=offer_data["description"],
                job_profile=offer_data.get("job_profile"),
                # ===== CHAMPS SOURCE-SPÉCIFIQUES =====
                languages=offer_data.get("languages"),
                soft_skills=offer_data.get("soft_skills"),
            )
            db_session.add(new_offer)
            existing_ids.add(
                offer_id
            )  # Ajouter à la liste pour éviter duplicates dans le même batch
            new_offers_count += 1
        except Exception as e:
            logger.warning(
                f"Erreur lors de la préparation de l'offre {offer_data.get('title', 'SANS TITRE')}: {e}"
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
