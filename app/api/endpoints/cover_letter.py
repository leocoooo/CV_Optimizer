"""
Endpoint de génération de lettre de motivation contextualisée.
"""

import tempfile
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import CVExtractionError, JobNotFoundError, LLMServiceError
from app.core.security import sanitize_filename, validate_file_upload
from app.schemas.cover_letter import CoverLetterResponse
from app.utils import run_in_thread
from src.database.models import JobOffer
from src.services.cv_reader import CVReader
from src.services.llm_advisor import JobAdvisor

router = APIRouter()


@router.post(
    "/cover-letter",
    response_model=CoverLetterResponse,
    tags=["LLM"],
    summary="Générer une lettre de motivation",
    description="Génère une lettre de motivation et sa version LaTeX à partir d'un CV et d'une offre.",
    status_code=200,
)
async def generate_cover_letter(
    file: UploadFile = File(..., description="CV au format PDF (max 5 MB)"),
    job_id: str = Form(..., description="ID de l'offre ciblée"),
    applicant_name: str = Form(..., description="Nom complet du candidat"),
    city: str = Form("", description="Ville du candidat"),
    email: str = Form("", description="Email du candidat"),
    phone: str = Form("", description="Téléphone du candidat"),
    letter_language: str = Form(
        "english", description="Langue de la lettre: english ou french"
    ),
    focus_note: str = Form("", description="Point à mettre en avant"),
    db: Session = Depends(get_db),
):
    """Produit une lettre de motivation contextualisée et sa version LaTeX."""
    start_time = time.time()

    offer = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not offer:
        raise JobNotFoundError(
            job_id=job_id,
            detail={"hint": "Utilisez /api/jobs ou /api/match pour choisir une offre."},
        )

    content = await file.read()
    validate_file_upload(
        filename=file.filename, file_size=len(content), content_type=file.content_type
    )

    safe_filename = sanitize_filename(file.filename)
    logger.info(f"Génération LM lancée pour {job_id} avec fichier {safe_filename}")

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

        advisor = JobAdvisor()
        applicant_profile = {
            "full_name": applicant_name.strip(),
            "city": city.strip(),
            "email": email.strip(),
            "phone": phone.strip(),
        }

        try:
            result = await run_in_thread(
                advisor.generate_cover_letter,
                cv_text,
                job_id,
                applicant_profile,
                letter_language,
                focus_note.strip(),
            )
        except Exception as exc:
            logger.error(f"Erreur de génération LM: {exc}")
            raise LLMServiceError(
                message="Le service de lettre de motivation est temporairement indisponible.",
                detail={"error": str(exc)[:120]},
            )

        execution_time = time.time() - start_time
        return CoverLetterResponse(
            job_id=str(offer.id),
            job_title=str(offer.title),
            company=str(offer.company),
            language=str(result["language"]),
            subject=str(result["subject"]),
            greeting=str(result["greeting"]),
            paragraphs=[str(item) for item in result["paragraphs"]],
            closing=str(result["closing"]),
            signature=str(result["signature"]),
            latex_source=str(result["latex_source"]),
            pdf_base64=str(result["pdf_base64"]),
            cv_length=len(cv_text),
            execution_time=round(execution_time, 3),
            llm_model=advisor.model_id,
        )

    finally:
        import os

        try:
            os.unlink(tmp_path)
        except Exception:
            pass
