import joblib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from src import config, models


ARTIFACT_DIR = config.BASE_DIR / "artifacts"
ARTIFACT_DEFAULT_PATH = ARTIFACT_DIR / "freight_rate_model.joblib"


def save_model_artifact(
    ensemble: models.FreightRateEnsemble,
    stats: Dict[str, Any],
    feature_names: List[str],
    metrics: Optional[Dict[str, Any]] = None,
    filepath: Optional[Path] = None,
) -> Path:
    """Serializes model ensemble, preprocessing stats, feature names, and metadata into a clean artifact."""
    save_path = filepath or ARTIFACT_DEFAULT_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model_version": "1.0.0",
        "created_at": datetime.utcnow().isoformat(),
        "random_seed": config.SEED,
        "target_strategy": "residual (posted_rate - base_signal)",
        "ensemble_weights": ensemble.weights,
        "ensemble": ensemble,
        "stats": stats,
        "feature_names": feature_names,
        "metrics": metrics or {},
    }

    joblib.dump(artifact, save_path)
    
    # Also save a copy to outputs dir for convenience
    alt_copy = config.OUTPUT_DIR / "freight_rate_model.joblib"
    alt_copy.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, alt_copy)

    return save_path


def load_model_artifact(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """Loads model artifact from disk without retraining."""
    import sys
    try:
        import sklearn._loss
        sys.modules.setdefault("sklearn.ensemble._hist_gradient_boosting._loss", sklearn._loss)
    except Exception:
        pass
    try:
        import sklearn.ensemble._hist_gradient_boosting._loss as _hgb_loss
        sys.modules.setdefault("sklearn._loss", _hgb_loss)
    except Exception:
        pass

    load_path = filepath or ARTIFACT_DEFAULT_PATH
    if not load_path.exists():
        fallback = config.OUTPUT_DIR / "freight_rate_model.joblib"
        if fallback.exists():
            load_path = fallback
        else:
            models_fallback = config.BASE_DIR / "models" / "freight_rate_model.joblib"
            if models_fallback.exists():
                load_path = models_fallback
            else:
                raise FileNotFoundError(
                    f"Model artifact not found at {load_path}. "
                    "Please train the model first by running: python -m src.train"
                )

    artifact = joblib.load(load_path)
    return artifact
