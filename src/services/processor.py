import sys
from typing import cast
from loguru import logger
from src.database.database import SessionLocal
from src.database.models import JobOffer
from src.services.embedder import Embedder

# Configuration du logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


def build_content_to_vectorize(offer: JobOffer) -> str | None:
    """
    Construit le contenu à vectoriser en concaténant les colonnes enrichies avec poids.

    Structure (importance via duplication):
    - title (x3) : Titre répété 3 fois
    - ai_hard_skills (x2) : Compétences techniques répétées 2 fois
    - ai_sector : Secteur
    - ai_missions : Missions
    - ai_soft_skills : Compétences douces
    - job_profile : Profil demandé

    Args:
        offer: Offre d'emploi

    Returns:
        Contenu concaténé ou None si aucune donnée
    """
    parts: list[str] = []

    # Title x3 (importance maximale)
    if offer.title:
        parts.extend([cast(str, offer.title)] * 3)

    # ai_hard_skills x2 (haute importance)
    if offer.ai_hard_skills:
        parts.extend([cast(str, offer.ai_hard_skills)] * 2)

    # ai_sector (importance moyenne)
    if offer.ai_sector:
        parts.append(cast(str, offer.ai_sector))

    # ai_missions (importance moyenne)
    if offer.ai_missions:
        parts.append(cast(str, offer.ai_missions))

    # ai_soft_skills (importance moyenne)
    if offer.ai_soft_skills:
        parts.append(cast(str, offer.ai_soft_skills))

    # job_profile (importance moyenne-basse)
    if offer.job_profile:
        parts.append(cast(str, offer.job_profile))

    # Retourner None si aucune données pour éviter de vectoriser du vide
    if not parts:
        return None

    # Joindre avec " " pour séparer les concepts
    return " ".join(str(p).strip() for p in parts if p)


def process_embeddings(regenerate_content: bool = False):
    """
    Parcourt les offres en base et génère les embeddings.

    Processus:
    1. Build content_to_vectorize (concaténation intelligente des colonnes enrichies)
    2. Génère l'embedding à partir de content_to_vectorize
    3. Sauvegarde

    Args:
        regenerate_content: Si True, régénère content_to_vectorize et embeddings pour TOUTES les offres.
                           Si False (défaut), traite seulement les offres sans embedding.
    """
    db = SessionLocal()
    embedder = Embedder()

    try:
        if regenerate_content:
            # REINDEX : Traiter TOUTES les offres
            offers_to_process = db.query(JobOffer).all()
            mode = "REINDEX (toutes les offres)"
        else:
            # Mode normal : Seulement offres sans embedding
            offers_to_process = (
                db.query(JobOffer).filter(JobOffer.embedding.is_(None)).all()
            )
            mode = "Vectorisation initiale (offres sans embedding)"

        total = len(offers_to_process)

        if total == 0:
            logger.info("Aucune offre à traiter.")
            return

        logger.info(f"Début de {mode} : {total} offre(s)...")

        for index, offer in enumerate(offers_to_process):
            # 2. Construire content_to_vectorize
            content = build_content_to_vectorize(offer)
            setattr(offer, "content_to_vectorize", content)

            # 3. Générer embedding seulement s'il y a du contenu à vectoriser
            if content:
                vector = embedder.get_embedding(content)
                setattr(offer, "embedding", vector)
            else:
                logger.warning(
                    f"Offre {offer.id} : aucun contenu pour vectoriser "
                    "(title, ai_hard_skills, ai_sector, ai_missions, ai_soft_skills, job_profile tous vides)"
                )
                # En mode reindex, effacer aussi l'embedding stale pour garder la cohérence
                if regenerate_content:
                    setattr(offer, "embedding", None)

            # Log de progression tous les 50 éléments
            if (index + 1) % 50 == 0:
                logger.info(f"Progression : {index + 1}/{total}")

        # 4. Sauvegarde groupée
        db.commit()
        logger.success(f"Vectorisation terminée avec succès pour {total} offre(s).")

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors du traitement des embeddings : {e}")
    finally:
        db.close()
        logger.info("Session de base de données fermée.")


if __name__ == "__main__":
    process_embeddings()
