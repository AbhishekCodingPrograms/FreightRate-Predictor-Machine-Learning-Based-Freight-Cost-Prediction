import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score


def evaluate_delayed_performance(
    predictions: List[Dict[str, Any]],
    outcomes: List[Dict[str, Any]],
    min_sample_size: int = 5
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Calculates delayed model evaluation metrics by matching stored predictions with actual outcomes by load_id."""
    if not predictions or not outcomes:
        return [], None

    pred_df = pd.DataFrame(predictions)
    out_df = pd.DataFrame(outcomes)

    if "load_id" not in pred_df.columns or "load_id" not in out_df.columns:
        return [], None

    merged = pd.merge(pred_df, out_df, on="load_id", how="inner", suffixes=("_pred", "_actual"))
    if len(merged) < min_sample_size:
        return [], None

    actuals = merged["actual_posted_rate"].values
    preds = merged["predicted_rate"].values
    residuals = actuals - preds

    rmse = float(root_mean_squared_error(actuals, preds))
    mae = float(mean_absolute_error(actuals, preds))
    
    # Avoid zero division in MAPE
    valid_mask = actuals != 0
    if np.any(valid_mask):
        mape = float(np.mean(np.abs(residuals[valid_mask] / actuals[valid_mask])) * 100.0)
    else:
        mape = 0.0

    r2 = float(r2_score(actuals, preds))
    res_mean = float(np.mean(residuals))
    res_std = float(np.std(residuals))

    model_version = merged["model_version"].iloc[0] if "model_version" in merged.columns else "unknown"

    global_metric = {
        "model_version": model_version,
        "sample_size": len(merged),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mape": round(mape, 2),
        "r2": round(r2, 4),
        "residual_mean": round(res_mean, 2),
        "residual_std": round(res_std, 2),
        "segment_name": "all",
        "segment_value": "all",
    }

    metrics_list = [global_metric]

    # Segment performance by equipment
    if "input_data" in merged.columns:
        merged["equipment"] = merged["input_data"].apply(
            lambda x: x.get("equipment", "Unknown") if isinstance(x, dict) else "Unknown"
        )
        
        for eq_type, grp in merged.groupby("equipment"):
            if len(grp) >= min_sample_size:
                act = grp["actual_posted_rate"].values
                prd = grp["predicted_rate"].values
                res = act - prd
                s_rmse = float(root_mean_squared_error(act, prd))
                s_mae = float(mean_absolute_error(act, prd))
                s_mape = float(np.mean(np.abs(res / act)) * 100.0) if np.all(act != 0) else 0.0
                s_r2 = float(r2_score(act, prd)) if len(grp) > 1 else 0.0

                metrics_list.append({
                    "model_version": model_version,
                    "sample_size": len(grp),
                    "rmse": round(s_rmse, 2),
                    "mae": round(s_mae, 2),
                    "mape": round(s_mape, 2),
                    "r2": round(s_r2, 4),
                    "residual_mean": round(float(np.mean(res)), 2),
                    "residual_std": round(float(np.std(res)), 2),
                    "segment_name": "equipment",
                    "segment_value": str(eq_type),
                })

    return metrics_list, global_metric
