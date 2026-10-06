import pytest
import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np


from src import data_loader, preprocessing, features


def test_feature_extraction():
    df_raw = data_loader.load_train_data().head(100)
    df_prep, _ = preprocessing.preprocess_data(df_raw)
    df_feat = features.extract_features(df_prep)

    feature_names = features.get_feature_names()

    for col in feature_names:
        assert col in df_feat.columns, f"Missing feature: {col}"
        assert not df_feat[col].isna().any(), f"Feature {col} contains NaN values"

    assert (df_feat["base_signal"] > 0).all()
    assert (df_feat["haversine_dist"] >= 0).all()
    assert (df_feat["circuity"] > 0).all()
