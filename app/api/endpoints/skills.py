"""
Endpoint de comparaison des compétences entre un CV et une offre.
"""

import tempfile

from fastapi import APIRouter, Depends, File, Form, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import CVExtractionError, JobNotFoundError
from app.core.security import sanitize_filename, validate_file_upload
from app.schemas.skills import SkillComparisonResponse
from app.utils import run_in_thread
from src.database.models import JobOffer
from src.services.cv_reader import CVReader
from src.services.skill_gap_analyzer import SkillGapAnalyzer

router = APIRouter()


@router.post(
    "/skills/compare",
    response_model=SkillComparisonResponse,
    tags=["Skills"],
    summary="Comparer les compétences d'un CV avec une offre",
    description="Upload un CV PDF et retourne les compétences visibles, manquantes et les signaux d'alignement.",
    status_code=200,
)
async def compare_skills(
    file: UploadFile = File(..., description="CV au format PDF"),
    job_id: str = Form(..., description="ID de l'offre ciblée"),
    db: Session = Depends(get_db),
):
    """Compare un CV avec les compétences demandées par une offre."""
    offer = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not offer:
        raise JobNotFoundError(
            job_id=job_id,
            detail={"hint": "Utilisez /api/jobs ou /api/match pour trouver une offre."},
        )

    logger.info(f"Comparaison de compétences pour l'offre {job_id}")

    content = await file.read()
    validate_file_upload(
        filename=file.filename, file_size=len(content), content_type=file.content_type
    )

    safe_filename = sanitize_filename(file.filename)
    logger.info(f"Fichier validé pour comparaison de compétences: {safe_filename}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        reader = CVReader()
        cv_text = await run_in_thread(reader.extract_text, tmp_path)

        if not cv_text or len(cv_text) < 50:
            raise CVExtractionError(
                message="Le CV est vide ou illisible.",
                detail={"extracted_length": len(cv_text) if cv_text else 0},
            )

        analyzer = SkillGapAnalyzer()
        comparison = await run_in_thread(analyzer.compare, cv_text, offer)
        return SkillComparisonResponse(**comparison)

    finally:
        import os

        try:
            os.unlink(tmp_path)
        except Exception:
            pass
