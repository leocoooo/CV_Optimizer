import sys
from loguru import logger
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.database.models import JobOffer
from src.services.embedder import Embedder

# Configuration du logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>", level="INFO")

def process_embeddings():
    """
    Parcourt les offres en base et génère les embeddings pour celles qui n'en ont pas.
    """
    db = SessionLocal()
    embedder = Embedder()
    
    try:
        # 1. Sélection des offres sans embedding
        offers_to_process = db.query(JobOffer).filter(JobOffer.embedding.is_(None)).all()
        total = len(offers_to_process)
        
        if total == 0:
            logger.info("Toutes les offres sont déjà vectorisées.")
            return

        logger.info(f"Début de la vectorisation pour {total} offres...")

        for index, offer in enumerate(offers_to_process):
            if offer.description:
                # 2. Génération de l'embedding
                vector = embedder.get_embedding(offer.description)
                offer.embedding = vector
                
                # Log de progression tous les 50 éléments
                if (index + 1) % 50 == 0:
                    logger.info(f"Progression : {index + 1}/{total}")
        
        # 3. Sauvegarde groupée
        db.commit()
        logger.success(f"Vectorisation terminée avec succès pour {total} offres.")

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors du traitement des embeddings : {e}")
    finally:
        db.close()
        logger.info("Session de base de données fermée.")

if __name__ == "__main__":
    process_embeddings()