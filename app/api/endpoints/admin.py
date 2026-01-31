"""
Endpoints admin protégés par API key.
Collecte de données et maintenance.
"""

from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.schemas.common import MessageResponse
from app.api.deps import get_db
from app.core.security import verify_api_key
from app.core.exceptions import DatabaseError
from app.utils import run_in_thread

# Import des services
from src.services.collector import run_collector
from src.services.processor import process_embeddings
from src.services.scrappe_hw import run_hw_scraper
from src.services.scrappe_wttj import run_wttj_scraper
from src.database.models import JobOffer

router = APIRouter()


@router.post(
    "/admin/collect",
    response_model=MessageResponse,
    tags=["Admin"],
    summary="Lancer la collecte d'offres",
    description="Collecte de nouvelles offres via API France Travail et scraping. **Requiert une API key.**",
    status_code=202
)
async def collect_jobs(
    keywords: List[str],
    max_offers: int = 10,
    enable_scraping: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Lance la collecte de nouvelles offres d'emploi.
    
    **Sources** :
    - API France Travail (toujours actif)
    - HelloWork (si enable_scraping=true)
    - Welcome to the Jungle (si enable_scraping=true)
    
    **Processus** :
    1. Collecte des offres depuis les sources
    2. Vérification des doublons (par ID)
    3. Insertion en base de données
    4. Génération des embeddings (automatique après collecte)
    
    **Authentification** :
    Endpoint protégé par API key. Fournir la clé dans le header `X-API-Key`.
    
    **Exemple** :
    ```bash
    curl -X POST "http://localhost:8000/api/admin/collect" \\
      -H "X-API-Key: votre-cle-admin" \\
      -H "Content-Type: application/json" \\
      -d '{"keywords": ["Data Scientist", "ML Engineer"], "max_offers": 20}'
    ```
    
    Args:
        keywords: Liste de mots-clés pour la recherche
        max_offers: Nombre max d'offres par mot-clé (défaut: 10)
        enable_scraping: Activer le scraping web (défaut: true)
        background_tasks: Tâches en arrière-plan (injecté)
        db: Session DB (injecté)
        api_key: API key validée (injecté)
    
    Returns:
        MessageResponse: Confirmation de lancement
    """
    
    if not keywords:
        return MessageResponse(
            message="Liste de mots-clés vide, aucune collecte lancée.",
            success=False
        )
    
    # Fonction de collecte complète (exécutée en arrière-plan)
    async def run_collection():
        try:
            # API France Travail
            logger.info("Collecte API France Travail...")
            await run_in_thread(run_collector, keywords, max_offers)
            
            # Scraping HelloWork : optionnel
            if enable_scraping:
                logger.info(f"Démarrage scraping HelloWork ({max_offers} offres/mot-clé)...")
                await run_in_thread(
                    run_hw_scraper,
                    keywords_to_fetch=keywords,
                    max_offres_per_kw=max_offers,
                    save_to_db=True,
                    headless=True
                )
                logger.success(" Scraping HelloWork terminé")
            
            # Scraping Welcome to the Jungle : optionnel
            if enable_scraping:
                logger.info(f" Démarrage scraping Welcome to the Jungle ({max_offers} offres/mot-clé)...")
                await run_in_thread(
                    run_wttj_scraper,
                    keywords_to_fetch=keywords,
                    max_offres_per_kw=max_offers,
                    save_to_db=True,
                    headless=True
                )
                logger.success(" Scraping Welcome to the Jungle terminé")
            
            # Génération des embeddings pour les nouvelles offres
            logger.info(" Génération des embeddings...")
            await run_in_thread(process_embeddings)
            
            logger.success(" Collecte complète terminée avec succès!")
            
        except Exception as e:
            logger.error(f" Erreur lors de la collecte : {e}")
    
    # Lancement en arrière-plan
    if background_tasks:
        background_tasks.add_task(run_collection)
    else:
        # Fallback si BackgroundTasks n'est pas disponible
        await run_collection()
    
    return MessageResponse(
        message=f"Collecte lancée pour {len(keywords)} mot(s)-clé(s).",
        success=True,
        data={
            "keywords": keywords,
            "max_offers_per_keyword": max_offers,
            "scraping_enabled": enable_scraping
}
    )


@router.post(
    "/admin/reindex",
    response_model=MessageResponse,
    tags=["Admin"],
    summary="Régénérer tous les embeddings",
    description="Régénère les embeddings pour toutes les offres. **Requiert une API key.**",
    status_code=202
)
async def reindex_embeddings(
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Régénère les embeddings pour toutes les offres.
    
    **Cas d'usage** :
    - Changement de modèle d'embedding
    - Correction de bugs dans la vectorisation
    - Réindexation complète de la base
    
    **Attention** : Opération longue si beaucoup d'offres.
    
    **Exemple** :
    ```bash
    curl -X POST "http://localhost:8000/api/admin/reindex" \\
      -H "X-API-Key: votre-cle-admin"
    ```
    
    Args:
        background_tasks: Tâches en arrière-plan (injecté)
        db: Session DB (injecté)
        api_key: API key validée (injecté)
    
    Returns:
        MessageResponse: Confirmation de lancement
    """

    # Fonction de réindexation
    async def run_reindex():
        try:
            await run_in_thread(process_embeddings)
            logger.success("Réindexation terminée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la réindexation : {e}")
    
    # Lancement en arrière-plan
    if background_tasks:
        background_tasks.add_task(run_reindex)
    else:
        await run_reindex()
    
    return MessageResponse(
        message="Réindexation des embeddings lancée en arrière-plan.",
        success=True
    )


@router.get(
    "/admin/stats",
    response_model=dict,
    tags=["Admin"],
    summary="Statistiques de la base",
    description="Statistiques sur les offres en base. **Requiert une API key.**",
    status_code=200
)
async def get_stats(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Statistiques sur la base de données.
    
    **Informations retournées** :
    - Nombre total d'offres
    - Nombre d'offres par source
    - Nombre d'offres avec/sans embeddings
    - Offre la plus récente
    
    Args:
        db: Session DB (injecté)
        api_key: API key validée (injecté)
    
    Returns:
        dict: Statistiques détaillées
    """
    
    try:
        # Nombre total d'offres
        total_jobs = db.query(JobOffer).count()
        
        # Nombre d'offres par source
        by_source = db.query(
            JobOffer.source,
            func.count(JobOffer.id).label('count')
        ).group_by(JobOffer.source).all()
        
        sources_stats = {source: count for source, count in by_source}
        
        # Offres avec/sans embeddings
        with_embeddings = db.query(JobOffer).filter(JobOffer.embedding.isnot(None)).count()
        without_embeddings = total_jobs - with_embeddings
        
        # Offre la plus récente
        latest_job = db.query(JobOffer).order_by(
            JobOffer.actualisation_date.desc()
        ).first()
        
        latest_job_info = None
        if latest_job:
            latest_job_info = {
                "title": latest_job.title,
                "company": latest_job.company,
                "date": latest_job.actualisation_date.isoformat() if latest_job.actualisation_date else None
            }
        
        logger.info(f" Statistiques générées : {total_jobs} offres")
        
        return {
            "total_jobs": total_jobs,
            "by_source": sources_stats,
            "embeddings": {
                "with_embeddings": with_embeddings,
                "without_embeddings": without_embeddings,
                "percentage_indexed": round((with_embeddings / total_jobs * 100), 2) if total_jobs > 0 else 0
            },
            "latest_job": latest_job_info
        }
        
    except Exception as e:
        logger.error(f" Erreur lors de la génération des stats : {e}")
        raise DatabaseError(
            message="Impossible de générer les statistiques",
            detail={"error": str(e)[:100]}
        )
