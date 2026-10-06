import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Tuple


def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """Calculates Population Stability Index (PSI) between baseline reference and production sample."""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_buckets + 1)
    buckets = np.percentile(expected, percentiles)
    buckets[0] -= 1e-5
    buckets[-1] += 1e-5

    # Ensure unique bucket edges
    buckets = np.unique(buckets)
    if len(buckets) < 2:
        return 0.0

    exp_counts, _ = np.histogram(expected, bins=buckets)
    act_counts, _ = np.histogram(actual, bins=buckets)

    exp_pct = exp_counts / len(expected)
    act_pct = act_counts / len(actual)

    # Avoid zero division
    exp_pct = np.where(exp_pct == 0, 0.0001, exp_pct)
    act_pct = np.where(act_pct == 0, 0.0001, act_pct)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(round(psi_val, 4))


def detect_feature_drift(
    baseline_df: pd.DataFrame,
    prod_payloads: List[Dict[str, Any]],
    numeric_features: List[str] = ["distance", "weight", "market_index", "quote_signal"]
) -> Tuple[List[Dict[str, Any]], str]:
    """Detects statistical feature drift between baseline reference training data and production input samples."""
    if not prod_payloads or baseline_df.empty:
        return [], "NORMAL"

    prod_df = pd.DataFrame(prod_payloads)
    drift_metrics = []
    overall_status = "NORMAL"

    for feat in numeric_features:
        if feat not in baseline_df.columns or feat not in prod_df.columns:
            continue

        baseline_vals = pd.to_numeric(baseline_df[feat], errors="coerce").dropna().values
        prod_vals = pd.to_numeric(prod_df[feat], errors="coerce").dropna().values

        if len(prod_vals) < 5 or len(baseline_vals) < 5:
            continue

        psi_score = calculate_psi(baseline_vals, prod_vals)

        # KS test
        ks_stat, p_val = stats.ks_2samp(baseline_vals, prod_vals)

        status = "NORMAL"
        if psi_score >= 0.25:
            status = "CRITICAL"
            overall_status = "CRITICAL"
        elif psi_score >= 0.1 and overall_status != "CRITICAL":
            status = "WARNING"
            overall_status = "WARNING"

        drift_metrics.append({
            "feature_name": feat,
            "metric_type": "PSI",
            "metric_value": psi_score,
            "ks_statistic": float(round(ks_stat, 4)),
            "ks_pvalue": float(round(p_val, 4)),
            "threshold_warning": 0.1,
            "threshold_critical": 0.25,
            "status": status,
        })

    return drift_metrics, overall_status
