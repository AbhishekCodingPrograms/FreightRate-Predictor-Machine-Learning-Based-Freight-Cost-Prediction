import pytest
from pathlib import Path
from src import artifact, models, config


def test_save_and_load_artifact(tmp_path):
    test_path = tmp_path / "test_model.joblib"
    ensemble = models.FreightRateEnsemble()
    stats = {"weight_median": 30000.0, "market_index_median": 1.0}
    feature_names = ["distance", "weight_imputed"]
    metrics = {"rmse": 661.52, "mae": 148.18, "mape": 6.58, "r2": 0.8121}

    saved_path = artifact.save_model_artifact(
        ensemble=ensemble,
        stats=stats,
        feature_names=feature_names,
        metrics=metrics,
        filepath=test_path,
    )

    assert saved_path.exists()

    loaded = artifact.load_model_artifact(filepath=saved_path)
    assert loaded["model_version"] == "1.0.0"
    assert loaded["stats"]["weight_median"] == 30000.0
    assert loaded["feature_names"] == feature_names
    assert loaded["metrics"]["mape"] == 6.58
