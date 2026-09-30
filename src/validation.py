import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import KFold


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / (y_true + 1e-5))) * 100.0)
    r2 = float(r2_score(y_true, y_pred))

    return {
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
    }


def split_oot_data(df: pd.DataFrame, train_cutoff_month: int = 8) -> Tuple[pd.DataFrame, pd.DataFrame]:
    months = pd.to_datetime(df["date"]).dt.month
    train_df = df[months <= train_cutoff_month].copy().reset_index(drop=True)
    val_df = df[months > train_cutoff_month].copy().reset_index(drop=True)
    return train_df, val_df


def run_cross_validation(
    model_cls,
    model_params: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    base_signal: pd.Series,
    n_splits: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof_preds = np.zeros(len(X))
    fold_metrics = []
    y_residual = y - base_signal

    for fold, (tr_idx, va_idx) in enumerate(kf.split(X)):
        X_tr, y_tr_res = X.iloc[tr_idx], y_residual.iloc[tr_idx]
        X_va, y_va = X.iloc[va_idx], y.iloc[va_idx]
        base_va = base_signal.iloc[va_idx]

        model = model_cls(**model_params)
        model.fit(X_tr, y_tr_res)

        preds_res = model.predict(X_va)
        preds_total = base_va + preds_res
        oof_preds[va_idx] = preds_total

        fold_metrics.append(calculate_metrics(y_va, preds_total))

    overall_metrics = calculate_metrics(y, oof_preds)
    return {
        "overall": overall_metrics,
        "folds": fold_metrics,
        "oof_preds": oof_preds,
    }
