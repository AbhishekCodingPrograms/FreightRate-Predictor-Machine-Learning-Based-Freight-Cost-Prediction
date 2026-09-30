import pandas as pd
from typing import Tuple, Dict, Any

from src import config, data_loader, preprocessing, features, validation, models


def run_training_pipeline() -> Tuple[models.FreightRateEnsemble, Dict[str, Any], Dict[str, Any]]:
    print("Loading training data...")
    df_raw = data_loader.load_train_data()
    data_loader.verify_data_integrity(df_raw, is_train=True)
    print(f"Dataset loaded: {len(df_raw):,} records.")

    print("Preprocessing and engineering features...")
    df_prep, stats = preprocessing.preprocess_data(df_raw)
    df_feat = features.extract_features(df_prep)
    feature_cols = features.get_feature_names()

    print("Evaluating Out-Of-Time validation (Jan-Aug train / Sep-Oct val)...")
    train_oot, val_oot = validation.split_oot_data(df_feat, train_cutoff_month=8)

    X_train_oot = train_oot[feature_cols]
    y_train_oot = train_oot[config.TARGET_COL]
    base_train_oot = train_oot["base_signal"]

    X_val_oot = val_oot[feature_cols]
    y_val_oot = val_oot[config.TARGET_COL]
    base_val_oot = val_oot["base_signal"]

    oot_ensemble = models.FreightRateEnsemble()
    oot_ensemble.fit(X_train_oot, y_train_oot - base_train_oot)
    val_preds = oot_ensemble.predict(X_val_oot, base_val_oot)

    oot_metrics = validation.calculate_metrics(y_val_oot, val_preds)
    print(f"OOT Metrics: RMSE=${oot_metrics['rmse']} | MAE=${oot_metrics['mae']} | MAPE={oot_metrics['mape']}% | R2={oot_metrics['r2']}")

    print("Fitting production ensemble model on full dataset...")
    X_full = df_feat[feature_cols]
    y_full = df_feat[config.TARGET_COL]
    base_full = df_feat["base_signal"]

    final_ensemble = models.FreightRateEnsemble()
    final_ensemble.fit(X_full, y_full - base_full)

    return final_ensemble, stats, oot_metrics


if __name__ == "__main__":
    run_training_pipeline()
