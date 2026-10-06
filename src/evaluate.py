import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np
from typing import Dict, Any


from src import validation, models, features


def evaluate_model_performance(
    ensemble: models.FreightRateEnsemble,
    df_feat: pd.DataFrame,
    target_col: str = "posted_rate",
) -> Dict[str, Any]:
    feature_cols = features.get_feature_names()
    X = df_feat[feature_cols]
    y_true = df_feat[target_col]
    base_signal = df_feat["base_signal"]

    y_pred = ensemble.predict(X, base_signal)
    metrics = validation.calculate_metrics(y_true, y_pred)
    residuals = y_true - y_pred

    return {
        "metrics": metrics,
        "residual_mean": float(np.mean(residuals)),
        "residual_std": float(np.std(residuals)),
        "feature_importances": ensemble.get_feature_importances(feature_cols),
    }


def print_evaluation_report(summary: Dict[str, Any]):
    m = summary["metrics"]
    print("\n--- Model Evaluation Summary ---")
    print(f"RMSE : ${m['rmse']:.2f}")
    print(f"MAE  : ${m['mae']:.2f}")
    print(f"MAPE : {m['mape']:.2f}%")
    print(f"R^2  : {m['r2']:.4f}")
    print(f"Residuals: mean = ${summary['residual_mean']:.2f}, std = ${summary['residual_std']:.2f}\n")
    print("Top Feature Importances:")
    print(summary["feature_importances"].head(8).to_string(index=False))
    print("--------------------------------\n")
