from typing import List, Dict, Any, Tuple
import pandas as pd


VALID_EQUIPMENT = {"Dry Van", "Reefer", "Flatbed"}


def audit_prediction_data_quality(input_payloads: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], str]:
    """Audits input prediction payloads for missing values, out-of-bounds coordinates, and invalid values."""
    if not input_payloads:
        return [], "NORMAL"

    df = pd.DataFrame(input_payloads)
    total_records = len(df)

    expected_features = [
        "pickup", "delivery", "pickup_lat", "pickup_lon",
        "delivery_lat", "delivery_lon", "distance", "equipment", "weight"
    ]

    metrics = []
    overall_status = "NORMAL"

    for feat in expected_features:
        if feat not in df.columns:
            missing_count = total_records
            invalid_count = 0
        else:
            missing_count = int(df[feat].isna().sum() + (df[feat] == "").sum())
            invalid_count = 0

            # Domain rule validation
            if feat in ["pickup_lat", "delivery_lat"]:
                invalid_count = int(((df[feat] < -90) | (df[feat] > 90)).sum())
            elif feat in ["pickup_lon", "delivery_lon"]:
                invalid_count = int(((df[feat] < -180) | (df[feat] > 180)).sum())
            elif feat in ["distance", "weight"]:
                invalid_count = int((df[feat] <= 0).sum())
            elif feat == "equipment":
                invalid_count = int((~df[feat].isin(VALID_EQUIPMENT)).sum())

        missing_pct = round((missing_count / total_records) * 100.0, 2)
        invalid_pct = round((invalid_count / total_records) * 100.0, 2)

        feat_status = "NORMAL"
        if missing_pct > 15.0 or invalid_pct > 10.0:
            feat_status = "CRITICAL"
            overall_status = "CRITICAL"
        elif (missing_pct > 5.0 or invalid_pct > 2.0) and overall_status != "CRITICAL":
            feat_status = "WARNING"
            overall_status = "WARNING"

        metrics.append({
            "feature_name": feat,
            "total_records": total_records,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "invalid_count": invalid_count,
            "invalid_pct": invalid_pct,
            "status": feat_status,
        })

    return metrics, overall_status
