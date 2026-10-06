import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from typing import Dict, Tuple, Any, List
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.optimize import minimize


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculates evaluation metrics (RMSE, MAE, MAPE, R2) safely."""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))

    # Safe MAPE calculation avoiding division by zero
    safe_denom = np.maximum(np.abs(y_true), 1e-5)
    mape = float(np.mean(np.abs((y_true - y_pred) / safe_denom)) * 100.0)
    r2 = float(r2_score(y_true, y_pred))

    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "count": len(y_true),
        "residual_mean": round(float(np.mean(y_true - y_pred)), 2),
        "residual_std": round(float(np.std(y_true - y_pred)), 2),
    }


def split_oot_data(df: pd.DataFrame, train_cutoff_month: int = 8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Partitions dataset into OOT Train (Jan-Aug) and OOT Validation (Sep-Oct)."""
    months = pd.to_datetime(df["date"]).dt.month
    train_df = df[months <= train_cutoff_month].copy().reset_index(drop=True)
    val_df = df[months > train_cutoff_month].copy().reset_index(drop=True)
    return train_df, val_df


def time_aware_cross_validation(
    model_cls,
    model_params: Dict[str, Any],
    df_train: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "posted_rate",
    min_train_months: int = 4,
) -> Dict[str, Any]:
    """Performs expanding-window temporal cross validation across training months."""
    months = pd.to_datetime(df_train["date"]).dt.month
    max_month = int(months.max())

    fold_metrics = []
    oof_preds = np.zeros(len(df_train))

    for cutoff in range(min_train_months, max_month):
        tr_mask = months <= cutoff
        va_mask = months == (cutoff + 1)

        if not va_mask.any():
            continue

        X_tr = df_train.loc[tr_mask, feature_cols]
        y_tr_res = df_train.loc[tr_mask, target_col] - df_train.loc[tr_mask, "base_signal"]

        X_va = df_train.loc[va_mask, feature_cols]
        y_va = df_train.loc[va_mask, target_col]
        base_va = df_train.loc[va_mask, "base_signal"]

        model = model_cls(**model_params)
        model.fit(X_tr, y_tr_res)

        res_preds = model.predict(X_va)
        total_preds = np.maximum(base_va.values + res_preds, 10.0)

        oof_preds[va_mask.values] = total_preds
        fold_metrics.append(calculate_metrics(y_va.values, total_preds))

    evaluated_mask = oof_preds > 0
    overall = calculate_metrics(df_train.loc[evaluated_mask, target_col].values, oof_preds[evaluated_mask])

    return {
        "overall": overall,
        "folds": fold_metrics,
        "oof_preds": oof_preds,
    }


def find_optimal_ensemble_weights(
    y_true: np.ndarray,
    lgb_preds: np.ndarray,
    cat_preds: np.ndarray,
    xgb_preds: np.ndarray,
) -> Dict[str, float]:
    """Optimizes ensemble weights via constrained optimization on internal validation predictions."""
    def loss_fn(weights):
        w_lgb, w_cat, w_xgb = weights
        combo = w_lgb * lgb_preds + w_cat * cat_preds + w_xgb * xgb_preds
        return mean_squared_error(y_true, combo)

    init_weights = [0.33, 0.33, 0.34]
    bounds = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
    constraints = ({'type': 'eq', 'fun': lambda w: 1.0 - sum(w)})

    res = minimize(loss_fn, init_weights, method='SLSQP', bounds=bounds, constraints=constraints)
    if res.success:
        w = res.x
        return {
            "lgbm": round(float(w[0]), 3),
            "catboost": round(float(w[1]), 3),
            "xgboost": round(float(w[2]), 3),
        }
    return {"lgbm": 0.4, "catboost": 0.4, "xgboost": 0.2}
