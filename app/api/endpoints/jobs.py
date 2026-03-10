"""
Endpoint de consultation des offres d'emploi.
Permet de parcourir et filtrer les offres en base.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, nullslast
from datetime import datetime, timedelta
from loguru import logger

from app.schemas.job import JobResponse, JobFilter, JobListResponse
from app.api.deps import get_db

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
    keywords: Optional[str] = Query(
        None, description="Mots-clés dans le titre ou description"
    ),
    location: Optional[str] = Query(
        None, description="Filtrer par localisation (ville, département, région)"
    ),
    city: Optional[str] = Query(None, description="Filtrer par ville spécifique"),
    department: Optional[str] = Query(None, description="Filtrer par département"),
    region: Optional[str] = Query(None, description="Filtrer par région"),
    contract_type: Optional[str] = Query(
        None, description="Type de contrat (CDI, CDD, Stage, etc.)"
    ),
    sector: Optional[str] = Query(None, description="Secteur d'activité"),
    remote_mode: Optional[str] = Query(None, description="Mode de télétravail"),
    experience: Optional[str] = Query(None, description="Niveau d'expérience (D/E/S)"),
    required_education: Optional[str] = Query(
        None, description="Niveau d'étude requis"
    ),
    company: Optional[str] = Query(None, description="Nom de l'entreprise"),
    source: Optional[str] = Query(None, description="Source de l'offre"),
    days_limit: int = Query(
        30, ge=1, le=365, description="Offres des N derniers jours"
    ),
    db: Session = Depends(get_db),
):
    """
    Liste paginée des offres d'emploi.

    **Filtres disponibles (tous optionnels)** :

    *Recherche textuelle* :
    - keywords : Mots-clés dans le titre ou description (ex: "Python", "Data")

    *Localisation* :
    - location : Localisation générique (ville, département, région)
    - city : Ville spécifique (ex: "Paris")
    - department : Département (ex: "Île-de-France")
    - region : Région (ex: "Occitanie")

    *Poste* :
    - contract_type : Type de contrat (ex: "CDI", "CDD", "Stage", "Alternance")
    - sector : Secteur d'activité
    - remote_mode : Mode de télétravail

    *Profil* :
    - experience : Niveau d'expérience (ex: "D" Débutant, "E", "S")
    - required_education : Niveau d'étude requis

    *Entreprise* :
    - company : Nom de l'entreprise
    - source : Source (ex: "France Travail", "HelloWork", "Welcome to the Jungle")

    *Dates* :
    - days_limit : Limiter aux N derniers jours (défaut: 30, basé sur date de publication de l'offre)

    **Pagination** :
    - page : Numéro de page (commence à 1)
    - page_size : Nombre de résultats par page (1-100, défaut: 20)

    **Exemples d'utilisation** :
    ```bash
    # Recherche à Paris avec CDI
    curl "http://localhost:8000/api/jobs?location=Paris&contract_type=CDI&page=1"

    # Recherche Data Engineer en Occitanie
    curl "http://localhost:8000/api/jobs?keywords=Data%20Engineer&region=Occitanie"

    # Filtrer par secteur et expérience
    curl "http://localhost:8000/api/jobs?sector=IT&experience=S"
    ```

    Args:
        page: Numéro de page
        page_size: Taille de page
        keywords: Recherche mots-clés (optionnel)
        location: Filtre localisation générique (optionnel)
        city: Filtre ville (optionnel)
        department: Filtre département (optionnel)
        region: Filtre région (optionnel)
        contract_type: Filtre type de contrat (optionnel)
        sector: Filtre secteur (optionnel)
        remote_mode: Filtre télétravail (optionnel)
        experience: Filtre expérience (optionnel)
        required_education: Filtre niveau étude (optionnel)
        company: Filtre entreprise (optionnel)
        source: Filtre source (optionnel)
        days_limit: Limite de jours (défaut: 30, basé sur date de publication)
        db: Session DB (injecté)

    Returns:
        JobListResponse: Liste paginée d'offres avec métadonnées

    Raises:
        Retourne une liste vide si aucune offre ne correspond
    """

    # Construction de la requête de base
    query = db.query(JobOffer)

    # Filtre sur la date de publication (date_publication) - date de parution de l'offre
    # Pour les offres sans date de publication, on les inclut aussi (fallback sur date_scraping)
    limit_date = datetime.now() - timedelta(days=days_limit)
    query = query.filter(
        or_(
            JobOffer.date_publication >= limit_date,
            (
                JobOffer.date_publication.is_(None)
                & (JobOffer.date_scraping >= limit_date)
            ),
        )
    )

    # Application des filtres optionnels
    filters_applied = {}

    if location:
        # Filtrer sur city, department, ou region
        query = query.filter(
            or_(
                JobOffer.city.ilike(f"%{location}%"),
                JobOffer.department.ilike(f"%{location}%"),
                JobOffer.region.ilike(f"%{location}%"),
            )
        )
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

    if city:
        query = query.filter(JobOffer.city.ilike(f"%{city}%"))
        filters_applied["city"] = city

    if department:
        query = query.filter(JobOffer.department.ilike(f"%{department}%"))
        filters_applied["department"] = department

    if region:
        query = query.filter(JobOffer.region.ilike(f"%{region}%"))
        filters_applied["region"] = region

    if sector:
        query = query.filter(JobOffer.sector.ilike(f"%{sector}%"))
        filters_applied["sector"] = sector

    if remote_mode:
        query = query.filter(JobOffer.remote_mode.ilike(f"%{remote_mode}%"))
        filters_applied["remote_mode"] = remote_mode

    if company:
        query = query.filter(JobOffer.company.ilike(f"%{company}%"))
        filters_applied["company"] = company

    if required_education:
        query = query.filter(
            JobOffer.required_education.ilike(f"%{required_education}%")
        )
        filters_applied["required_education"] = required_education

    # Tri par date de publication en descendant (plus récentes en premier)
    # Si date_publication est NULL, la mettre à la fin
    query = query.order_by(nullslast(JobOffer.date_publication.desc()))

    # Compte total (avant pagination)
    total = query.count()

    # Si aucun résultat, retourner une réponse vide au lieu d'une erreur
    if total == 0:
        logger.info(
            f"Aucune offre trouvée avec les filtres: {filters_applied}, days_limit={days_limit}"
        )

        # Construction des filtres appliqués
        filter_obj = None
        if filters_applied:
            filter_obj = JobFilter(
                keywords=filters_applied.get("keywords"),
                location=filters_applied.get("location"),
                city=filters_applied.get("city"),
                department=filters_applied.get("department"),
                region=filters_applied.get("region"),
                contract_type=filters_applied.get("contract_type"),
                sector=filters_applied.get("sector"),
                remote_mode=filters_applied.get("remote_mode"),
                experience=filters_applied.get("experience"),
                required_education=filters_applied.get("required_education"),
                company=filters_applied.get("company"),
                source=filters_applied.get("source"),
                days_limit=days_limit,
            )

        # Retourner une réponse vide avec total=0
        return JobListResponse(
            jobs=[],
            total=0,
            page=1,
            page_size=page_size,
            total_pages=0,
            filters_applied=filter_obj,
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
            # ===== IDENTIFIANTS =====
            id=str(job.id),
            url=str(job.url) if job.url else None,
            source=str(job.source) if job.source else None,
            # ===== POSTE =====
            title=str(job.title),
            sector=str(job.sector) if job.sector else None,
            contract_type=str(job.contract_type) if job.contract_type else None,
            remote_mode=str(job.remote_mode) if job.remote_mode else None,
            salary=str(job.salary) if job.salary else None,
            # ===== LOCALISATION =====
            city=str(job.city) if job.city else None,
            department=str(job.department) if job.department else None,
            region=str(job.region) if job.region else None,
            location=job.location,  # Propriété calculée du modèle
            # ===== ENTREPRISE =====
            company=str(job.company),
            company_size=str(job.company_size) if job.company_size else None,
            # ===== PROFIL DEMANDÉ =====
            required_experience=str(job.required_experience)
            if job.required_experience
            else None,
            required_education=str(job.required_education)
            if job.required_education
            else None,
            competences=str(job.competences) if job.competences else None,
            soft_skills=str(job.soft_skills) if job.soft_skills else None,
            languages=str(job.languages) if job.languages else None,
            # ===== CONTENU TEXTUEL =====
            description=description_preview,
            job_profile=str(job.job_profile) if job.job_profile else None,
            # ===== DATES =====
            date_publication=job.date_publication,  # type: ignore[arg-type]
            date_scraping=job.date_scraping,  # type: ignore[arg-type]
        )
        job_responses.append(job_response)

    # Construction des filtres appliqués
    filter_obj = None
    if filters_applied:
        filter_obj = JobFilter(
            keywords=filters_applied.get("keywords"),
            location=filters_applied.get("location"),
            city=filters_applied.get("city"),
            department=filters_applied.get("department"),
            region=filters_applied.get("region"),
            contract_type=filters_applied.get("contract_type"),
            sector=filters_applied.get("sector"),
            remote_mode=filters_applied.get("remote_mode"),
            experience=filters_applied.get("experience"),
            required_education=filters_applied.get("required_education"),
            company=filters_applied.get("company"),
            source=filters_applied.get("source"),
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
        # ===== IDENTIFIANTS =====
        id=str(job.id),
        url=str(job.url) if job.url else None,
        source=str(job.source) if job.source else None,
        # ===== POSTE =====
        title=str(job.title),
        sector=str(job.sector) if job.sector else None,
        contract_type=str(job.contract_type) if job.contract_type else None,
        remote_mode=str(job.remote_mode) if job.remote_mode else None,
        salary=str(job.salary) if job.salary else None,
        # ===== LOCALISATION =====
        city=str(job.city) if job.city else None,
        department=str(job.department) if job.department else None,
        region=str(job.region) if job.region else None,
        location=job.location,  # Propriété calculée du modèle
        # ===== ENTREPRISE =====
        company=str(job.company),
        company_size=str(job.company_size) if job.company_size else None,
        # ===== PROFIL DEMANDÉ =====
        required_experience=str(job.required_experience)
        if job.required_experience
        else None,
        required_education=str(job.required_education)
        if job.required_education
        else None,
        competences=str(job.competences) if job.competences else None,
        soft_skills=str(job.soft_skills) if job.soft_skills else None,
        languages=str(job.languages) if job.languages else None,
        # ===== CONTENU TEXTUEL =====
        description=str(job.description)
        if job.description
        else None,  # Description complète (pas tronquée)
        job_profile=str(job.job_profile) if job.job_profile else None,
        # ===== DATES =====
        date_publication=job.date_publication,  # type: ignore[arg-type]
        date_scraping=job.date_scraping,  # type: ignore[arg-type]
    )
