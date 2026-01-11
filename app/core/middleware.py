"""
Middleware pour l'API FastAPI.
Gère CORS, logging des requêtes, request ID, et gestion des erreurs.
"""

from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings


def setup_cors(app):
    """
    Configure le middleware CORS pour autoriser les requêtes cross-origin.
    
    Args:
        app: Instance FastAPI
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
        allow_headers=["*"],  # Tous les headers autorisés
    )
    logger.info(f"CORS configuré pour : {settings.ALLOWED_ORIGINS}")

