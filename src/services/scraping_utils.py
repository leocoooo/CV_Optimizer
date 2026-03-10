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
        "%Y-%m-%dT%H:%M:%S",  # HelloWork ISO: 2026-03-05T00:00:00 (sans Z, sans ms)
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


def get_existing_urls(db_session) -> set:
    """
    Récupère les URLs déjà présentes en base pour éviter les doublons (par URL).

    Utilisé pour détecter les offres dupliquées même si leur job_id a changé
    (par exemple, si location_address devient None après un scraping).

    Args:
        db_session: Session SQLAlchemy active

    Returns:
        Set des URLs existantes (non-None)
    """
    return {
        offer.url
        for offer in db_session.query(JobOffer.url)
        .filter(JobOffer.url.isnot(None))
        .all()
    }


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


def parse_location_hellowork(location_str: str | None) -> dict[str, str | None]:
    """
    Parse une localisation HelloWork au format "Ville - Code" et extrait city, department, region.

    Exemples:
        "Nantes - 44" → {"city": "Nantes", "department": "Loire-Atlantique", "region": "Pays de la Loire"}
        "Lyon - 69" → {"city": "Lyon", "department": "Rhône", "region": "Auvergne-Rhône-Alpes"}
        "Belgique" → {"city": None, "department": None, "region": None}

    Args:
        location_str: Localisation au format "Ville - Code" ou autre

    Returns:
        dict: {"city": str|None, "department": str|None, "region": str|None}
    """
    result: dict[str, str | None] = {"city": None, "department": None, "region": None}

    if not location_str:
        return result

    # Mappages département → nom (complet, même source que France Travail API)
    dept_names = {
        "01": "Ain",
        "02": "Aisne",
        "03": "Allier",
        "04": "Alpes-de-Haute-Provence",
        "05": "Hautes-Alpes",
        "06": "Alpes-Maritimes",
        "07": "Ardèche",
        "08": "Ardennes",
        "09": "Ariège",
        "10": "Aube",
        "11": "Aude",
        "12": "Aveyron",
        "13": "Bouches-du-Rhône",
        "14": "Calvados",
        "15": "Cantal",
        "16": "Charente",
        "17": "Charente-Maritime",
        "18": "Cher",
        "19": "Corrèze",
        "2A": "Corse-du-Sud",
        "2B": "Haute-Corse",
        "21": "Côte-d'Or",
        "22": "Côtes-d'Armor",
        "23": "Creuse",
        "24": "Dordogne",
        "25": "Doubs",
        "26": "Drôme",
        "27": "Eure",
        "28": "Eure-et-Loir",
        "29": "Finistère",
        "30": "Gard",
        "31": "Haute-Garonne",
        "32": "Gers",
        "33": "Gironde",
        "34": "Hérault",
        "35": "Ille-et-Vilaine",
        "36": "Indre",
        "37": "Indre-et-Loire",
        "38": "Isère",
        "39": "Jura",
        "40": "Landes",
        "41": "Loir-et-Cher",
        "42": "Loire",
        "43": "Haute-Loire",
        "44": "Loire-Atlantique",
        "45": "Loiret",
        "46": "Lot",
        "47": "Lot-et-Garonne",
        "48": "Lozère",
        "49": "Maine-et-Loire",
        "50": "Manche",
        "51": "Marne",
        "52": "Haute-Marne",
        "53": "Mayenne",
        "54": "Meurthe-et-Moselle",
        "55": "Meuse",
        "56": "Morbihan",
        "57": "Moselle",
        "58": "Nièvre",
        "59": "Nord",
        "60": "Oise",
        "61": "Orne",
        "62": "Pas-de-Calais",
        "63": "Puy-de-Dôme",
        "64": "Pyrénées-Atlantiques",
        "65": "Hautes-Pyrénées",
        "66": "Pyrénées-Orientales",
        "67": "Bas-Rhin",
        "68": "Haut-Rhin",
        "69": "Rhône",
        "70": "Haute-Saône",
        "71": "Saône-et-Loire",
        "72": "Sarthe",
        "73": "Savoie",
        "74": "Haute-Savoie",
        "75": "Paris",
        "76": "Seine-Maritime",
        "77": "Seine-et-Marne",
        "78": "Yvelines",
        "79": "Deux-Sèvres",
        "80": "Somme",
        "81": "Tarn",
        "82": "Tarn-et-Garonne",
        "83": "Var",
        "84": "Vaucluse",
        "85": "Vendée",
        "86": "Vienne",
        "87": "Haute-Vienne",
        "88": "Vosges",
        "89": "Yonne",
        "90": "Territoire de Belfort",
        "91": "Essonne",
        "92": "Hauts-de-Seine",
        "93": "Seine-Saint-Denis",
        "94": "Val-de-Marne",
        "95": "Val-d'Oise",
    }

    # Mappages département → région
    regions = {
        "75": "Île-de-France",
        "77": "Île-de-France",
        "78": "Île-de-France",
        "91": "Île-de-France",
        "92": "Île-de-France",
        "93": "Île-de-France",
        "94": "Île-de-France",
        "95": "Île-de-France",
        "60": "Île-de-France",
        "21": "Bourgogne-Franche-Comté",
        "25": "Bourgogne-Franche-Comté",
        "39": "Bourgogne-Franche-Comté",
        "58": "Bourgogne-Franche-Comté",
        "70": "Bourgogne-Franche-Comté",
        "71": "Bourgogne-Franche-Comté",
        "89": "Bourgogne-Franche-Comté",
        "90": "Bourgogne-Franche-Comté",
        "22": "Bretagne",
        "29": "Bretagne",
        "35": "Bretagne",
        "56": "Bretagne",
        "18": "Centre-Val de Loire",
        "28": "Centre-Val de Loire",
        "36": "Centre-Val de Loire",
        "37": "Centre-Val de Loire",
        "41": "Centre-Val de Loire",
        "45": "Centre-Val de Loire",
        "2A": "Corse",
        "2B": "Corse",
        "08": "Grand Est",
        "10": "Grand Est",
        "51": "Grand Est",
        "52": "Grand Est",
        "54": "Grand Est",
        "55": "Grand Est",
        "57": "Grand Est",
        "67": "Grand Est",
        "68": "Grand Est",
        "88": "Grand Est",
        "02": "Hauts-de-France",
        "59": "Hauts-de-France",
        "62": "Hauts-de-France",
        "80": "Hauts-de-France",
        "14": "Normandie",
        "27": "Normandie",
        "50": "Normandie",
        "61": "Normandie",
        "76": "Normandie",
        "16": "Nouvelle-Aquitaine",
        "17": "Nouvelle-Aquitaine",
        "19": "Nouvelle-Aquitaine",
        "23": "Nouvelle-Aquitaine",
        "24": "Nouvelle-Aquitaine",
        "33": "Nouvelle-Aquitaine",
        "40": "Nouvelle-Aquitaine",
        "47": "Nouvelle-Aquitaine",
        "64": "Nouvelle-Aquitaine",
        "79": "Nouvelle-Aquitaine",
        "86": "Nouvelle-Aquitaine",
        "87": "Nouvelle-Aquitaine",
        "09": "Occitanie",
        "11": "Occitanie",
        "12": "Occitanie",
        "30": "Occitanie",
        "31": "Occitanie",
        "32": "Occitanie",
        "34": "Occitanie",
        "46": "Occitanie",
        "48": "Occitanie",
        "65": "Occitanie",
        "66": "Occitanie",
        "81": "Occitanie",
        "82": "Occitanie",
        "01": "Auvergne-Rhône-Alpes",
        "03": "Auvergne-Rhône-Alpes",
        "07": "Auvergne-Rhône-Alpes",
        "15": "Auvergne-Rhône-Alpes",
        "26": "Auvergne-Rhône-Alpes",
        "38": "Auvergne-Rhône-Alpes",
        "42": "Auvergne-Rhône-Alpes",
        "43": "Auvergne-Rhône-Alpes",
        "63": "Auvergne-Rhône-Alpes",
        "69": "Auvergne-Rhône-Alpes",
        "73": "Auvergne-Rhône-Alpes",
        "74": "Auvergne-Rhône-Alpes",
        "04": "Provence-Alpes-Côte d'Azur",
        "05": "Provence-Alpes-Côte d'Azur",
        "06": "Provence-Alpes-Côte d'Azur",
        "13": "Provence-Alpes-Côte d'Azur",
        "83": "Provence-Alpes-Côte d'Azur",
        "84": "Provence-Alpes-Côte d'Azur",
        "44": "Pays de la Loire",
        "49": "Pays de la Loire",
        "53": "Pays de la Loire",
        "72": "Pays de la Loire",
        "85": "Pays de la Loire",
    }

    # Parse "Ville - Code" format
    try:
        parts = location_str.split(" - ")
        if len(parts) == 2:
            city_name = parts[0].strip()
            dept_code = parts[1].strip()

            # Extraire et stocker la ville
            result["city"] = city_name if city_name else None

            # Lookup département et région via les mappages
            result["department"] = dept_names.get(dept_code, dept_code)
            result["region"] = regions.get(dept_code)
        else:
            # Pas de " - " dans le format, garder la localisation comme ville
            result["city"] = location_str.strip() if location_str else None
    except Exception as e:
        logger.debug(f"Erreur parsing location HelloWork '{location_str}': {e}")

    return result


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
