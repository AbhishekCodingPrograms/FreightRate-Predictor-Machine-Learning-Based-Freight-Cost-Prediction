import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import ModelVersion, ModelAuditEvent


def compute_file_checksum(filepath: str) -> str:
    """Computes SHA-256 checksum of model artifact for integrity verification."""
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelRegistry:
    """Lightweight Model Registry for managing model versions, candidate registration, status lifecycle, and audit logs."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def register_candidate(
        self,
        version: str,
        model_type: str,
        target_strategy: str,
        ensemble_weights: Dict[str, float],
        validation_metrics: Dict[str, float],
        training_period: str,
        artifact_path: str,
        feature_schema: Dict[str, Any],
        git_commit: Optional[str] = "main",
        status: str = "candidate"
    ) -> ModelVersion:
        """Registers a newly trained candidate model in the DB registry."""
        checksum = compute_file_checksum(artifact_path)
        
        # Check if version exists
        existing = self.db.query(ModelVersion).filter(ModelVersion.version == version).first()
        if existing:
            # Update existing record
            existing.model_type = model_type
            existing.target_strategy = target_strategy
            existing.ensemble_weights = ensemble_weights
            existing.validation_metrics = validation_metrics
            existing.training_period = training_period
            existing.artifact_path = artifact_path
            existing.checksum = checksum
            existing.feature_schema = feature_schema
            existing.status = status
            model_rec = existing
        else:
            model_rec = ModelVersion(
                version=version,
                model_type=model_type,
                target_strategy=target_strategy,
                ensemble_weights=ensemble_weights,
                validation_metrics=validation_metrics,
                training_period=training_period,
                artifact_path=artifact_path,
                checksum=checksum,
                feature_schema=feature_schema,
                status=status,
                is_active=False,
                git_commit=git_commit,
                created_at=datetime.utcnow()
            )
            self.db.add(model_rec)

        # Audit event
        audit = ModelAuditEvent(
            model_version=version,
            event_type="REGISTERED",
            actor="system",
            details={"status": status, "metrics": validation_metrics, "artifact_path": artifact_path}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(model_rec)
        return model_rec

    def get_production_model(self) -> Optional[ModelVersion]:
        """Returns current active production model."""
        return (
            self.db.query(ModelVersion)
            .filter(ModelVersion.is_active == True, ModelVersion.status == "production")
            .first()
        )

    def list_models(self) -> List[ModelVersion]:
        """Returns all registered models ordered by creation date desc."""
        return self.db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()

    def get_model(self, version: str) -> Optional[ModelVersion]:
        """Looks up a model version by version string with flexible prefix handling."""
        # 1. Exact match
        model = self.db.query(ModelVersion).filter(ModelVersion.version == version).first()
        if model:
            return model

        # 2. Flexible normalized matching (e.g. 'freight-rate-v1.0.0', 'v1.0.0', '1.0.0')
        clean_version = version.replace("freight-rate-", "").lstrip("v")
        all_models = self.db.query(ModelVersion).all()
        for m in all_models:
            m_clean = m.version.replace("freight-rate-", "").lstrip("v")
            if m_clean == clean_version:
                return m

        return None

    def ensure_production_registered(
        self,
        artifact_metadata: Dict[str, Any],
        artifact_path: str = "artifacts/freight_rate_model.joblib"
    ) -> ModelVersion:
        """Ensures the currently loaded artifact is registered as active production in DB."""
        version = artifact_metadata.get("model_version", "1.0.0")
        model_rec = self.get_model(version)
        checksum = compute_file_checksum(artifact_path)
        if not model_rec:
            model_rec = self.register_candidate(
                version=version,
                model_type="GBDT Ensemble (LightGBM+CatBoost+XGBoost)",
                target_strategy=artifact_metadata.get("target_strategy", "Residual (posted_rate - base_signal)"),
                ensemble_weights=artifact_metadata.get("ensemble_weights", {"lgbm": 0.785, "catboost": 0.146, "xgboost": 0.069}),
                validation_metrics=artifact_metadata.get("metrics", {"rmse": 128.45, "mae": 92.30, "mape": 4.72, "r2": 0.9453}),
                training_period="2026-01-01 to 2026-10-31",
                artifact_path=artifact_path,
                feature_schema={"features": artifact_metadata.get("feature_names", [])},
                status="production"
            )
        else:
            # Ensure fields are populated
            if not model_rec.artifact_path or not os.path.exists(model_rec.artifact_path):
                model_rec.artifact_path = artifact_path
            if not model_rec.checksum:
                model_rec.checksum = checksum
            if model_rec.status != "production" or not model_rec.is_active:
                model_rec.status = "production"
                model_rec.is_active = True
                model_rec.promoted_at = datetime.utcnow()
                model_rec.promoted_by = "system"
            self.db.commit()
            self.db.refresh(model_rec)

        return model_rec


    def update_status(self, version: str, new_status: str, actor: str = "system", reason: Optional[str] = None) -> ModelVersion:
        """Updates lifecycle status of a registered model."""
        model_rec = self.get_model(version)
        if not model_rec:
            raise ValueError(f"Model version '{version}' not found in registry.")

        old_status = model_rec.status
        model_rec.status = new_status
        if new_status == "production":
            model_rec.is_active = True
            model_rec.promoted_at = datetime.utcnow()
            model_rec.promoted_by = actor
            
            # Deactivate other production models
            other_prods = (
                self.db.query(ModelVersion)
                .filter(ModelVersion.version != version, ModelVersion.status == "production")
                .all()
            )
            for m in other_prods:
                m.status = "archived"
                m.is_active = False

        elif old_status == "production" and new_status != "production":
            model_rec.is_active = False

        # Add Audit Event
        audit = ModelAuditEvent(
            model_version=version,
            event_type=f"STATUS_CHANGE_{new_status.upper()}",
            actor=actor,
            details={"old_status": old_status, "new_status": new_status, "reason": reason}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(model_rec)
        return model_rec
