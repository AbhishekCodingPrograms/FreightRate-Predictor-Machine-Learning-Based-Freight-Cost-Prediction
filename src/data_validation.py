import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np
from typing import List, Dict, Any, Tuple
from src import config


def validate_dataset(df: pd.DataFrame, is_train: bool = True) -> Tuple[bool, List[str]]:
    """Strictly validates input dataframe schema, data types, value ranges, and target availability.
    
    Raises ValueError with descriptive error messages if critical validation checks fail.
    Returns (True, warnings) if dataset passes validation.
    """
    if df is None or len(df) == 0:
        raise ValueError("Validation Error: Input DataFrame is empty or None")

    errors: List[str] = []
    warnings: List[str] = []

    # 1. Required Columns Check
    required_cols = [
        "pickup", "delivery", "pickup_lat", "pickup_lon",
        "delivery_lat", "delivery_lon", "distance", "equipment",
        "weight", "date"
    ]
    if is_train:
        required_cols.append(config.TARGET_COL)
    else:
        if config.ID_COL in df.columns:
            if df[config.ID_COL].isna().any():
                errors.append(f"Column '{config.ID_COL}' contains missing (NaN) values.")
            if df[config.ID_COL].duplicated().any():
                dup_count = df[config.ID_COL].duplicated().sum()
                errors.append(f"Column '{config.ID_COL}' contains {dup_count} duplicate IDs.")

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required column(s): {missing_cols}")
        raise ValueError("; ".join(errors))

    # 2. Date Column Integrity
    try:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")
        if parsed_dates.isna().any():
            invalid_count = parsed_dates.isna().sum()
            errors.append(f"Column 'date' contains {invalid_count} unparseable date values.")
    except Exception as e:
        errors.append(f"Failed to parse 'date' column: {e}")

    # 3. Distance Validation (Distance must be positive > 0)
    invalid_dist = df["distance"].isna() | (df["distance"] <= 0) | ~np.isfinite(df["distance"])
    if invalid_dist.any():
        errors.append(f"Column 'distance' contains {invalid_dist.sum()} invalid (<=0, NaN, or Inf) values.")

    # 4. Weight Validation Warning
    valid_weights = df["weight"].dropna()
    neg_weights = valid_weights <= 0
    if neg_weights.any():
        warnings.append(f"Column 'weight' contains {neg_weights.sum()} negative values (handled in preprocessing).")

    # 5. Geographic Coordinate Bounds
    if "pickup_lat" in df.columns:
        valid_p_lat = df["pickup_lat"].dropna()
        invalid_p_lat = (valid_p_lat < -90) | (valid_p_lat > 90)
        if invalid_p_lat.any():
            errors.append(f"Column 'pickup_lat' contains {invalid_p_lat.sum()} out-of-bounds latitude values.")

    if "pickup_lon" in df.columns:
        valid_p_lon = df["pickup_lon"].dropna()
        invalid_p_lon = (valid_p_lon < -180) | (valid_p_lon > 180)
        if invalid_p_lon.any():
            errors.append(f"Column 'pickup_lon' contains {invalid_p_lon.sum()} out-of-bounds longitude values.")

    if "delivery_lat" in df.columns:
        valid_d_lat = df["delivery_lat"].dropna()
        invalid_d_lat = (valid_d_lat < -90) | (valid_d_lat > 90)
        if invalid_d_lat.any():
            errors.append(f"Column 'delivery_lat' contains {invalid_d_lat.sum()} out-of-bounds latitude values.")

    if "delivery_lon" in df.columns:
        valid_d_lon = df["delivery_lon"].dropna()
        invalid_d_lon = (valid_d_lon < -180) | (valid_d_lon > 180)
        if invalid_d_lon.any():
            errors.append(f"Column 'delivery_lon' contains {invalid_d_lon.sum()} out-of-bounds longitude values.")

    # 6. Equipment Categories
    allowed_equipment = {"Dry Van", "Reefer", "Flatbed"}
    if "equipment" in df.columns:
        invalid_equip = ~df["equipment"].isin(allowed_equipment) & df["equipment"].notna()
        if invalid_equip.any():
            unknown_cats = set(df.loc[invalid_equip, "equipment"].unique())
            errors.append(f"Column 'equipment' contains invalid categories: {unknown_cats}")

    # 7. Target Validation
    if is_train and config.TARGET_COL in df.columns:
        target = df[config.TARGET_COL]
        invalid_target = target.isna() | (target <= 0) | ~np.isfinite(target)
        if invalid_target.any():
            errors.append(f"Target column '{config.TARGET_COL}' contains {invalid_target.sum()} invalid (<=0, NaN, or Inf) values.")

    if errors:
        raise ValueError("Data Validation Failed:\n - " + "\n - ".join(errors))

    return True, warnings
