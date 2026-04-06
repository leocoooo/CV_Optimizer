"""
Script pour homogénéiser les données dans la table job_offers.
Crée des colonnes cleaned_* basées sur les valeurs existantes avec des règles métier.
"""

import re
import unicodedata
from sqlalchemy import text, inspect
from src.database.database import engine, SessionLocal
from typing import Optional
from loguru import logger


# ===== VALEURS ACCEPTÉES =====
CLEANED_TITLES = [
    "Data scientist",
    "Data engineer",
    "Data Analyst",
    "Developpeur Python",
    "Developpeur frontend",
    "Developpeur backend",
    "Developpeur fullstack",
    "GenAI Engineer",
    "AI Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "Research Engineer",
    "Developpeur",
    "Software Engineer",
    "Chef de Projet Data",
    "Data manager",
    "DevOps",
    "MLOps",
    "LLM Engineer",
    "Ingénieur IA",
]

CLEANED_CONTRACT_TYPES = [
    "CDI",
    "CDD",
    "Freelance",
    "Alternance",
    "Stage",
    "Indépendant",
    "VIE",
    "Graduate Program",
    "Interim",
]

CLEANED_REMOTE_MODES = [
    "Pas de télétravail",
    "Télétravail possible",
    "Télétravail complet",
]

CLEANED_EDUCATIONS = [
    "Doctorat",
    "Master/Bac+5",
    "Bac+3/+4",
    "Bac+2",
    "Bac et moins",
]


# ===== UTILITAIRES =====
def remove_accents(text: str) -> str:
    """Supprime les accents d'une chaîne pour normaliser les comparaisons."""
    if not text:
        return text
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


# ===== FONCTIONS DE TRANSFORMATION =====
def clean_title(title: Optional[str]) -> Optional[str]:
    """
    Homogénéise le titre : cherche une correspondance approximative.
    Si pas de match direct, nettoie le titre en enlevant les H/F, contrats, tirets, etc.
    Retourne la valeur acceptée si trouvée, sinon le titre nettoyé.
    """
    if not title:
        return None

    title_normalized = remove_accents(title.lower().strip())

    # Correspondances directes (fuzzy matching simple)
    for cleaned_title in CLEANED_TITLES:
        cleaned_normalized = remove_accents(cleaned_title.lower())
        if (
            cleaned_normalized in title_normalized
            or title_normalized in cleaned_normalized
        ):
            return cleaned_title

    # Si pas de match direct, nettoyer le titre
    cleaned = _cleanup_title(title)

    # Essayer de matcher le titre nettoyé
    if cleaned and cleaned != title:
        cleaned_normalized = remove_accents(cleaned.lower().strip())
        for cleaned_title in CLEANED_TITLES:
            cleaned_normalized_ref = remove_accents(cleaned_title.lower())
            if (
                cleaned_normalized_ref in cleaned_normalized
                or cleaned_normalized in cleaned_normalized_ref
            ):
                return cleaned_title

    # Retourner le titre nettoyé si différent de l'original
    return cleaned if cleaned and cleaned != title else title


def _cleanup_title(title: str) -> str:
    """
    Nettoie un titre en enlevant :
    - Les patterns (H/F), (H/M), (H), (F), (M) avec ou sans parenthèses
    - Les noms de contrats au début (Stage, Alternance, CDI, etc.)
    - Les tirets au début
    - Les espaces superflus
    """
    if not title:
        return title

    # Enlever les patterns (H/F), (H/M), (H), (F), (M) - uniquement avec parenthèses ou à la fin/séparation
    # Patterns reconnus : (H/F), (H), H/F, etc.
    cleaned = re.sub(r"\s*\(\s*[HFM](?:/[HFM])?\s*\)", "", title, flags=re.IGNORECASE)
    # Aussi enlever H/F en fin de chaîne ou avant autres séparateurs
    cleaned = re.sub(r"\s+[HFM]/[HFM](?:\s|$)", " ", cleaned, flags=re.IGNORECASE)

    # Enlever les noms de contrats au début (suivi de tiret, deux-points, etc.)
    for contract in CLEANED_CONTRACT_TYPES:
        pattern = rf"^{re.escape(contract)}\s*[-:–—]\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Enlever les tirets au début
    cleaned = re.sub(r"^[-–—]\s*", "", cleaned)

    # Nettoyer les espaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def clean_contract_type(contract_type: Optional[str]) -> Optional[str]:
    """
    Homogénéise le type de contrat.
    """
    if not contract_type:
        return None

    contract_normalized = remove_accents(contract_type.lower().strip())

    for cleaned_type in CLEANED_CONTRACT_TYPES:
        cleaned_normalized = remove_accents(cleaned_type.lower())
        if (
            cleaned_normalized in contract_normalized
            or contract_normalized in cleaned_normalized
        ):
            return cleaned_type

    return contract_type


def clean_remote_mode(remote_mode: Optional[str]) -> Optional[str]:
    """
    Homogénéise le mode de télétravail selon la règle :
    - Occasionnel, Fréquent, Partiel, Possible → "Télétravail possible"
    - Total, Complet → "Télétravail complet"
    - Non autorisé, Pas de, etc. → "Pas de télétravail"
    """
    if not remote_mode:
        return None

    remote_normalized = remove_accents(remote_mode.lower().strip())

    # Télétravail complet
    if any(keyword in remote_normalized for keyword in ["total", "complet", "100%"]):
        return "Télétravail complet"

    # Pas de télétravail
    if any(
        keyword in remote_normalized for keyword in ["non autorise", "pas de", "aucun"]
    ):
        return "Pas de télétravail"

    # Télétravail possible (defaut pour les autres variations)
    if any(
        keyword in remote_normalized
        for keyword in ["occasionnel", "frequent", "partiel", "possible"]
    ):
        return "Télétravail possible"

    # Par défaut, si c'est mentionné mais pas clair
    if "teletravail" in remote_normalized or "remote" in remote_normalized:
        return "Télétravail possible"

    return remote_mode


def clean_required_experience(experience: Optional[str]) -> Optional[str]:
    """
    Homogénéise l'expérience requise :
    - "debutant" → "0"
    - "Expérience exigée" → "2"
    - Sinon extrait le plus petit chiffre trouvé
    """
    if not experience:
        return None

    exp_normalized = remove_accents(experience.lower().strip())

    # Cas particuliers
    if "debutant" in exp_normalized or "junior" in exp_normalized:
        return "0"

    if "experience exigee" in exp_normalized:
        return "2"

    # Chercher tous les chiffres dans la chaîne
    numbers = re.findall(r"\d+", exp_normalized)
    if numbers:
        # Retourner le plus petit
        min_years = min(int(n) for n in numbers)
        exp_years = str(min_years)
        return exp_years if min_years < 15 else experience

    return experience


def clean_required_education(education: Optional[str]) -> Optional[str]:
    """
    Homogénéise l'éducation requise :
    - Doctorat : > Bac +5, Doctorat
    - Master/Bac+5 : Bac +5, Master, équivalents (sans Doctorat)
    - Bac+3/+4 : Bac +3, Bac +4, ou les deux ensemble
    - Bac+2 : Bac +2
    - Bac et moins : Bac, Bac ou équivalent, BEP, CAP, Sans diplôme
    """
    if not education:
        return None

    edu_normalized = remove_accents(education.lower().strip())

    # Doctorat
    if "doctorat" in edu_normalized or "> bac +5" in edu_normalized:
        return "Doctorat"

    # Master/Bac+5 (sans Doctorat)
    if any(keyword in edu_normalized for keyword in ["bac +5", "bac+5", "master"]):
        if "doctorat" not in edu_normalized:
            return "Master/Bac+5"

    # Bac+3/+4 (chercher les deux ou l'un d'eux)
    has_bac3 = any(keyword in edu_normalized for keyword in ["bac +3", "bac+3"])
    has_bac4 = any(keyword in edu_normalized for keyword in ["bac +4", "bac+4"])
    if has_bac3 or has_bac4:
        return "Bac+3/+4"

    # Bac+2
    if any(keyword in edu_normalized for keyword in ["bac +2", "bac+2"]):
        return "Bac+2"

    # Bac et moins
    if any(
        keyword in edu_normalized for keyword in ["bac", "bep", "cap", "sans diplome"]
    ):
        return "Bac et moins"

    return education


# ===== GESTION DE LA BASE DE DONNÉES =====
def column_exists(table_name: str, column_name: str) -> bool:
    """Vérifie si une colonne existe dans une table."""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def create_cleaned_columns():
    """Crée les colonnes cleaned_* s'elles n'existent pas."""
    cleaned_columns = [
        "cleaned_title",
        "cleaned_contract_type",
        "cleaned_remote_mode",
        "cleaned_required_experience",
        "cleaned_required_education",
    ]

    with engine.connect() as connection:
        for col_name in cleaned_columns:
            if not column_exists("job_offers", col_name):
                logger.info(f"Créating column {col_name}...")
                alter_query = text(
                    f"ALTER TABLE job_offers ADD COLUMN {col_name} VARCHAR(255) DEFAULT NULL;"
                )
                connection.execute(alter_query)
                connection.commit()
                logger.info(f"Column {col_name} created")
            else:
                logger.info(f"Column {col_name} already exists")


def homogenize_titles():
    """Remplit la colonne cleaned_title."""
    logger.info("Processing titles...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        # Récupérer tous les enregistrements avec title
        jobs = session.query(JobOffer).filter(JobOffer.title.isnot(None)).all()

        count_updated = 0
        for job in jobs:
            if job.title:
                cleaned = clean_title(job.title)
                if cleaned and job.cleaned_title != cleaned:
                    job.cleaned_title = cleaned
                    count_updated += 1

        session.commit()
        logger.info(f"{count_updated} titles updated")
    finally:
        session.close()


def homogenize_contract_types():
    """Remplit la colonne cleaned_contract_type."""
    logger.info("Processing contract types...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        jobs = session.query(JobOffer).filter(JobOffer.contract_type.isnot(None)).all()

        count_updated = 0
        for job in jobs:
            if job.contract_type:
                cleaned = clean_contract_type(job.contract_type)
                if cleaned and job.cleaned_contract_type != cleaned:
                    job.cleaned_contract_type = cleaned
                    count_updated += 1

        session.commit()
        logger.info(f"{count_updated} contract types updated")
    finally:
        session.close()


def homogenize_remote_modes():
    """Remplit la colonne cleaned_remote_mode."""
    logger.info("Processing remote modes...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        jobs = session.query(JobOffer).filter(JobOffer.remote_mode.isnot(None)).all()

        count_updated = 0
        for job in jobs:
            if job.remote_mode:
                cleaned = clean_remote_mode(job.remote_mode)
                if cleaned and job.cleaned_remote_mode != cleaned:
                    job.cleaned_remote_mode = cleaned
                    count_updated += 1

        session.commit()
        logger.info(f"{count_updated} remote modes updated")
    finally:
        session.close()


def homogenize_required_experience():
    """Remplit la colonne cleaned_required_experience."""
    logger.info("Processing required experience...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        jobs = (
            session.query(JobOffer)
            .filter(JobOffer.required_experience.isnot(None))
            .all()
        )

        count_updated = 0
        for job in jobs:
            if job.required_experience:
                cleaned = clean_required_experience(job.required_experience)
                if cleaned and job.cleaned_required_experience != cleaned:
                    job.cleaned_required_experience = cleaned
                    count_updated += 1

        session.commit()
        logger.info(f"{count_updated} required experiences updated")
    finally:
        session.close()


def homogenize_required_education():
    """Remplit la colonne cleaned_required_education."""
    logger.info("Processing required education...")
    session = SessionLocal()

    try:
        from src.database.models import JobOffer

        jobs = (
            session.query(JobOffer)
            .filter(JobOffer.required_education.isnot(None))
            .all()
        )

        count_updated = 0
        for job in jobs:
            if job.required_education:
                cleaned = clean_required_education(job.required_education)
                if cleaned and job.cleaned_required_education != cleaned:
                    job.cleaned_required_education = cleaned
                    count_updated += 1

        session.commit()
        logger.info(f"{count_updated} required educations updated")
    finally:
        session.close()


# ===== FONCTION PRINCIPALE =====
def run_homogenization():
    """Exécute tout le processus d'homogénéisation."""
    logger.info("=" * 60)
    logger.info("Starting database homogenization...")
    logger.info("=" * 60)

    # Étape 1 : Créer les colonnes
    logger.info("\n[STEP 1] Creating columns...")
    create_cleaned_columns()

    # Étape 2 : Remplir les colonnes
    logger.info("\n[STEP 2] Filling columns with cleaned values...")
    homogenize_titles()
    homogenize_contract_types()
    homogenize_remote_modes()
    homogenize_required_experience()
    homogenize_required_education()

    logger.info("Homogenisation de la base de données terminée.")


if __name__ == "__main__":
    run_homogenization()
