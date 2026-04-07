"""
Schémas pour les données agrégées du dashboard public.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BreakdownItem(BaseModel):
    """Élément de répartition pour une métrique agrégée."""

    label: str = Field(..., description="Libellé de la catégorie")
    value: int = Field(..., ge=0, description="Valeur associée")


class DashboardJobPreview(BaseModel):
    """Aperçu d'une offre pour les vues dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Identifiant unique de l'offre")
    title: str = Field(..., description="Titre du poste")
    company: str = Field(..., description="Entreprise")
    location: Optional[str] = Field(None, description="Localisation composée")
    contract_type: Optional[str] = Field(None, description="Type de contrat")
    remote_mode: Optional[str] = Field(None, description="Mode de télétravail")
    salary: Optional[str] = Field(None, description="Salaire proposé")
    source: Optional[str] = Field(None, description="Source de l'offre")
    url: Optional[str] = Field(None, description="URL de l'offre")
    date_publication: Optional[datetime] = Field(
        None, description="Date de publication de l'offre"
    )
    date_scraping: Optional[datetime] = Field(
        None, description="Date d'ingestion dans la base"
    )


class DashboardResponse(BaseModel):
    """Réponse agrégée pour le cockpit public."""

    total_jobs: int = Field(..., ge=0, description="Nombre total d'offres")
    indexed_jobs: int = Field(..., ge=0, description="Nombre d'offres vectorisées")
    indexing_rate: float = Field(
        ..., ge=0, le=100, description="Taux d'indexation en pourcentage"
    )
    active_sources: int = Field(..., ge=0, description="Nombre de sources actives")
    last_ingested_at: Optional[datetime] = Field(
        None, description="Dernière date d'ingestion connue"
    )
    source_breakdown: list[BreakdownItem] = Field(
        default_factory=list, description="Répartition par source"
    )
    contract_breakdown: list[BreakdownItem] = Field(
        default_factory=list, description="Répartition par type de contrat"
    )
    region_breakdown: list[BreakdownItem] = Field(
        default_factory=list, description="Répartition par région"
    )
    top_hard_skills: list[BreakdownItem] = Field(
        default_factory=list,
        description="Compétences techniques les plus fréquentes dans les offres",
    )
    recent_jobs: list[DashboardJobPreview] = Field(
        default_factory=list, description="Dernières offres disponibles"
    )
