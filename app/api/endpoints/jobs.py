"""
Endpoint de consultation des offres d'emploi.
Permet de parcourir et filtrer les offres en base.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from loguru import logger

from app.schemas.job import JobResponse, JobFilter, JobListResponse
from app.api.deps import get_db
from app.core.exceptions import NoMatchFoundError

# Import du modèle
from src.database.models import JobOffer

router = APIRouter()


@router.get(
    "/jobs",
    response_model=JobListResponse,
    tags=["Jobs"],
    summary="Liste des offres d'emploi",
    description="Parcourt les offres en base avec filtres et pagination.",
    status_code=200,
)
async def get_jobs(
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    location: Optional[str] = Query(None, description="Filtrer par localisation"),
    contract_type: Optional[str] = Query(None, description="Type de contrat"),
    experience: Optional[str] = Query(None, description="Niveau d'expérience (D/E/S)"),
    source: Optional[str] = Query(None, description="Source de l'offre"),
    keywords: Optional[str] = Query(None, description="Mots-clés dans le titre"),
    days_limit: int = Query(
        30, ge=1, le=365, description="Offres des N derniers jours"
    ),
    db: Session = Depends(get_db),
):
    """
    Liste paginée des offres d'emploi.

    **Filtres disponibles** :
    - location : "Paris", "Lyon", etc.
    - contract_type : "CDI", "CDD", "Stage", "Alternance"
    - experience : "D" (Débutant), "E", "S"
    - source : "France Travail", "HelloWork", "Welcome to the Jungle"
    - keywords : Recherche dans le titre (ex: "Python", "Data")
    - days_limit : Limiter aux N derniers jours (défaut: 30)

    **Pagination** :
    - page : Numéro de page (commence à 1)
    - page_size : Nombre de résultats par page (1-100, défaut: 20)

    **Exemple d'utilisation** :
    ```bash
    curl "http://localhost:8000/api/jobs?location=Paris&contract_type=CDI&page=1&page_size=20"
    ```

    Args:
        page: Numéro de page
        page_size: Taille de page
        location: Filtre localisation (optionnel)
        contract_type: Filtre type de contrat (optionnel)
        experience: Filtre expérience (optionnel)
        source: Filtre source (optionnel)
        keywords: Recherche mots-clés (optionnel)
        days_limit: Limite de jours (défaut: 30)
        db: Session DB (injecté)

    Returns:
        JobListResponse: Liste paginée d'offres avec métadonnées

    Raises:
        NoMatchFoundError: Aucune offre avec ces filtres
    """

    # Construction de la requête de base
    query = db.query(JobOffer)

    # Filtre sur la date d'actualisation (offres récentes)
    limit_date = datetime.now() - timedelta(days=days_limit)
    query = query.filter(JobOffer.actualisation_date >= limit_date)

    # Application des filtres optionnels
    filters_applied = {}

    if location:
        query = query.filter(JobOffer.location.ilike(f"%{location}%"))
        filters_applied["location"] = location

    if contract_type:
        query = query.filter(JobOffer.contract_type == contract_type)
        filters_applied["contract_type"] = contract_type

    if experience:
        query = query.filter(JobOffer.required_experience.ilike(f"%{experience}%"))
        filters_applied["experience"] = experience

    if source:
        query = query.filter(JobOffer.source == source)
        filters_applied["source"] = source

    if keywords:
        # Recherche dans le titre ou la description
        search_pattern = f"%{keywords}%"
        query = query.filter(
            or_(
                JobOffer.title.ilike(search_pattern),
                JobOffer.description.ilike(search_pattern),
            )
        )
        filters_applied["keywords"] = keywords

    # Tri par date de mise à jour décroissante
    query = query.order_by(JobOffer.actualisation_date.desc())

    # Compte total (avant pagination)
    total = query.count()

    if total == 0:
        raise NoMatchFoundError(
            message="Aucune offre ne correspond à ces critères.",
            detail={"filters": filters_applied, "days_limit": days_limit},
        )

    # Calcul de la pagination
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    # Validation de la page demandée
    if page > total_pages:
        page = total_pages

    # Application de la pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Exécution de la requête
    jobs = query.all()

    logger.info(
        f" {len(jobs)} offres retournées (page {page}/{total_pages}, total: {total})"
    )

    # Conversion en schéma Pydantic
    job_responses = []
    for job in jobs:
        # Tronquer la description pour l'aperçu (500 caractères max)
        description_preview = None
        if job.description:
            description_preview = str(job.description)[:500]
            if len(str(job.description)) > 500:
                description_preview += "..."

        job_response = JobResponse(
            id=str(job.id),
            title=str(job.title),
            company=str(job.company),
            location=str(job.location) if job.location else None,
            description=description_preview,
            contract_type=str(job.contract_type) if job.contract_type else None,
            required_experience=str(job.required_experience)
            if job.required_experience
            else None,
            url=str(job.url) if job.url else None,
            source=str(job.source) if job.source else None,
            creation_date=getattr(job, "creation_date", None),
            actualisation_date=getattr(job, "actualisation_date", None),
        )
        job_responses.append(job_response)

    # Construction des filtres appliqués
    filter_obj = None
    if filters_applied:
        filter_obj = JobFilter(
            location=filters_applied.get("location"),
            contract_type=filters_applied.get("contract_type"),
            experience=filters_applied.get("experience"),
            source=filters_applied.get("source"),
            keywords=filters_applied.get("keywords"),
            days_limit=days_limit,
        )

    # Réponse finale
    response = JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        filters_applied=filter_obj,
    )

    return response


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Détails d'une offre",
    description="Récupère les détails complets d'une offre spécifique.",
    status_code=200,
)
async def get_job_details(job_id: str, db: Session = Depends(get_db)):
    """
    Détails d'une offre d'emploi.

    Retourne toutes les informations d'une offre, incluant la description complète.

    Args:
        job_id: Identifiant de l'offre
        db: Session DB (injecté)

    Returns:
        JobResponse: Détails complets de l'offre

    Raises:
        JobNotFoundError: Offre introuvable
    """
    from app.core.exceptions import JobNotFoundError

    job = db.query(JobOffer).filter(JobOffer.id == job_id).first()

    if not job:
        raise JobNotFoundError(job_id=job_id)

    logger.info(f"Détails de l'offre {job_id} : {job.title}")

    # Retourne la description complète (pas tronquée)
    return JobResponse(
        id=str(job.id),
        title=str(job.title),
        company=str(job.company),
        location=str(job.location) if job.location else None,
        description=str(job.description) if job.description else None,
        contract_type=str(job.contract_type) if job.contract_type else None,
        required_experience=str(job.required_experience)
        if job.required_experience
        else None,
        url=str(job.url) if job.url else None,
        source=str(job.source) if job.source else None,
        creation_date=getattr(job, "creation_date", None),
        actualisation_date=getattr(job, "actualisation_date", None),
    )
