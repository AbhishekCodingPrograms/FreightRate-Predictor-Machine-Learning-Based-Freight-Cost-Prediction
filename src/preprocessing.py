import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


def haversine_distance(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Computes great-circle distance in miles between coordinate pairs."""
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return 3958.8 * c


def preprocess_data(df: pd.DataFrame, stats: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Cleans raw dataframe, computes haversine distance, and imputes missing weight and market index."""
    df = df.copy()

    if stats is None:
        stats = {
            "weight_median": float(df["weight"].median()),
            "market_index_median": float(df["market_index"].median()),
        }

    df["weight_imputed"] = df["weight"].fillna(stats["weight_median"])
    df["market_index_imputed"] = df["market_index"].fillna(stats["market_index_median"])

    # Geometry & circuity
    df["haversine_dist"] = haversine_distance(
        df["pickup_lat"].values,
        df["pickup_lon"].values,
        df["delivery_lat"].values,
        df["delivery_lon"].values
    )
    df["circuity"] = df["distance"] / (df["haversine_dist"] + 1e-5)

    return df, stats
