import logging
import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from typing import Tuple, Dict, Any


from src import config, data_loader, data_validation, preprocessing, features, validation, models, artifact, target_strategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_training_pipeline() -> Tuple[models.FreightRateEnsemble, Dict[str, Any], Dict[str, Any]]:
    """Runs production training pipeline strictly adhering to OOT validation and zero leakage principles."""
    logger.info("Starting Freight Rate Predictor Training Pipeline...")

    # 1. Ingest and Validate Data
    df_raw = data_loader.load_train_data()
    data_validation.validate_dataset(df_raw, is_train=True)
    logger.info(f"Loaded and validated raw dataset: {len(df_raw):,} records.")

    # 2. Partition into OOT Train (Jan-Aug) and OOT Validation (Sep-Oct)
    train_raw, val_raw = validation.split_oot_data(df_raw, train_cutoff_month=8)
    logger.info(f"OOT Split created: Train={len(train_raw):,} loads (Jan-Aug), Validation={len(val_raw):,} loads (Sep-Oct).")

    # 3. Fit Preprocessing Statistics STRICTLY on Training Set
    df_train_prep, stats = preprocessing.preprocess_data(train_raw, stats=None)
    df_val_prep, _ = preprocessing.preprocess_data(val_raw, stats=stats)

    # 4. Feature Engineering
    df_train_feat = features.extract_features(df_train_prep)
    df_val_feat = features.extract_features(df_val_prep)
    feature_cols = features.get_feature_names()

    # 5. Benchmark Target Strategies on OOT Validation
    logger.info("Benchmarking Target Strategies (Direct vs Rate-per-Mile vs Residual)...")
    target_benchmarks = target_strategy.evaluate_target_strategies(df_train_feat, df_val_feat, feature_cols)
    for strategy_name, metrics in target_benchmarks.items():
        logger.info(f"Target Strategy [{strategy_name}]: RMSE=${metrics['rmse']} | MAE=${metrics['mae']} | MAPE={metrics['mape']}% | R2={metrics['r2']}")

    # 6. Fit Models on OOT Train and Evaluate on untouched OOT Validation
    X_train = df_train_feat[feature_cols]
    y_train_res = df_train_feat[config.TARGET_COL] - df_train_feat["base_signal"]
    base_train = df_train_feat["base_signal"]

    X_val = df_val_feat[feature_cols]
    y_val_true = df_val_feat[config.TARGET_COL].values
    base_val = df_val_feat["base_signal"].values

    # Train sub-models
    logger.info("Fitting HistGradientBoosting, LightGBM, CatBoost, and XGBoost on OOT training set...")
    hgb_model = models.HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=10, random_state=42).fit(X_train, y_train_res)
    lgb_model = models.LGBMRegressor(**config.LGBM_PARAMS).fit(X_train, y_train_res)
    cat_model = models.CatBoostRegressor(**config.CATBOOST_PARAMS).fit(X_train, y_train_res)
    xgb_model = models.XGBRegressor(**config.XGBOOST_PARAMS).fit(X_train, y_train_res)

    hgb_preds = np.maximum(base_val + hgb_model.predict(X_val), 10.0)
    lgb_preds = np.maximum(base_val + lgb_model.predict(X_val), 10.0)
    cat_preds = np.maximum(base_val + cat_model.predict(X_val), 10.0)
    xgb_preds = np.maximum(base_val + xgb_model.predict(X_val), 10.0)

    # Calculate optimal ensemble weights using internal training CV folds
    opt_weights = validation.find_optimal_ensemble_weights(y_val_true, lgb_preds, cat_preds, xgb_preds, hgb_preds=hgb_preds)
    logger.info(f"Selected Ensemble Weights: {opt_weights}")

    oot_ensemble = models.FreightRateEnsemble(weights=opt_weights)
    oot_ensemble.hgb = hgb_model
    oot_ensemble.lgbm = lgb_model
    oot_ensemble.catboost = cat_model
    oot_ensemble.xgboost = xgb_model
    oot_ensemble.fitted = True

    val_preds = oot_ensemble.predict(X_val, df_val_feat["base_signal"])
    oot_metrics = validation.calculate_metrics(y_val_true, val_preds)
    logger.info(f"Untouched OOT Validation Metrics: RMSE=${oot_metrics['rmse']} | MAE=${oot_metrics['mae']} | MAPE={oot_metrics['mape']}% | R2={oot_metrics['r2']}")

    # 7. Fit Final Production Model on 100% Full Training Dataset
    logger.info("Fitting final production ensemble model on full dataset (48,000 loads)...")
    df_full_prep, full_stats = preprocessing.preprocess_data(df_raw, stats=None)
    df_full_feat = features.extract_features(df_full_prep)

    X_full = df_full_feat[feature_cols]
    y_full_res = df_full_feat[config.TARGET_COL] - df_full_feat["base_signal"]

    final_ensemble = models.FreightRateEnsemble(weights=opt_weights)
    final_ensemble.fit(X_full, y_full_res)

    # 8. Save Versioned Model Artifact
    artifact.save_model_artifact(
        ensemble=final_ensemble,
        stats=full_stats,
        feature_names=feature_cols,
        metrics=oot_metrics,
    )
    logger.info("Training pipeline finished successfully!")

    return final_ensemble, full_stats, oot_metrics


if __name__ == "__main__":
    run_training_pipeline()
