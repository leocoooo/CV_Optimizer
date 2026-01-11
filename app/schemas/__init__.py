"""Schémas Pydantic pour l'API."""

from app.schemas.common import HealthResponse, ErrorResponse, MessageResponse
from app.schemas.match import MatchResponse, JobMatch
from app.schemas.advice import AdviceRequest, AdviceResponse
from app.schemas.job import JobResponse, JobFilter, JobListResponse

__all__ = [
    "HealthResponse",
    "ErrorResponse",
    "MessageResponse",
    "MatchResponse",
    "JobMatch",
    "AdviceRequest",
    "AdviceResponse",
    "JobResponse",
    "JobFilter",
    "JobListResponse",
]
