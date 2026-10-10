from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas.response import ModelInfoResponse
from app.services.model_service import ModelService
from app.dependencies import get_model_service, get_db_session
from app.db.repositories import ModelVersionRepository

router = APIRouter(prefix="/model", tags=["Model Information"])


@router.get(
    "/info",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Model Metadata & Metrics",
    description="Retrieves trained model artifact metadata combined with database model version record."
)
def get_model_info(
    model_svc: ModelService = Depends(get_model_service),
    db: Session = Depends(get_db_session)
) -> ModelInfoResponse:
    info = model_svc.get_model_info()
    version_str = info.get("model_version", "freight-rate-v1.0.0")

    db_mv = ModelVersionRepository.get_by_version(db, version_str)
    if not db_mv:
        # Sync model artifact metadata to DB if not registered yet
        db_mv = ModelVersionRepository.create_or_update_version(db, info)

    info["database_metadata"] = db_mv.to_dict() if db_mv else None
    return ModelInfoResponse(**info)


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get Feature Importances & Model Metrics",
    description="Returns calculated feature importances, ensemble weights, and validation benchmark metrics."
)
def get_model_metrics(
    model_svc: ModelService = Depends(get_model_service),
):
    model_svc._ensure_loaded()
    ensemble = model_svc.get_ensemble()
    feature_names = model_svc.get_feature_names()
    importances = ensemble.get_feature_importances(feature_names).to_dict(orient="records")

    return {
        "metrics": model_svc.artifact.get("metrics", {}) if model_svc.artifact else {},
        "ensemble_weights": ensemble.weights,
        "feature_importances": importances,
    }

