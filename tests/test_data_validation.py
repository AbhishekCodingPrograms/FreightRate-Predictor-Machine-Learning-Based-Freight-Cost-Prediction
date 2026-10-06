import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np

from src import data_validation, data_loader


def test_valid_data_validation():
    df_train = data_loader.load_train_data().head(50)
    passed, warnings = data_validation.validate_dataset(df_train, is_train=True)
    assert passed is True


def test_missing_required_column():
    df_invalid = data_loader.load_train_data().head(10).drop(columns=["distance"])
    with pytest.raises(ValueError, match="Missing required column"):
        data_validation.validate_dataset(df_invalid, is_train=True)


def test_negative_distance_validation():
    df_invalid = data_loader.load_train_data().head(10).copy()
    df_invalid.loc[0, "distance"] = -50.0
    with pytest.raises(ValueError, match="distance"):
        data_validation.validate_dataset(df_invalid, is_train=True)


def test_invalid_equipment_validation():
    df_invalid = data_loader.load_train_data().head(10).copy()
    df_invalid.loc[0, "equipment"] = "Hovercraft"
    with pytest.raises(ValueError, match="equipment"):
        data_validation.validate_dataset(df_invalid, is_train=True)


def test_invalid_coordinates_validation():
    df_invalid = data_loader.load_train_data().head(10).copy()
    df_invalid.loc[0, "pickup_lat"] = 185.0
    with pytest.raises(ValueError, match="pickup_lat"):
        data_validation.validate_dataset(df_invalid, is_train=True)


def test_duplicate_load_id_validation():
    df_val = data_loader.load_validation_data().head(10).copy()
    df_val.loc[1, "load_id"] = df_val.loc[0, "load_id"]
    with pytest.raises(ValueError, match="duplicate"):
        data_validation.validate_dataset(df_val, is_train=False)
