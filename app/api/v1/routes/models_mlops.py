from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from src.mlops.registry import ModelRegistry
from src.mlops.promotion import promote_candidate_model
from src.mlops.rollback import rollback_production_model

router = APIRouter(prefix="/models", tags=["Model Lifecycle & Registry"])


class PromoteRequest(BaseModel):
    version: str
    actor: Optional[str] = "admin"
    force: Optional[bool] = False


class RollbackRequest(BaseModel):
    version: str
    actor: Optional[str] = "operator"


@router.get("", summary="List registered model versions and statuses")
def list_registered_models(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns list of registered model versions, statuses, and validation metrics."""
    registry = ModelRegistry(db)
    models = registry.list_models()
    return {
        "total": len(models),
        "items": [m.to_dict() for m in models],
    }


@router.post("/promote", summary="Promote candidate model to active production")
def promote_model_endpoint(
    body: PromoteRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Evaluates candidate model against production validation gates and promotes if criteria are satisfied."""
    success, message, details = promote_candidate_model(db, body.version, actor=body.actor or "admin", force=body.force or False)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "SUCCESS", "message": message, "details": details}


@router.post("/rollback", summary="Rollback production model to previous version")
def rollback_model_endpoint(
    body: RollbackRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Rolls back production active model reference to specified version."""
    success, message, details = rollback_production_model(db, body.version, actor=body.actor or "operator")
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "SUCCESS", "message": message, "details": details}
