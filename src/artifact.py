import joblib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from src import config, models


ARTIFACT_DIR = config.BASE_DIR / "artifacts"
ARTIFACT_DEFAULT_PATH = ARTIFACT_DIR / "freight_rate_model.joblib"


def register_sklearn_loss_aliases() -> None:
    """Registers sys.modules aliases for scikit-learn _loss module across versions to handle pickle compatibility."""
    import sys
    try:
        import sklearn._loss
        sys.modules.setdefault("_loss", sklearn._loss)
        sys.modules.setdefault("sklearn._loss", sklearn._loss)
        sys.modules.setdefault("sklearn.ensemble._hist_gradient_boosting._loss", sklearn._loss)
        if hasattr(sklearn._loss, "_loss"):
            sys.modules.setdefault("sklearn._loss._loss", sklearn._loss._loss)
    except Exception:
        pass

    try:
        import sklearn.ensemble._hist_gradient_boosting._loss as _hgb_loss
        sys.modules.setdefault("_loss", _hgb_loss)
        sys.modules.setdefault("sklearn._loss", _hgb_loss)
        sys.modules.setdefault("sklearn.ensemble._hist_gradient_boosting._loss", _hgb_loss)
    except Exception:
        pass


# Register aliases immediately on module import
register_sklearn_loss_aliases()


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

    joblib.dump(artifact, save_path, compress=3)
    
    # Also save a copy to outputs dir for convenience
    alt_copy = config.OUTPUT_DIR / "freight_rate_model.joblib"
    alt_copy.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, alt_copy, compress=3)

    return save_path


def load_model_artifact(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """Loads model artifact from disk without retraining."""
    register_sklearn_loss_aliases()

    candidate_paths: List[Path] = []
    if filepath:
        candidate_paths.append(Path(filepath))
    candidate_paths.extend([
        ARTIFACT_DEFAULT_PATH,
        config.OUTPUT_DIR / "freight_rate_model.joblib",
        config.BASE_DIR / "models" / "freight_rate_model.joblib",
    ])

    # Deduplicate preserving order
    unique_paths: List[Path] = []
    for p in candidate_paths:
        if p not in unique_paths:
            unique_paths.append(p)

    last_error: Optional[Exception] = None
    for path in unique_paths:
        if path.exists():
            try:
                artifact = joblib.load(path)
                return artifact
            except Exception as exc:
                last_error = exc
                continue

    if last_error:
        raise RuntimeError(
            f"Failed to load model artifact from any candidate path: {last_error}"
        ) from last_error
    else:
        raise FileNotFoundError(
            f"Model artifact not found at {[str(p) for p in unique_paths]}. "
            "Please train the model first by running: python -m src.train"
        )

