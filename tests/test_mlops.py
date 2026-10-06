import os
import pytest
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import ModelVersion, Prediction, PredictionOutcome
from src.mlops.data_quality import audit_prediction_data_quality
from src.mlops.drift import calculate_psi, detect_feature_drift
from src.mlops.performance import evaluate_delayed_performance
from src.mlops.registry import ModelRegistry
from src.mlops.promotion import promote_candidate_model
from src.mlops.rollback import rollback_production_model


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_data_quality_auditing():
    payloads = [
        {"pickup": "Lexington", "delivery": "Fort Wayne", "pickup_lat": 38.0464, "pickup_lon": -84.497, "delivery_lat": 41.0793, "delivery_lon": -85.1394, "distance": 360, "equipment": "Dry Van", "weight": 32000},
        {"pickup": "Chicago", "delivery": "Detroit", "pickup_lat": 150.0, "pickup_lon": -87.6298, "delivery_lat": 41.0793, "delivery_lon": -85.1394, "distance": -10, "equipment": "UnknownType", "weight": 0},
    ]

    metrics, status = audit_prediction_data_quality(payloads)
    assert len(metrics) > 0
    assert status in ["WARNING", "CRITICAL"]

    distance_metric = next(m for m in metrics if m["feature_name"] == "distance")
    assert distance_metric["invalid_count"] == 1


def test_psi_calculation():
    np.random.seed(42)
    expected = np.random.normal(100, 10, 1000)
    actual_same = np.random.normal(100, 10, 1000)
    actual_shifted = np.random.normal(150, 20, 1000)

    psi_same = calculate_psi(expected, actual_same)
    psi_shifted = calculate_psi(expected, actual_shifted)

    assert psi_same < 0.1
    assert psi_shifted > 0.25


def test_feature_drift_detection():
    baseline_df = pd.DataFrame({
        "distance": np.random.normal(300, 50, 100),
        "weight": np.random.normal(30000, 5000, 100),
    })

    payloads = [
        {"distance": 300 + i, "weight": 30000 + i * 10} for i in range(50)
    ]

    metrics, status = detect_feature_drift(baseline_df, payloads, numeric_features=["distance", "weight"])
    assert len(metrics) == 2
    assert status in ["NORMAL", "WARNING", "CRITICAL"]


def test_delayed_performance_evaluation():
    preds = [
        {"load_id": f"LOAD-{i}", "predicted_rate": 1000.0 + i * 10, "model_version": "v1.0.0", "input_data": {"equipment": "Dry Van"}}
        for i in range(10)
    ]
    outcomes = [
        {"load_id": f"LOAD-{i}", "actual_posted_rate": 1020.0 + i * 10}
        for i in range(10)
    ]

    metrics_list, global_metric = evaluate_delayed_performance(preds, outcomes, min_sample_size=5)
    assert global_metric is not None
    assert global_metric["sample_size"] == 10
    assert global_metric["rmse"] > 0
    assert global_metric["mae"] == 20.0


def test_model_registry_lifecycle(db_session, tmp_path):
    registry = ModelRegistry(db_session)
    artifact_file = tmp_path / "model.joblib"
    artifact_file.write_text("dummy artifact content")

    candidate = registry.register_candidate(
        version="freight-rate-v9.9.9",
        model_type="Ensemble",
        target_strategy="residual",
        ensemble_weights={"lgbm": 0.5, "catboost": 0.5},
        validation_metrics={"rmse": 100.0, "mape": 5.0},
        training_period="2025-01 to 2025-08",
        artifact_path=str(artifact_file),
        feature_schema={"features": ["distance", "weight"]},
        status="candidate"
    )

    assert candidate.version == "freight-rate-v9.9.9"
    assert candidate.status == "candidate"
    assert candidate.is_active is False

    updated = registry.update_status("freight-rate-v9.9.9", "approved")
    assert updated.status == "approved"


def test_promotion_gate_rejection(db_session, tmp_path):
    registry = ModelRegistry(db_session)

    # 1. Register active production model with MAPE 5.0%
    prod_artifact = tmp_path / "prod.joblib"
    import joblib
    joblib.dump({"models": {}, "preprocessing": {}}, prod_artifact)

    registry.register_candidate(
        version="prod-v1.0.0",
        model_type="Ensemble",
        target_strategy="residual",
        ensemble_weights={"lgbm": 1.0},
        validation_metrics={"rmse": 120.0, "mape": 5.0},
        training_period="2025-01 to 2025-08",
        artifact_path=str(prod_artifact),
        feature_schema={"features": ["distance"]},
        status="production"
    )
    registry.update_status("prod-v1.0.0", "production")

    # 2. Register candidate model with WORSE MAPE 15.0%
    cand_artifact = tmp_path / "cand.joblib"
    joblib.dump({"models": {}, "preprocessing": {}}, cand_artifact)

    registry.register_candidate(
        version="cand-v2.0.0",
        model_type="Ensemble",
        target_strategy="residual",
        ensemble_weights={"lgbm": 1.0},
        validation_metrics={"rmse": 250.0, "mape": 15.0},
        training_period="2025-01 to 2025-08",
        artifact_path=str(cand_artifact),
        feature_schema={"features": ["distance"]},
        status="candidate"
    )

    # Attempt promotion without force
    success, message, _ = promote_candidate_model(db_session, "cand-v2.0.0", force=False)
    assert success is False
    assert "exceeds active production" in message
