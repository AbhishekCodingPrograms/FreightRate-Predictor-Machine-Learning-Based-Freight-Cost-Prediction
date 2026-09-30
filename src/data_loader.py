import pandas as pd
from pathlib import Path
from typing import Optional
from src import config


def load_train_data(path: Optional[Path] = None) -> pd.DataFrame:
    filepath = path or config.TRAIN_PATH
    if not filepath.exists():
        filepath = config.DATA_DIR / "train_test.csv"
    if not filepath.exists():
        filepath = config.BASE_DIR / "train-test.csv"

    df = pd.read_csv(filepath)
    df[config.DATE_COL] = pd.to_datetime(df[config.DATE_COL])
    return df


def load_validation_data(path: Optional[Path] = None) -> pd.DataFrame:
    filepath = path or config.VAL_PATH
    if not filepath.exists():
        filepath = config.BASE_DIR / "validation.csv"

    df = pd.read_csv(filepath)
    df[config.DATE_COL] = pd.to_datetime(df[config.DATE_COL])
    return df


def load_december_data(path: Optional[Path] = None) -> pd.DataFrame:
    filepath = path or config.DECEMBER_INPUT_PATH
    if not filepath.exists():
        filepath = config.DATA_DIR / "december_chart_inputs.csv"
    if not filepath.exists():
        filepath = config.BASE_DIR / "december-chart-inputs.csv"

    df = pd.read_csv(filepath)
    df[config.DATE_COL] = pd.to_datetime(df[config.DATE_COL])
    return df


def verify_data_integrity(df: pd.DataFrame, is_train: bool = True) -> bool:
    if df is None or len(df) == 0:
        raise ValueError("DataFrame is empty or None")

    required = [
        "pickup", "delivery", "pickup_lat", "pickup_lon",
        "delivery_lat", "delivery_lon", "distance", "equipment",
        "weight", "date", "market_index", "quote_signal"
    ]
    if is_train:
        required.append(config.TARGET_COL)
    else:
        required.append(config.ID_COL)

    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return True
