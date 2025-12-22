import os
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from loguru import logger
from dotenv import load_dotenv

# NE PAS MODIFIER : C'est ici que SQLAlchemy découvre les tables
from src.database.database import Base
from src.database.models import JobOffer 

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    engine = create_engine(DATABASE_URL)
    
    # Création de la base de données si nécessaire
    if not database_exists(engine.url):
        create_database(engine.url)
        logger.info("Base de données créée.")

    # Activation de l'extension pgvector pour la recherche sémantique
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.success("Extension pgvector activée.")
    except Exception as e:
        logger.error(f"Erreur lors de l'activation de pgvector : {e}")

    # Création des tables définies dans les modèles importés
    try:
        # Comme JobOffer est importé, Base.metadata contient maintenant la structure
        Base.metadata.create_all(bind=engine)
        logger.success("Tables créées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables : {e}")

if __name__ == "__main__":
    init_db()