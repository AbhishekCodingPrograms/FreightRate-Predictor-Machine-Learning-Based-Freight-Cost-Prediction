from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.db.models import (
    DataQualityMetric, DriftMetric, ModelPerformanceMetric,
    MonitoringRun, PredictionOutcome, Prediction
)
from src.mlops.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["MLOps Monitoring"])


@router.get("/summary", summary="Get overall system monitoring summary")
def get_monitoring_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns high-level MLOps monitoring status, alert counts, and recent execution run."""
    last_run = db.query(MonitoringRun).order_by(MonitoringRun.timestamp.desc()).first()
    total_preds = db.query(Prediction).count()
    total_outcomes = db.query(PredictionOutcome).count()

    if not last_run:
        return {
            "status": "NO_MONITORING_DATA",
            "message": "No monitoring runs have been executed yet.",
            "total_predictions": total_preds,
            "total_actual_outcomes": total_outcomes,
            "last_run": None,
        }

    return {
        "status": "ACTIVE",
        "total_predictions": total_preds,
        "total_actual_outcomes": total_outcomes,
        "last_run": last_run.to_dict(),
    }


@router.get("/drift", summary="Get feature drift metrics")
def get_drift_metrics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Returns Population Stability Index (PSI) and KS test feature drift metrics."""
    metrics = db.query(DriftMetric).order_by(DriftMetric.timestamp.desc()).limit(limit).all()
    if not metrics:
        return {"total": 0, "items": [], "status": "No feature drift data available."}

    return {
        "total": len(metrics),
        "items": [m.to_dict() for m in metrics],
    }


@router.get("/data-quality", summary="Get data quality audit metrics")
def get_data_quality_metrics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Returns input feature missingness and invalidity metrics."""
    metrics = db.query(DataQualityMetric).order_by(DataQualityMetric.timestamp.desc()).limit(limit).all()
    if not metrics:
        return {"total": 0, "items": [], "status": "No data quality data available."}

    return {
        "total": len(metrics),
        "items": [m.to_dict() for m in metrics],
    }


@router.get("/performance", summary="Get delayed outcome model performance metrics")
def get_performance_metrics(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Returns actual vs predicted evaluation metrics (RMSE, MAE, MAPE, R2) grouped globally and by segment."""
    metrics = db.query(ModelPerformanceMetric).order_by(ModelPerformanceMetric.timestamp.desc()).limit(limit).all()
    if not metrics:
        return {"total": 0, "items": [], "status": "No delayed performance evaluation data available."}

    return {
        "total": len(metrics),
        "items": [m.to_dict() for m in metrics],
    }


@router.post("/outcomes", summary="Ingest actual posted rate for a load")
def ingest_outcome(
    load_id: str,
    actual_posted_rate: float,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ingests delayed actual posted rate for performance evaluation matching."""
    if actual_posted_rate <= 0:
        raise HTTPException(status_code=400, detail="Actual posted rate must be positive.")

    existing = db.query(PredictionOutcome).filter(PredictionOutcome.load_id == load_id).first()
    if existing:
        existing.actual_posted_rate = actual_posted_rate
    else:
        rec = PredictionOutcome(load_id=load_id, actual_posted_rate=actual_posted_rate)
        db.add(rec)
    db.commit()

    return {"status": "SUCCESS", "load_id": load_id, "actual_posted_rate": actual_posted_rate}


@router.post("/run", summary="Trigger offline monitoring run on demand")
def trigger_monitoring_run(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Triggers an offline monitoring execution cycle."""
    service = MonitoringService(db)
    res = service.run_monitoring_cycle()
    return res
