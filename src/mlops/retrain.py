import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from src.data_loader import load_raw_data, split_oot_data
from src.features import create_features
from src.preprocessing import fit_preprocessing, transform_preprocessing
from src.models import train_lightgbm, train_catboost, train_xgboost, optimize_ensemble
from src.evaluate import evaluate_predictions
from src.target_strategy import benchmark_target_strategies
from src.mlops.registry import ModelRegistry


def run_retraining_pipeline(
    db_session: Session,
    new_version_tag: Optional[str] = None,
    data_path: str = "data/train-test.csv"
) -> Dict[str, Any]:
    """Runs time-aware retraining, evaluates candidate models, generates artifact, and registers candidate in DB."""
    registry = ModelRegistry(db_session)

    # 1. Load data
    df = load_raw_data(data_path)
    train_df, val_df = split_oot_data(df)

    # 2. Feature engineering & Preprocessing
    train_df, val_df = create_features(train_df, val_df)
    preproc = fit_preprocessing(train_df)
    X_train, y_train, train_df_clean = transform_preprocessing(train_df, preproc)
    X_val, y_val, val_df_clean = transform_preprocessing(val_df, preproc)

    # 3. Fit models
    lgb_m = train_lightgbm(X_train, y_train)
    cat_m = train_catboost(X_train, y_train)
    xgb_m = train_xgboost(X_train, y_train)

    p_lgb = lgb_m.predict(X_val)
    p_cat = cat_m.predict(X_val)
    p_xgb = xgb_m.predict(X_val)

    # 4. Optimize Ensemble
    weights = optimize_ensemble([p_lgb, p_cat, p_xgb], y_val)
    ensemble_val_preds = weights[0]*p_lgb + weights[1]*p_cat + weights[2]*p_xgb

    metrics = evaluate_predictions(val_df_clean["posted_rate"].values, ensemble_val_preds)

    # Version tag
    if not new_version_tag:
        version_tag = f"freight-rate-v1.{int(datetime.utcnow().timestamp()) % 1000}.0"
    else:
        version_tag = new_version_tag

    artifact_dir = os.path.join("artifacts", "candidates", version_tag)
    os.makedirs(artifact_dir, exist_ok=True)
    artifact_filepath = os.path.join(artifact_dir, "freight_rate_model.joblib")

    candidate_artifact = {
        "model_version": version_tag,
        "created_at": datetime.utcnow().isoformat(),
        "models": {
            "lightgbm": lgb_m,
            "catboost": cat_m,
            "xgboost": xgb_m,
        },
        "ensemble_weights": {
            "lightgbm": weights[0],
            "catboost": weights[1],
            "xgboost": weights[2],
        },
        "preprocessing": preproc,
        "feature_names": list(X_train.columns),
        "target_strategy": "residual",
        "validation_metrics": metrics,
    }

    joblib.dump(candidate_artifact, artifact_filepath)

    # Register in DB Registry as status "candidate" (NOT active production)
    rec = registry.register_candidate(
        version=version_tag,
        model_type="Ensemble (LightGBM+CatBoost+XGBoost)",
        target_strategy="residual",
        ensemble_weights={"lightgbm": weights[0], "catboost": weights[1], "xgboost": weights[2]},
        validation_metrics=metrics,
        training_period="2025-01 to 2025-08 (OOT Train)",
        artifact_path=artifact_filepath,
        feature_schema={"feature_names": list(X_train.columns), "count": len(X_train.columns)},
        status="candidate"
    )

    return {
        "status": "CANDIDATE_REGISTERED",
        "model_version": version_tag,
        "artifact_path": artifact_filepath,
        "validation_metrics": metrics,
        "registered_id": rec.id,
    }
