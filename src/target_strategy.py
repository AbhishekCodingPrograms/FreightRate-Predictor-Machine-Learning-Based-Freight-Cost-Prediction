import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from typing import Dict, Any, Tuple
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from xgboost import XGBRegressor

from src import config, validation, features


def evaluate_target_strategies(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_cols: list
) -> Dict[str, Dict[str, float]]:
    """Benchmarks Target Strategies (Direct, Rate-per-Mile, and Residual) using OOT validation set.
    
    Returns metrics dict comparing all three formulations.
    """
    X_train = train_df[feature_cols]
    y_train_raw = train_df[config.TARGET_COL].values
    dist_train = np.maximum(train_df["distance"].values, 0.1)
    base_train = train_df["base_signal"].values

    X_val = val_df[feature_cols]
    y_val_raw = val_df[config.TARGET_COL].values
    dist_val = np.maximum(val_df["distance"].values, 0.1)
    base_val = val_df["base_signal"].values

    results = {}

    # Target A: Direct (posted_rate)
    model_a = LGBMRegressor(**config.LGBM_PARAMS)
    model_a.fit(X_train, y_train_raw)
    pred_a = np.maximum(model_a.predict(X_val), 10.0)
    results["Direct (posted_rate)"] = validation.calculate_metrics(y_val_raw, pred_a)

    # Target B: Rate-per-mile (posted_rate / distance)
    y_train_rate = y_train_raw / dist_train
    model_b = LGBMRegressor(**config.LGBM_PARAMS)
    model_b.fit(X_train, y_train_rate)
    pred_b_rpm = model_b.predict(X_val)
    pred_b = np.maximum(pred_b_rpm * dist_val, 10.0)
    results["Rate-per-mile (posted_rate / distance)"] = validation.calculate_metrics(y_val_raw, pred_b)

    # Target C: Residual (posted_rate - base_signal)
    y_train_res = y_train_raw - base_train
    model_c = LGBMRegressor(**config.LGBM_PARAMS)
    model_c.fit(X_train, y_train_res)
    pred_c_res = model_c.predict(X_val)
    pred_c = np.maximum(base_val + pred_c_res, 10.0)
    results["Residual (posted_rate - base_signal)"] = validation.calculate_metrics(y_val_raw, pred_c)

    return results
