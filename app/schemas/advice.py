"""
Schémas pour le endpoint de conseils LLM.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AdviceRequest(BaseModel):
    """Requête pour obtenir des conseils d'optimisation CV."""
    
    job_id: str = Field(..., description="Identifiant de l'offre d'emploi ciblée")


class AdviceResponse(BaseModel):
    """Réponse avec les conseils du LLM."""
    
    job_id: str = Field(..., description="ID de l'offre analysée")
    job_title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Nom de l'entreprise")
    advice: str = Field(..., description="Conseils détaillés générés par le LLM")
    cv_length: int = Field(..., description="Nombre de caractères du CV analysé")
    execution_time: float = Field(..., description="Temps d'exécution en secondes")
    llm_model: Optional[str] = Field(None, description="Modèle LLM utilisé")
