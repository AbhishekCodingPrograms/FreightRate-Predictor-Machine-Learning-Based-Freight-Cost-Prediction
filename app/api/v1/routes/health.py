from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.schemas.response import HealthResponse
from app.services.model_service import ModelService
from app.dependencies import get_model_service, get_db_session
from app.core.exceptions import ModelNotLoadedError
from app.db.database import check_db_connected

router = APIRouter(tags=["Health & Readiness"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Lightweight check returning service status, model loaded flag, and database connection status."
)
def get_health(
    model_svc: ModelService = Depends(get_model_service),
    db: Session = Depends(get_db_session)
) -> HealthResponse:
    db_ok = check_db_connected(db)
    return HealthResponse(
        status="healthy" if (model_svc.is_loaded and db_ok) else "degraded",
        service=settings.SERVICE_NAME,
        model_loaded=model_svc.is_loaded,
        database_connected=db_ok,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Readiness probe ensuring trained model artifact and database connection are active."
)
def get_ready(
    model_svc: ModelService = Depends(get_model_service),
    db: Session = Depends(get_db_session)
):
    if not model_svc.is_loaded:
        raise ModelNotLoadedError("Service is not ready: Trained model artifact is not loaded.")
    db_ok = check_db_connected(db)
    return {
        "status": "ready" if db_ok else "not_ready",
        "service": settings.SERVICE_NAME,
        "model_version": model_svc.get_model_version(),
        "database_connected": db_ok,
    }
