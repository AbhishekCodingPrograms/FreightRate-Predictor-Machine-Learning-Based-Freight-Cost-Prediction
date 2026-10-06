import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from typing import Dict, Any, Tuple, Optional


def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Computes great-circle distance in miles between coordinate pairs."""
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return 3958.8 * c


def fit_preprocessing_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes preprocessing statistics strictly from training data to avoid data leakage."""
    valid_weights = df["weight"].dropna() if "weight" in df.columns else pd.Series(dtype=float)
    valid_weights = np.abs(valid_weights[valid_weights != 0])
    weight_med = float(valid_weights.median()) if len(valid_weights) > 0 else 30000.0

    valid_mi = df["market_index"].dropna() if "market_index" in df.columns else pd.Series(dtype=float)
    valid_mi = valid_mi[valid_mi > 0]
    mi_med = float(valid_mi.median()) if len(valid_mi) > 0 else 1.0

    valid_qs = df["quote_signal"].dropna() if "quote_signal" in df.columns else pd.Series(dtype=float)
    valid_qs = valid_qs[valid_qs > 0]
    qs_med = float(valid_qs.median()) if len(valid_qs) > 0 else 5.25
    qs_mean = float(valid_qs.mean()) if len(valid_qs) > 0 else 5.25

    stats = {
        "weight_median": weight_med,
        "market_index_median": mi_med,
        "quote_signal_median": qs_med,
        "quote_signal_mean": qs_mean,
        "pickup_lat_median": float(df["pickup_lat"].median()) if "pickup_lat" in df.columns and df["pickup_lat"].notna().any() else 38.0464,
        "pickup_lon_median": float(df["pickup_lon"].median()) if "pickup_lon" in df.columns and df["pickup_lon"].notna().any() else -84.4970,
        "delivery_lat_median": float(df["delivery_lat"].median()) if "delivery_lat" in df.columns and df["delivery_lat"].notna().any() else 41.0793,
        "delivery_lon_median": float(df["delivery_lon"].median()) if "delivery_lon" in df.columns and df["delivery_lon"].notna().any() else -85.1394,
    }
    return stats


def preprocess_data(df: pd.DataFrame, stats: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Applies preprocessing transformations strictly using fitted statistics.
    
    If stats is None, fits stats on df (assumed to be training data).
    """
    df = df.copy()

    if stats is None:
        stats = fit_preprocessing_stats(df)

    # Clean negative weight data entry errors safely by taking absolute value
    if "weight" in df.columns:
        df["weight"] = np.abs(df["weight"])

    # Impute missing values with fitted training stats
    df["weight_imputed"] = df["weight"].fillna(stats["weight_median"])
    df["market_index_imputed"] = df["market_index"].fillna(stats["market_index_median"])

    if "quote_signal" in df.columns:
        df["quote_signal"] = df["quote_signal"].fillna(stats["quote_signal_median"])
    else:
        df["quote_signal"] = stats["quote_signal_median"]

    p_lat = df["pickup_lat"].fillna(stats["pickup_lat_median"]).values
    p_lon = df["pickup_lon"].fillna(stats["pickup_lon_median"]).values
    d_lat = df["delivery_lat"].fillna(stats["delivery_lat_median"]).values
    d_lon = df["delivery_lon"].fillna(stats["delivery_lon_median"]).values

    # Geometry & circuity
    df["haversine_dist"] = haversine_distance(p_lat, p_lon, d_lat, d_lon)
    safe_dist = np.maximum(df["distance"].values, 0.1)
    df["circuity"] = safe_dist / (df["haversine_dist"] + 1e-5)

    return df, stats
