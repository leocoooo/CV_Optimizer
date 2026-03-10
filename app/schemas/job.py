"""
Schémas pour les offres d'emploi.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class JobFilter(BaseModel):
    """Filtres pour la recherche d'offres."""

    model_config = ConfigDict(from_attributes=True)

    # ===== RECHERCHE TEXTUELLE =====
    keywords: Optional[str] = Field(
        None, description="Mots-clés dans le titre ou la description"
    )

    # ===== LOCALISATION =====
    location: Optional[str] = Field(
        None, description="Filtrer par localisation (ville, département, région)"
    )
    city: Optional[str] = Field(None, description="Filtrer par ville spécifique")
    department: Optional[str] = Field(None, description="Filtrer par département")
    region: Optional[str] = Field(None, description="Filtrer par région")

    # ===== POSTE =====
    contract_type: Optional[str] = Field(
        None, description="Type de contrat (CDI, CDD, Stage, Alternance, etc.)"
    )
    sector: Optional[str] = Field(None, description="Secteur d'activité")
    remote_mode: Optional[str] = Field(None, description="Mode de télétravail")

    # ===== PROFIL =====
    experience: Optional[str] = Field(None, description="Niveau d'expérience (D/E/S)")
    required_education: Optional[str] = Field(None, description="Niveau d'étude requis")

    # ===== ENTREPRISE =====
    company: Optional[str] = Field(None, description="Nom de l'entreprise")
    source: Optional[str] = Field(
        None,
        description="Source de l'offre (Welcome to the Jungle, HelloWork, France Travail)",
    )

    # ===== DATES =====
    days_limit: int = Field(
        30,
        ge=1,
        le=365,
        description="Offres des N derniers jours (basé sur date_scraping)",
    )


class JobResponse(BaseModel):
    """Représentation d'une offre d'emploi."""

    model_config = ConfigDict(from_attributes=True)

    # ===== IDENTIFIANTS =====
    id: str = Field(..., description="Identifiant unique")
    url: Optional[str] = Field(None, description="Lien vers l'offre")
    source: Optional[str] = Field(
        None, description="Source (Welcome to the Jungle, HelloWork, France Travail)"
    )

    # ===== POSTE =====
    title: str = Field(..., description="Titre du poste")
    sector: Optional[str] = Field(None, description="Secteur d'activité")
    contract_type: Optional[str] = Field(
        None, description="Type de contrat (CDI, CDD, Stage, etc.)"
    )
    remote_mode: Optional[str] = Field(None, description="Mode de télétravail")
    salary: Optional[str] = Field(None, description="Salaire proposé")

    # ===== LOCALISATION =====
    city: Optional[str] = Field(None, description="Ville")
    department: Optional[str] = Field(None, description="Département")
    region: Optional[str] = Field(None, description="Région")
    location: Optional[str] = Field(
        None, description="Localisation composée (city - department - region)"
    )

    # ===== ENTREPRISE =====
    company: str = Field(..., description="Entreprise")
    company_size: Optional[str] = Field(None, description="Taille de l'entreprise")

    # ===== PROFIL DEMANDÉ =====
    required_experience: Optional[str] = Field(None, description="Expérience requise")
    required_education: Optional[str] = Field(None, description="Niveau d'étude requis")
    competences: Optional[str] = Field(
        None, description="Compétences requises (comma-separated)"
    )
    soft_skills: Optional[str] = Field(
        None, description="Soft skills (compétences comportementales)"
    )
    languages: Optional[str] = Field(None, description="Langues requises")

    # ===== CONTENU TEXTUEL =====
    description: Optional[str] = Field(
        None, description="Description complète du poste"
    )
    job_profile: Optional[str] = Field(
        None, description="Profil demandé / Qualifications"
    )

    # ===== DATES =====
    date_publication: Optional[datetime] = Field(
        None, description="Date de publication de l'offre"
    )
    date_scraping: Optional[datetime] = Field(
        None, description="Date de scraping/insertion en base"
    )


class JobListResponse(BaseModel):
    """Réponse paginée avec liste d'offres."""

    model_config = ConfigDict(from_attributes=True)

    jobs: List[JobResponse] = Field(..., description="Liste des offres")
    total: int = Field(..., description="Nombre total d'offres correspondantes")
    page: int = Field(..., ge=1, description="Page actuelle")
    page_size: int = Field(..., ge=1, le=100, description="Taille de la page")
    total_pages: int = Field(..., description="Nombre total de pages")
    filters_applied: Optional[JobFilter] = Field(
        None, description="Filtres appliqués à la recherche"
    )
