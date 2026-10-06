from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from app.db.database import Base


class ModelVersion(Base):
    """Stores model metadata, target formulation, validation metrics, lifecycle status, and active flag."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(64), unique=True, index=True, nullable=False)
    model_type = Column(String(64), nullable=False)
    target_strategy = Column(String(64), nullable=False)
    ensemble_weights = Column(JSON, nullable=True)
    validation_metrics = Column(JSON, nullable=True)
    training_period = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Extended MLOps Registry fields
    status = Column(String(32), default="candidate", index=True, nullable=False)  # candidate, approved, production, archived, rejected
    git_commit = Column(String(64), nullable=True)
    artifact_path = Column(String(256), nullable=True)
    checksum = Column(String(64), nullable=True)
    feature_schema = Column(JSON, nullable=True)
    promoted_at = Column(DateTime, nullable=True)
    promoted_by = Column(String(64), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "version": self.version,
            "model_type": self.model_type,
            "target_strategy": self.target_strategy,
            "ensemble_weights": self.ensemble_weights,
            "validation_metrics": self.validation_metrics,
            "training_period": self.training_period,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "status": self.status,
            "git_commit": self.git_commit,
            "artifact_path": self.artifact_path,
            "checksum": self.checksum,
            "feature_schema": self.feature_schema,
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "promoted_by": self.promoted_by,
        }


class PredictionRequest(Base):
    """Tracks operational inference request metadata (single/batch execution, status, timestamp)."""
    __tablename__ = "prediction_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    request_type = Column(String(32), nullable=False)  # "single" or "batch"
    batch_size = Column(Integer, default=1, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "request_type": self.request_type,
            "batch_size": self.batch_size,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Prediction(Base):
    """Persists detailed spot rate predictions, confidence intervals, inputs, and model version trace."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), index=True, nullable=False)
    load_id = Column(String(128), index=True, nullable=True)
    predicted_rate = Column(Float, nullable=False)
    rate_per_mile = Column(Float, nullable=False)
    confidence_interval_lower = Column(Float, nullable=False)
    confidence_interval_upper = Column(Float, nullable=False)
    base_signal = Column(Float, nullable=True)
    residual = Column(Float, nullable=True)
    model_version = Column(String(64), index=True, nullable=False)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    input_data = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "load_id": self.load_id,
            "predicted_rate": self.predicted_rate,
            "rate_per_mile": self.rate_per_mile,
            "confidence_interval": {
                "lower": self.confidence_interval_lower,
                "upper": self.confidence_interval_upper,
            },
            "base_signal": self.base_signal,
            "residual": self.residual,
            "model_version": self.model_version,
            "prediction_timestamp": self.prediction_timestamp.isoformat() if self.prediction_timestamp else None,
            "input_data": self.input_data,
        }


class PredictionOutcome(Base):
    """Stores delayed actual posted rates matched by load_id for true performance monitoring."""
    __tablename__ = "prediction_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_id = Column(String(128), unique=True, index=True, nullable=False)
    actual_posted_rate = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "load_id": self.load_id,
            "actual_posted_rate": self.actual_posted_rate,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class DataQualityMetric(Base):
    """Stores feature-level data quality monitoring audit logs."""
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    feature_name = Column(String(64), nullable=False)
    total_records = Column(Integer, nullable=False)
    missing_count = Column(Integer, default=0, nullable=False)
    missing_pct = Column(Float, default=0.0, nullable=False)
    invalid_count = Column(Integer, default=0, nullable=False)
    invalid_pct = Column(Float, default=0.0, nullable=False)
    status = Column(String(32), default="NORMAL", nullable=False)  # NORMAL, WARNING, CRITICAL

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "feature_name": self.feature_name,
            "total_records": self.total_records,
            "missing_count": self.missing_count,
            "missing_pct": self.missing_pct,
            "invalid_count": self.invalid_count,
            "invalid_pct": self.invalid_pct,
            "status": self.status,
        }


class DriftMetric(Base):
    """Stores feature drift metrics (PSI, KS test) calculated against training baseline."""
    __tablename__ = "drift_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    feature_name = Column(String(64), nullable=False)
    metric_type = Column(String(32), nullable=False)  # PSI, KS, JS
    metric_value = Column(Float, nullable=False)
    threshold_warning = Column(Float, default=0.1, nullable=False)
    threshold_critical = Column(Float, default=0.25, nullable=False)
    status = Column(String(32), default="NORMAL", nullable=False)  # NORMAL, WARNING, CRITICAL

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "feature_name": self.feature_name,
            "metric_type": self.metric_type,
            "metric_value": self.metric_value,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "status": self.status,
        }


class ModelPerformanceMetric(Base):
    """Stores delayed actual model evaluation metrics globally and by segment."""
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    model_version = Column(String(64), index=True, nullable=False)
    sample_size = Column(Integer, nullable=False)
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)
    residual_mean = Column(Float, nullable=True)
    residual_std = Column(Float, nullable=True)
    segment_name = Column(String(64), default="all", nullable=False)  # e.g. "all", "equipment", "distance_bucket"
    segment_value = Column(String(64), default="all", nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model_version": self.model_version,
            "sample_size": self.sample_size,
            "rmse": self.rmse,
            "mae": self.mae,
            "mape": self.mape,
            "r2": self.r2,
            "residual_mean": self.residual_mean,
            "residual_std": self.residual_std,
            "segment_name": self.segment_name,
            "segment_value": self.segment_value,
        }


class MonitoringRun(Base):
    """Audit log of executed offline monitoring jobs."""
    __tablename__ = "monitoring_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    prediction_count = Column(Integer, default=0, nullable=False)
    data_quality_status = Column(String(32), default="NORMAL", nullable=False)
    drift_status = Column(String(32), default="NORMAL", nullable=False)
    performance_status = Column(String(32), default="NORMAL", nullable=False)
    alert_count = Column(Integer, default=0, nullable=False)
    details = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "prediction_count": self.prediction_count,
            "data_quality_status": self.data_quality_status,
            "drift_status": self.drift_status,
            "performance_status": self.performance_status,
            "alert_count": self.alert_count,
            "details": self.details,
        }


class ModelAuditEvent(Base):
    """Audit trail for model lifecycle state changes (promotion, rollback, retraining)."""
    __tablename__ = "model_audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    model_version = Column(String(64), index=True, nullable=False)
    event_type = Column(String(32), nullable=False)  # REGISTERED, EVALUATED, PROMOTED, DEMOTED, ROLLBACK
    actor = Column(String(64), default="system", nullable=False)
    details = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model_version": self.model_version,
            "event_type": self.event_type,
            "actor": self.actor,
            "details": self.details,
        }
