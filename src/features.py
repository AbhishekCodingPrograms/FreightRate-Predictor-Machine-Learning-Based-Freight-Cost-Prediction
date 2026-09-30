import numpy as np
import pandas as pd
from typing import List

FEATURE_COLUMNS = [
    "distance",
    "pickup_lat",
    "pickup_lon",
    "delivery_lat",
    "delivery_lon",
    "haversine_dist",
    "circuity",
    "weight_imputed",
    "market_index_imputed",
    "quote_signal",
    "base_signal",
    "market_signal",
    "weight_per_mile",
    "month",
    "day",
    "dayofweek",
    "dayofyear",
    "is_weekend",
    "sin_month",
    "cos_month",
    "sin_dayofweek",
    "cos_dayofweek",
    "is_reefer",
    "is_flatbed",
    "is_dryvan",
]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Calendar features
    dates = pd.to_datetime(df["date"])
    df["month"] = dates.dt.month
    df["day"] = dates.dt.day
    df["dayofweek"] = dates.dt.dayofweek
    df["dayofyear"] = dates.dt.dayofyear
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)

    # Cyclical date transformations
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12)
    df["sin_dayofweek"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["cos_dayofweek"] = np.cos(2 * np.pi * df["dayofweek"] / 7)

    # Base domain interaction signals
    df["base_signal"] = df["distance"] * df["quote_signal"]
    df["market_signal"] = df["distance"] * df["quote_signal"] * df["market_index_imputed"]
    df["weight_per_mile"] = df["weight_imputed"] / (df["distance"] + 1e-5)

    # Equipment encoding
    df["is_reefer"] = (df["equipment"] == "Reefer").astype(int)
    df["is_flatbed"] = (df["equipment"] == "Flatbed").astype(int)
    df["is_dryvan"] = (df["equipment"] == "Dry Van").astype(int)

    return df


def get_feature_names() -> List[str]:
    return FEATURE_COLUMNS.copy()
