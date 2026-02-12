"""
Point d'entrée principal de l'API CV-Optimizer.
Configure l'application FastAPI avec tous les middlewares et routers.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.router import api_router
from app.config import get_settings


# Récupération de la configuration
settings = get_settings()

# Variable pour tracker le temps de démarrage
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    - startup: Initialisation des ressources
    - shutdown: Nettoyage des ressources
    """
    # Startup
    logger.info("Démarrage de CV-Optimizer API")
    logger.info(f"Environment: {settings.DEBUG}")
    logger.info(
        f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}"
    )
    logger.info(f"CORS origins: {settings.ALLOWED_ORIGINS}")

    yield

    # Shutdown
    uptime = time.time() - _start_time
    logger.info(f"Arrêt de CV-Optimizer API (uptime: {uptime:.2f}s)")


# Création de l'application FastAPI
app = FastAPI(
    title="CV-Optimizer API",
    description="""
## API de matching et optimisation de CV

Cette API permet de :
- **Matcher** un CV avec des offres d'emploi via recherche vectorielle
- **Obtenir des conseils** personnalisés d'un LLM pour améliorer son CV
- **Rechercher** et filtrer des offres d'emploi
- **Administrer** la collecte et l'indexation des offres

### Technologies
- **Vectorisation** : sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **LLM** : Qwen 2.5 via Hugging Face Inference API
- **Base de données** : PostgreSQL avec extension pgvector
- **Sources** : France Travail API, HelloWork, Welcome to the Jungle

### Authentication
- Endpoints publics : Aucune authentification requise
- Endpoints admin (`/api/admin/*`) : Header `X-API-Key` requis

### Rate Limiting
- Limite globale : 60 requêtes/minute (configurable)
- Limite upload : 5 MB par fichier
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# CORS - Autorisation des requêtes cross-origin (pour un futur front-end)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du router principal
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    logger.info("Démarrage du serveur Uvicorn...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
