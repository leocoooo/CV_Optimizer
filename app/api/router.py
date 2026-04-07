"""
Router principal de l'API.
Regroupe tous les endpoints dans un router unique.
"""

from fastapi import APIRouter

from app.api.endpoints import (
    admin,
    advice,
    chat,
    cover_letter,
    dashboard,
    health,
    jobs,
    match,
    skills,
)

# Router principal
api_router = APIRouter()

# Inclusion des routers d'endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
api_router.include_router(match.router, prefix="/api", tags=["Matching"])
api_router.include_router(advice.router, prefix="/api", tags=["LLM"])
api_router.include_router(chat.router, prefix="/api", tags=["LLM"])
api_router.include_router(cover_letter.router, prefix="/api", tags=["LLM"])
api_router.include_router(skills.router, prefix="/api", tags=["Skills"])
api_router.include_router(jobs.router, prefix="/api", tags=["Jobs"])
api_router.include_router(admin.router, prefix="/api", tags=["Admin"])
