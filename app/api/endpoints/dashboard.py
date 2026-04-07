"""
Endpoint public d'agrégation pour le cockpit UI.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, nullslast
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.dashboard import BreakdownItem, DashboardJobPreview, DashboardResponse
from src.database.models import JobOffer

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["Dashboard"],
    summary="Vue agrégée du cockpit",
    description="Expose les métriques publiques nécessaires à l'interface CV-Optimizer.",
    status_code=200,
)
async def get_dashboard(db: Session = Depends(get_db)):
    """Retourne les métriques clés et un aperçu des offres récentes."""

    total_jobs = db.query(func.count(JobOffer.id)).scalar() or 0
    indexed_jobs = (
        db.query(func.count(JobOffer.id))
        .filter(JobOffer.embedding.is_not(None))
        .scalar()
        or 0
    )

    latest_ingestion = db.query(func.max(JobOffer.date_scraping)).scalar()

    source_rows = (
        db.query(JobOffer.source, func.count(JobOffer.id).label("count"))
        .filter(JobOffer.source.is_not(None))
        .group_by(JobOffer.source)
        .order_by(func.count(JobOffer.id).desc(), JobOffer.source.asc())
        .all()
    )
    contract_rows = (
        db.query(JobOffer.contract_type, func.count(JobOffer.id).label("count"))
        .filter(JobOffer.contract_type.is_not(None))
        .group_by(JobOffer.contract_type)
        .order_by(func.count(JobOffer.id).desc(), JobOffer.contract_type.asc())
        .limit(5)
        .all()
    )
    region_rows = (
        db.query(JobOffer.region, func.count(JobOffer.id).label("count"))
        .filter(JobOffer.region.is_not(None))
        .group_by(JobOffer.region)
        .order_by(func.count(JobOffer.id).desc(), JobOffer.region.asc())
        .limit(5)
        .all()
    )

    recent_jobs_rows = (
        db.query(JobOffer)
        .order_by(
            nullslast(JobOffer.date_publication.desc()),
            nullslast(JobOffer.date_scraping.desc()),
        )
        .limit(6)
        .all()
    )

    return DashboardResponse(
        total_jobs=total_jobs,
        indexed_jobs=indexed_jobs,
        indexing_rate=round((indexed_jobs / total_jobs) * 100, 2)
        if total_jobs
        else 0.0,
        active_sources=len(source_rows),
        last_ingested_at=latest_ingestion,
        source_breakdown=[
            BreakdownItem(label=str(label), value=int(value))
            for label, value in source_rows
            if label
        ],
        contract_breakdown=[
            BreakdownItem(label=str(label), value=int(value))
            for label, value in contract_rows
            if label
        ],
        region_breakdown=[
            BreakdownItem(label=str(label), value=int(value))
            for label, value in region_rows
            if label
        ],
        recent_jobs=[
            DashboardJobPreview(
                id=str(job.id),
                title=str(job.title),
                company=str(job.company),
                location=job.location,
                contract_type=str(job.contract_type) if job.contract_type else None,
                remote_mode=str(job.remote_mode) if job.remote_mode else None,
                salary=str(job.salary) if job.salary else None,
                source=str(job.source) if job.source else None,
                url=str(job.url) if job.url else None,
                date_publication=job.date_publication,  # type: ignore[arg-type]
                date_scraping=job.date_scraping,  # type: ignore[arg-type]
            )
            for job in recent_jobs_rows
        ],
    )
