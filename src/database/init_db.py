import os
from sqlalchemy import create_all, create_engine
from sqlalchemy_utils import database_exists, create_database
from src.database.models import Base, JobOffer 
from dotenv import load_dotenv

# Chargement de l'URL depuis l'environnement 
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    engine = create_engine(DATABASE_URL)
    
    # Créer la database si elle n'existe pas
    if not database_exists(engine.url):
        create_database(engine.url)
        print("✅ Base de données créée.")

    # Activer l'extension pgvector (indispensable pour le matching)
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        print("✅ Extension pgvector activée.")

    # Créer les tables basées sur nos modèles SQLAlchemy
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès.")

if __name__ == "__main__":
    init_db()