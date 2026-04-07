"""
Endpoint de chat LLM contextualisé avec CV et offre.
"""

import json
import tempfile
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.core.exceptions import CVExtractionError, JobNotFoundError, LLMServiceError
from app.core.security import sanitize_filename, validate_file_upload
from app.schemas.chat import ChatResponse
from app.utils import run_in_thread
from src.database.models import JobOffer
from src.services.cv_reader import CVReader
from src.services.llm_advisor import JobAdvisor

router = APIRouter()


def _parse_history(history_json: str) -> list[dict[str, str]]:
    """Valide et normalise l'historique envoyé par l'UI."""
    try:
        raw_history = json.loads(history_json or "[]")
    except json.JSONDecodeError:
        return []

    if not isinstance(raw_history, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in raw_history[-8:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        normalized.append({"role": role, "content": content[:2000]})
    return normalized


@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["LLM"],
    summary="Discuter avec le coach CV",
    description="Chat contextuel avec le LLM à partir d'un CV et d'une offre ciblée.",
    status_code=200,
)
async def chat_about_cv(
    file: UploadFile = File(..., description="CV au format PDF (max 5 MB)"),
    job_id: str = Form(..., description="ID de l'offre ciblée"),
    message: str = Form(..., description="Message utilisateur"),
    history: str = Form("[]", description="Historique JSON user/assistant"),
    db: Session = Depends(get_db),
):
    """Permet d'échanger avec le LLM sur les modifications du CV."""
    start_time = time.time()

    offer = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not offer:
        raise JobNotFoundError(
            job_id=job_id,
            detail={"hint": "Utilisez /api/jobs ou /api/match pour choisir une offre."},
        )

    if not message or not message.strip():
        raise LLMServiceError(
            message="Le message utilisateur est vide.",
            detail={"hint": "Envoyez une demande de modification ou une question."},
        )

    content = await file.read()
    validate_file_upload(
        filename=file.filename, file_size=len(content), content_type=file.content_type
    )

    safe_filename = sanitize_filename(file.filename)
    logger.info(f"Chat CV lancé pour {job_id} avec fichier {safe_filename}")

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
        parsed_history = _parse_history(history)

        try:
            reply = await run_in_thread(
                advisor.chat_about_modifications,
                cv_text,
                job_id,
                message.strip(),
                parsed_history,
            )
        except Exception as exc:
            logger.error(f"Erreur de chat LLM: {exc}")
            raise LLMServiceError(
                message="Le coach LLM est temporairement indisponible.",
                detail={"error": str(exc)[:100]},
            )

        if not reply or "temporairement indisponible" in reply:
            raise LLMServiceError(
                message="Le coach LLM n'a pas pu répondre.",
                detail={"model": advisor.model_id, "timeout": settings.LLM_TIMEOUT_SECONDS},
            )

        execution_time = time.time() - start_time
        return ChatResponse(
            job_id=str(offer.id),
            job_title=str(offer.title),
            company=str(offer.company),
            reply=reply,
            execution_time=round(execution_time, 3),
            llm_model=advisor.model_id,
        )

    finally:
        import os

        try:
            os.unlink(tmp_path)
        except Exception:
            pass
