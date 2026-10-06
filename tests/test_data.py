"""
Unit tests for data loading and data integrity validation.
"""
import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
from pathlib import Path


from src import config, data_loader


def test_load_train_data():
    df = data_loader.load_train_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 48000
    assert config.TARGET_COL in df.columns
    assert "date" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_load_validation_data():
    df = data_loader.load_validation_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 12000
    assert config.ID_COL in df.columns
    assert config.TARGET_COL not in df.columns


def test_verify_data_integrity():
    df_train = data_loader.load_train_data()
    assert data_loader.verify_data_integrity(df_train, is_train=True) is True

    df_val = data_loader.load_validation_data()
    assert data_loader.verify_data_integrity(df_val, is_train=False) is True


def test_empty_data_integrity():
    df_empty = pd.DataFrame()
    with pytest.raises(ValueError):
        data_loader.verify_data_integrity(df_empty, is_train=True)
