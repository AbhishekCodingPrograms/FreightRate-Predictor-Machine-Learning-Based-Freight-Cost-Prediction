import pytest
from pathlib import Path
from src import artifact, models, config
from app.core.exceptions import ModelNotLoadedError
from app.services.model_service import ModelService


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


def test_model_service_rejects_incompatible_legacy_artifact():
    legacy_path = config.BASE_DIR / "models" / "freight_rate_model.joblib"
    service = ModelService(artifact_path=legacy_path)

    with pytest.raises(ModelNotLoadedError, match="missing estimators"):
        service.load_artifact()

    assert not service.is_loaded


def test_sklearn_loss_alias_registration():
    import sys
    artifact.register_sklearn_loss_aliases()
    assert "_loss" in sys.modules

