import os
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database
from src.database.models import Base 
from dotenv import load_dotenv

# Chargement de l'URL depuis l'environnement 
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    engine = create_engine(DATABASE_URL)
    
    # 1. Créer la database si elle n'existe pas
    if not database_exists(engine.url):
        create_database(engine.url)
        print("✅ Base de données créée.")

    # 2. Activer l'extension pgvector
    with engine.connect() as conn:
        # On utilise text() pour les commandes SQL brutes
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
        print("✅ Extension pgvector activée.")

    # 3. Créer les tables
    # C'est ici que le changement opère : on appelle create_all sur metadata
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès.")

if __name__ == "__main__":
    init_db()