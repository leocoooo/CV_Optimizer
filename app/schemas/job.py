"""
Schémas pour les offres d'emploi.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobFilter(BaseModel):
    """Filtres pour la recherche d'offres."""
    
    location: Optional[str] = Field(None, description="Filtrer par localisation")
    contract_type: Optional[str] = Field(None, description="Type de contrat")
    experience: Optional[str] = Field(None, description="Niveau d'expérience (D/E/S)")
    source: Optional[str] = Field(None, description="Source de l'offre")
    keywords: Optional[str] = Field(None, description="Mots-clés dans le titre ou la description")
    days_limit: int = Field(30, ge=1, le=365, description="Offres des N derniers jours")


class JobResponse(BaseModel):
    """Représentation d'une offre d'emploi."""
    
    id: str = Field(..., description="Identifiant unique")
    title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Entreprise")
    location: Optional[str] = Field(None, description="Localisation")
    description: Optional[str] = Field(None, description="Description du poste")
    contract_type: Optional[str] = Field(None, description="Type de contrat")
    required_experience: Optional[str] = Field(None, description="Expérience requise")
    url: Optional[str] = Field(None, description="Lien vers l'offre")
    source: Optional[str] = Field(None, description="Source")
    creation_date: Optional[datetime] = Field(None, description="Date de publication")
    actualisation_date: Optional[datetime] = Field(None, description="Date de mise à jour")
    
    class Config:
        from_attributes = True  # Pour compatibility avec SQLAlchemy


class JobListResponse(BaseModel):
    """Réponse paginée avec liste d'offres."""
    
    jobs: List[JobResponse] = Field(..., description="Liste des offres")
    total: int = Field(..., description="Nombre total d'offres correspondantes")
    page: int = Field(..., ge=1, description="Page actuelle")
    page_size: int = Field(..., ge=1, le=100, description="Taille de la page")
    total_pages: int = Field(..., description="Nombre total de pages")
