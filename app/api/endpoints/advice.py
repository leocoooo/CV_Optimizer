"""
Endpoint de conseils LLM personnalisés.
Génère des recommandations pour optimiser un CV pour une offre spécifique.
"""

import time
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from loguru import logger

from app.schemas.advice import AdviceResponse
from app.api.deps import get_db
from app.core.exceptions import CVExtractionError, JobNotFoundError, LLMServiceError
from app.core.security import validate_file_upload, sanitize_filename
from app.utils import run_in_thread
from app.config import settings

# Import des services
from src.services.cv_reader import CVReader
from src.services.llm_advisor import JobAdvisor
from src.database.models import JobOffer

router = APIRouter()


@router.post(
    "/advice",
    response_model=AdviceResponse,
    tags=["LLM"],
    summary="Obtenir des conseils d'optimisation CV",
    description="Upload un CV et obtient des conseils personnalisés du LLM (Qwen 2.5) pour une offre spécifique.",
    status_code=200
)
async def get_cv_advice(
    file: UploadFile = File(..., description="CV au format PDF (max 5 MB)"),
    job_id: str = Form(..., description="ID de l'offre d'emploi ciblée"),
    db: Session = Depends(get_db)
):
    """
    Conseils personnalisés pour optimiser un CV.
    
    **Processus** :
    1. Upload et validation du CV
    2. Extraction du texte
    3. Vérification de l'existence de l'offre
    4. Appel au LLM Qwen 2.5 via Hugging Face
    5. Génération de conseils structurés
    
    **Le LLM analyse** :
    - Points forts du candidat
    - Compétences manquantes
    - Proposition d'accroche personnalisée
    
    **Exemple d'utilisation** :
    ```bash
    curl -X POST "http://localhost:8000/api/advice" \\
      -F "file=@mon_cv.pdf" \\
      -F "job_id=123456"
    ```
    
    Args:
        file: Fichier PDF du CV
        job_id: Identifiant de l'offre ciblée
        db: Session DB (injecté)
    
    Returns:
        AdviceResponse: Conseils détaillés du LLM
    
    Raises:
        InvalidFileError: Fichier invalide
        CVExtractionError: Impossible d'extraire le texte
        JobNotFoundError: Offre introuvable
        LLMServiceError: Service LLM indisponible
    """
    start_time = time.time()    
    logger.info("Demande de conseils pour l'offre {job_id}")
    
    # Vérification de l'existence de l'offre en base
    offer = db.query(JobOffer).filter(JobOffer.id == job_id).first()
    if not offer:
        raise JobNotFoundError(
            job_id=job_id,
            detail={"hint": "Utilisez /api/match pour trouver des offres"}
        )
    
    logger.info(f"Offre trouvée : {offer.title} chez {offer.company}")
    
    # Lecture du contenu du fichier
    content = await file.read()
    
    # Validation du fichier
    validate_file_upload(
        filename=file.filename,
        file_size=len(content),
        content_type=file.content_type
    )
    
    safe_filename = sanitize_filename(file.filename)
    logger.info(f" Fichier validé : {safe_filename}")
    
    # Création d'un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Extraction du texte du CV
        reader = CVReader()
        logger.info(" Extraction du texte du CV...")
        cv_text = await run_in_thread(reader.extract_text, tmp_path)
        
        if not cv_text or len(cv_text) < 50:
            raise CVExtractionError(
                message="Le CV est vide ou illisible.",
                detail={"extracted_length": len(cv_text) if cv_text else 0}
            )
        
        logger.success(f" Texte extrait : {len(cv_text)} caractères")
        
        # Appel au service LLM (Qwen 2.5 via Hugging Face)
        logger.info(" Appel au LLM pour génération des conseils...")
        
        advisor = JobAdvisor()
        
        try:
            # Appel synchrone dans un thread (peut prendre 5-20s)
            advice_text = await run_in_thread(
                advisor.get_advice,
                cv_text=cv_text,
                job_id=job_id
            )
            
            if not advice_text or "temporairement indisponible" in advice_text:
                raise LLMServiceError(
                    message="Le service LLM n'a pas pu générer de conseils.",
                    detail={
                        "model": advisor.model_id,
                        "timeout": settings.LLM_TIMEOUT_SECONDS
                    }
                )
            
        except Exception as e:
            logger.error(f" Erreur LLM : {str(e)}")
            raise LLMServiceError(
                message="Le service LLM est temporairement indisponible.",
                detail={"error": str(e)[:100]}
            )
        
        logger.success(" Conseils générés avec succès")
        
        # Construction de la réponse
        execution_time = time.time() - start_time
        
        response = AdviceResponse(
            job_id=job_id,
            job_title=offer.title,
            company=offer.company,
            advice=advice_text,
            cv_length=len(cv_text),
            execution_time=round(execution_time, 3),
            llm_model=advisor.model_id
        )
        
        logger.info(f" Conseils retournés en {execution_time:.3f}s")
        
        return response
        
    finally:
        # Nettoyage du fichier temporaire
        import os
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
