"""
Endpoints de santé et statut de l'API.
"""

import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.common import HealthResponse, StatusResponse
from app.api.deps import get_db


router = APIRouter()

# Variable globale pour tracker l'uptime
_start_time = time.time()


@router.get("/", include_in_schema=False)
async def root():
    """
    Page d'accueil de l'API.
    Redirige vers la documentation interactive.
    """
    return {
        "message": "Bienvenue sur CV-Optimizer API",
        "documentation": "/docs",
        "health": "/health",
        "status": "/api/v1/status"
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check simple",
    description="Vérifie que l'API répond. Utile pour load balancers et monitoring."
)
async def health_check():
    """
    Health check basique.
    
    Retourne simplement un statut "healthy" si l'API répond.
    Endpoint léger pour vérifications fréquentes (ex: toutes les 10s).
    
    Returns:
        HealthResponse: Statut et timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now()
    )


@router.get(
    "/api/v1/status",
    response_model=StatusResponse,
    tags=["Health"],
    summary="Statut détaillé de l'API",
    description="Informations complètes sur l'état de l'API et ses dépendances."
)
async def get_status(
    db: Session = Depends(get_db)
):
    """
    Statut détaillé de l'API.
    
    Vérifie :
    - Réponse de l'API
    - Connexion à la base de données
    - Version et configuration
    - Uptime
    
    Args:
        db: Session de base de données
        config: Configuration de l'application
    
    Returns:
        StatusResponse: Statut détaillé
    """
    # Vérification de la connexion DB
    database_status = "connected"
    try:
        # Test simple de connexion
        db.execute(text("SELECT 1"))
    except Exception as e:
        database_status = f"error: {str(e)[:50]}"
    
    # Calcul de l'uptime
    uptime = time.time() - _start_time
    
    # Détermination du statut global
    overall_status = "healthy" if database_status == "connected" else "degraded"
    
    return StatusResponse(
        status=overall_status,
        database=database_status,
        timestamp=datetime.now(),
        uptime_seconds=round(uptime, 2)
    )
