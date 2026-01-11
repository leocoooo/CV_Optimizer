"""
Dépendances réutilisables pour les endpoints FastAPI.
Ces fonctions sont injectées via Depends() dans les endpoints.
"""

from typing import Generator
from sqlalchemy.orm import Session

from src.database.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance pour obtenir une session de base de données.
    
    Crée une nouvelle session SQLAlchemy pour chaque requête,
    et la ferme automatiquement à la fin (même en cas d'erreur).
    
    Yields:
        Session: Session SQLAlchemy pour interagir avec la DB
    
    Usage dans un endpoint:
        @app.get("/jobs")
        async def get_jobs(db: Session = Depends(get_db)):
            jobs = db.query(JobOffer).all()
            return jobs
    
    Note:
        - La session est automatiquement fermée après la requête
        - En cas d'erreur, la session est quand même fermée (finally)
        - Pattern recommandé par SQLAlchemy pour FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
