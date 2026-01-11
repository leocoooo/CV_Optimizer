"""
Schémas pour le endpoint de matching CV/Offres.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobMatch(BaseModel):
    """Une offre matchée avec son score de similarité."""
    
    job_id: str = Field(..., description="Identifiant unique de l'offre")
    title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Nom de l'entreprise")
    location: Optional[str] = Field(None, description="Localisation")
    contract_type: Optional[str] = Field(None, description="Type de contrat")
    required_experience: Optional[str] = Field(None, description="Expérience requise")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Score de similarité (0-1)")
    url: Optional[str] = Field(None, description="Lien vers l'offre")
    creation_date: Optional[datetime] = Field(None, description="Date de publication")
    source: Optional[str] = Field(None, description="Source de l'offre")


class MatchResponse(BaseModel):
    """Réponse du endpoint de matching."""
    
    matches: List[JobMatch] = Field(..., description="Liste des offres correspondantes triées par score")
    total_matches: int = Field(..., description="Nombre total de correspondances trouvées")
    cv_length: int = Field(..., description="Nombre de caractères extraits du CV")
    execution_time: float = Field(..., description="Temps d'exécution en secondes")
