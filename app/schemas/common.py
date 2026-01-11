"""
Schémas communs réutilisables dans toute l'API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Réponse du endpoint de santé."""
    
    status: str = Field(..., description="Statut de l'API (healthy, degraded, unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Horodatage de la vérification")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class StatusResponse(BaseModel):
    """Réponse détaillée du statut de l'API."""
    
    status: str = Field(..., description="Statut général")
    database: str = Field(..., description="Statut de la base de données")
    timestamp: datetime = Field(default_factory=datetime.now)
    uptime_seconds: Optional[float] = Field(None, description="Temps de fonctionnement en secondes")
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message d'erreur détaillé")
    detail: Optional[Dict[str, Any]] = Field(None, description="Informations supplémentaires sur l'erreur")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class MessageResponse(BaseModel):
    """Réponse simple avec message."""
    
    message: str = Field(..., description="Message de réponse")
    success: bool = Field(True, description="Indicateur de succès")
    data: Optional[Dict[str, Any]] = Field(None, description="Données additionnelles")

