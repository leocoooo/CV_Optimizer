"""
Router principal de l'API v1.
Regroupe tous les endpoints dans un router unique.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, match, advice, jobs, admin

# Router principal v1
api_router = APIRouter()

# Inclusion des routers d'endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(match.router, prefix="/api/v1", tags=["Matching"])
api_router.include_router(advice.router, prefix="/api/v1", tags=["LLM"])
api_router.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
api_router.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
