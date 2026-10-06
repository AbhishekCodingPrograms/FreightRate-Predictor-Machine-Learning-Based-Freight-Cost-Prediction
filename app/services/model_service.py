from pathlib import Path
from typing import Dict, Any, Optional
from app.config import settings
from app.core.logging import logger
from app.core.exceptions import ModelNotLoadedError
from src import artifact, models


class ModelService:
    """Manages model artifact lifecycle, safe loading, and metadata inspection."""

    def __init__(self, artifact_path: Optional[Path] = None):
        self.artifact_path = artifact_path or settings.MODEL_ARTIFACT_PATH
        self.artifact: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False

    def load_artifact(self) -> None:
        """Loads model artifact safely from disk. Fails cleanly without retraining if artifact is missing."""
        logger.info(f"Loading trained model artifact from: {self.artifact_path}")
        try:
            self.artifact = artifact.load_model_artifact(filepath=self.artifact_path)
            self._validate_artifact(self.artifact)
            self.is_loaded = True
            logger.info(
                f"Model artifact successfully loaded. Version='{self.get_model_version()}', "
                f"Features={len(self.get_feature_names())}, Seed={self.artifact.get('random_seed')}."
            )
        except Exception as exc:
            self.is_loaded = False
            self.artifact = None
            logger.error(f"Failed to load model artifact from {self.artifact_path}: {exc}", exc_info=True)
            raise ModelNotLoadedError(f"Model artifact at '{self.artifact_path}' could not be loaded: {exc}")

    def _validate_artifact(self, art: Dict[str, Any]) -> None:
        """Validates that loaded artifact contains all mandatory keys and fitted model ensemble."""
        required_keys = ["ensemble", "stats", "feature_names", "model_version"]
        missing = [k for k in required_keys if k not in art]
        if missing:
            raise ValueError(f"Model artifact is missing required keys: {missing}")

        ensemble = art["ensemble"]
        if not hasattr(ensemble, "predict") or not getattr(ensemble, "fitted", False):
            raise ValueError("Loaded model ensemble object is not properly fitted")

    def get_ensemble(self) -> models.FreightRateEnsemble:

        if not self.is_loaded or self.artifact is None:
            raise ModelNotLoadedError()
        return self.artifact["ensemble"]

    def get_stats(self) -> Dict[str, Any]:
        if not self.is_loaded or self.artifact is None:
            raise ModelNotLoadedError()
        return self.artifact["stats"]

    def get_feature_names(self) -> list:
        if not self.is_loaded or self.artifact is None:
            raise ModelNotLoadedError()
        return self.artifact["feature_names"]

    def get_model_version(self) -> str:
        if not self.is_loaded or self.artifact is None:
            return "unknown"
        return self.artifact.get("model_version", "1.0.0")

    def get_model_info(self) -> Dict[str, Any]:
        if not self.is_loaded or self.artifact is None:
            raise ModelNotLoadedError()

        ensemble: models.FreightRateEnsemble = self.artifact["ensemble"]
        return {
            "model_version": self.get_model_version(),
            "created_at": self.artifact.get("created_at", "unknown"),
            "random_seed": self.artifact.get("random_seed", 42),
            "target_strategy": self.artifact.get("target_strategy", "residual"),
            "ensemble_weights": ensemble.weights,
            "feature_count": len(self.get_feature_names()),
            "feature_names": self.get_feature_names(),
            "metrics": self.artifact.get("metrics", {}),
        }


# Global singleton instance of ModelService
model_service = ModelService()
