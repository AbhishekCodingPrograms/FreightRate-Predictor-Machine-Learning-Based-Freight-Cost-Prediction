import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import (
    Prediction, PredictionOutcome, DataQualityMetric, DriftMetric,
    ModelPerformanceMetric, MonitoringRun, ModelVersion
)
from src.mlops.data_quality import audit_prediction_data_quality
from src.mlops.drift import detect_feature_drift
from src.mlops.performance import evaluate_delayed_performance


class MonitoringService:
    """Offline monitoring engine for data quality, feature drift, and delayed actual model performance."""

    def __init__(self, db_session: Session, baseline_data_path: str = "data/train-test.csv"):
        self.db = db_session
        self.baseline_data_path = baseline_data_path
        self._baseline_df: Optional[pd.DataFrame] = None

    def _load_baseline_df(self) -> pd.DataFrame:
        if self._baseline_df is None:
            if os.path.exists(self.baseline_data_path):
                self._baseline_df = pd.read_csv(self.baseline_data_path)
            else:
                self._baseline_df = pd.DataFrame()
        return self._baseline_df

    def run_monitoring_cycle(self, limit: int = 1000) -> Dict[str, Any]:
        """Executes a complete monitoring run over recent prediction records."""
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        # 1. Fetch recent predictions from DB
        recent_preds = (
            self.db.query(Prediction)
            .order_by(Prediction.prediction_timestamp.desc())
            .limit(limit)
            .all()
        )

        pred_dicts = [p.to_dict() for p in recent_preds]
        payloads = [p.get("input_data") for p in pred_dicts if p.get("input_data")]

        # 2. Data Quality Audit
        dq_metrics, dq_status = audit_prediction_data_quality(payloads)
        for dq in dq_metrics:
            rec = DataQualityMetric(
                run_id=run_id,
                timestamp=now,
                feature_name=dq["feature_name"],
                total_records=dq["total_records"],
                missing_count=dq["missing_count"],
                missing_pct=dq["missing_pct"],
                invalid_count=dq["invalid_count"],
                invalid_pct=dq["invalid_pct"],
                status=dq["status"],
            )
            self.db.add(rec)

        # 3. Feature Drift Detection
        baseline_df = self._load_baseline_df()
        drift_metrics, drift_status = detect_feature_drift(baseline_df, payloads)
        for dm in drift_metrics:
            rec = DriftMetric(
                run_id=run_id,
                timestamp=now,
                feature_name=dm["feature_name"],
                metric_type=dm["metric_type"],
                metric_value=dm["metric_value"],
                threshold_warning=dm["threshold_warning"],
                threshold_critical=dm["threshold_critical"],
                status=dm["status"],
            )
            self.db.add(rec)

        # 4. Delayed Outcome Performance Evaluation
        outcomes = self.db.query(PredictionOutcome).all()
        outcome_dicts = [o.to_dict() for o in outcomes]

        perf_metrics, global_perf = evaluate_delayed_performance(pred_dicts, outcome_dicts)
        perf_status = "NORMAL"
        for pm in perf_metrics:
            rec = ModelPerformanceMetric(
                run_id=run_id,
                timestamp=now,
                model_version=pm["model_version"],
                sample_size=pm["sample_size"],
                rmse=pm["rmse"],
                mae=pm["mae"],
                mape=pm["mape"],
                r2=pm["r2"],
                residual_mean=pm["residual_mean"],
                residual_std=pm["residual_std"],
                segment_name=pm["segment_name"],
                segment_value=pm["segment_value"],
            )
            self.db.add(rec)
            if pm["mape"] > 15.0 or pm["r2"] < 0.7:
                perf_status = "WARNING"

        # Count alerts
        alert_count = sum(1 for dq in dq_metrics if dq["status"] != "NORMAL") + \
                      sum(1 for dm in drift_metrics if dm["status"] != "NORMAL")

        # Create Monitoring Run Record
        run_record = MonitoringRun(
            run_id=run_id,
            timestamp=now,
            prediction_count=len(recent_preds),
            data_quality_status=dq_status,
            drift_status=drift_status,
            performance_status=perf_status,
            alert_count=alert_count,
            details={
                "data_quality": dq_metrics,
                "drift": drift_metrics,
                "performance": perf_metrics,
            },
        )
        self.db.add(run_record)
        self.db.commit()

        return {
            "run_id": run_id,
            "timestamp": now.isoformat(),
            "prediction_count": len(recent_preds),
            "data_quality_status": dq_status,
            "drift_status": drift_status,
            "performance_status": perf_status,
            "alert_count": alert_count,
            "global_performance": global_perf,
        }
