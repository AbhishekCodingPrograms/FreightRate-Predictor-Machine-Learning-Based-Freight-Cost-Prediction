"""
Unit tests for output prediction format, shapes, non-negativity, and schema validity.
"""
import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np

from pathlib import Path

from src import config


def test_validation_predictions_format():
    path = config.VAL_PREDS_PATH
    if not path.exists():
        path = config.BASE_DIR / "validation_predictions.csv"

    assert path.exists(), "validation_predictions.csv file not found"

    df = pd.read_csv(path)
    assert list(df.columns) == ["load_id", "predicted_rate"]
    assert len(df) == 12000
    assert not df["load_id"].isna().any()
    assert not df["load_id"].duplicated().any()
    assert (df["predicted_rate"] > 0).all()


def test_december_predictions_format():
    path = config.DECEMBER_PREDS_PATH
    if not path.exists():
        path = config.DECEMBER_INPUT_PATH

    assert path.exists(), "december predictions file not found"

    df = pd.read_csv(path)
    expected_cols = ["pickup", "delivery", "distance", "equipment", "weight", "date", "predicted_rate"]
    assert list(df.columns) == expected_cols
    assert len(df) == 31
    assert (df["predicted_rate"] > 0).all()
    assert df["pickup"].eq("Lexington").all()
    assert df["delivery"].eq("Fort Wayne").all()
    assert np.isclose(df["distance"], 360.0).all()
    assert df["equipment"].eq("Dry Van").all()
    assert np.isclose(df["weight"], 32000.0).all()
