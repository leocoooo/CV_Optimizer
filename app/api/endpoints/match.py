"""
Endpoint de matching CV/Offres.
Upload d'un CV et recherche des offres les plus pertinentes.
"""

import time
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from loguru import logger

from app.schemas.match import MatchResponse, JobMatch
from app.api.deps import get_db
from app.core.exceptions import CVExtractionError, NoMatchFoundError
from app.core.security import validate_file_upload, sanitize_filename
from app.utils import run_in_thread
from app.config import settings

# Import des services existants
from src.services.cv_reader import CVReader
from src.services.matcher import JobMatcher

router = APIRouter()


@router.post(
    "/match",
    response_model=MatchResponse,
    tags=["Matching"],
    summary="Matcher un CV avec les offres",
    description="Upload un CV (PDF) et retourne les offres d'emploi les plus pertinentes.",
    status_code=200,
)
async def match_cv(
    file: UploadFile = File(..., description="CV au format PDF (max 5 MB)"),
    location: Optional[str] = Form(None, description="Ville souhaitée"),
    contract_type: Optional[str] = Form(
        None, description="Type de contrat (CDI, CDD, etc.)"
    ),
    experience: Optional[str] = Form(None, description="Niveau d'expérience (D/E/S)"),
    days_limit: Optional[int] = Form(
        settings.DEFAULT_DAYS_LIMIT, description="Limiter aux N derniers jours"
    ),
    top_n: int = Form(
        settings.DEFAULT_TOP_N,
        ge=1,
        le=settings.MAX_TOP_N,
        description="Nombre de résultats",
    ),
    db: Session = Depends(get_db),
):
    """
    Matching CV/Offres avec recherche sémantique.
    
    **Processus** :
    1. Upload et validation du fichier PDF
    2. Extraction du texte du CV
    3. Génération de l'embedding du CV
    4. Recherche vectorielle dans la base d'offres
    5. Application des filtres optionnels
    6. Retour des N meilleures offres triées par score
    
    **Filtres optionnels** :
    - location : "Paris", "Lyon", "Remote", etc.
    - contract_type : "CDI", "CDD", "Stage", "Alternance"
    - experience : "D" (Débutant), "E" (Expérimenté), "S" (Senior)
    - days_limit : Limiter aux offres des N derniers jours (défaut: 30)
    - top_n : Nombre de résultats à retourner (1-50, défaut: 10)
    
    **Exemple d'utilisation** :
    ```bash
    curl -X POST "http://localhost:8000/api/match" \\
      -F "file=@mon_cv.pdf" \\
      -F "location=Paris" \\
      -F "contract_type=CDI" \\
      -F "top_n=10"
    ```
    
    Args:
        file: Fichier PDF du CV
        location: Localisation souhaitée (optionnel)
        contract_type: Type de contrat (optionnel)
        experience: Niveau d'expérience (optionnel)
        days_limit: Limite de jours (défaut: 30)
        top_n: Nombre de résultats (défaut: 10)
        db: Session DB (injecté)
    
    Returns:
        MatchResponse: Liste des offres matchées avec scores
    
    Raises:
        InvalidFileError: Fichier invalide (format, taille)
        CVExtractionError: Impossible d'extraire le texte
        NoMatchFoundError: Aucune offre correspondante
    """
    start_time = time.time()

    logger.info(f"Upload du CV : {file.filename}")

    # Lecture du contenu du fichier
    content = await file.read()

    # Validation du fichier
    validate_file_upload(
        filename=file.filename, file_size=len(content), content_type=file.content_type
    )

    # Sanitization du nom de fichier
    safe_filename = sanitize_filename(file.filename)
    logger.info(f" Fichier validé : {safe_filename} ({len(content)} bytes)")

    # Correction Swagger UI : si param == "string", on ignore le filtre
    if location == "string":
        location = None
    if contract_type == "string":
        contract_type = None
    if experience == "string":
        experience = None

    # Création d'un fichier temporaire pour l'extraction
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extraction du texte du CV (opération sync dans un thread)
        reader = CVReader()
        logger.info(" Extraction du texte du CV...")
        cv_text = await run_in_thread(reader.extract_text, tmp_path)

        if not cv_text or len(cv_text) < 50:
            raise CVExtractionError(
                message="Le CV est vide ou illisible. Vérifiez que le PDF contient du texte.",
                detail={"extracted_length": len(cv_text) if cv_text else 0},
            )

        logger.success(f" Texte extrait : {len(cv_text)} caractères")

        # Construction des filtres
        filters_dict: dict[str, str | int] = {}
        if location:
            filters_dict["location"] = location
        if contract_type:
            filters_dict["contract_type"] = contract_type
        if experience:
            filters_dict["experience"] = experience
        if days_limit:
            filters_dict["days_limit"] = days_limit

        logger.info(f" Recherche de matches (top {top_n}) avec filtres: {filters_dict}")

        # Recherche des offres correspondantes (opération sync dans un thread)
        matcher = JobMatcher()
        results = await run_in_thread(
            matcher.find_matches,
            profile_text=cv_text,
            days_limit=days_limit or 30,
            top_n=top_n,
            location=location,
            contract_type=contract_type,
            experience=experience,
        )

        if not results:
            raise NoMatchFoundError(
                message="Aucune offre ne correspond à votre profil avec les filtres appliqués.",
                detail={"filters": filters_dict, "cv_length": len(cv_text)},
            )

        logger.success(f" {len(results)} offres trouvées")

        # Conversion des résultats en schéma Pydantic
        matches = []
        for row in results:
            match = JobMatch(
                job_id=row.id,
                title=row.title,
                company=row.company,
                location=row.location,
                contract_type=row.contract_type,
                required_experience=row.required_experience,
                similarity_score=round(row.similarity_score, 4),
                url=row.url,
                creation_date=row.creation_date
                if hasattr(row, "creation_date")
                else None,
                source=row.source if hasattr(row, "source") else None,
            )
            matches.append(match)

        # Construction de la réponse
        execution_time = time.time() - start_time

        filters_applied = None
        if any([location, contract_type, experience]):
            filters_applied = {
                "location": location,
                "contract_type": contract_type,
                "experience": experience,
                "days_limit": days_limit or 30,
            }

        response = MatchResponse(
            matches=matches,
            total_matches=len(matches),
            cv_length=len(cv_text),
            execution_time=round(execution_time, 3),
            filters_applied=filters_applied,
        )

        logger.info(f" Matching terminé en {execution_time:.3f}s")

        return response

    finally:
        # Nettoyage du fichier temporaire
        import os

        try:
            os.unlink(tmp_path)
        except Exception:
            pass
