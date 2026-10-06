import os
import joblib
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.mlops.registry import ModelRegistry


def promote_candidate_model(
    db_session: Session,
    version: str,
    actor: str = "engineer",
    force: bool = False
) -> Tuple[bool, str, Dict[str, Any]]:
    """Evaluates candidate model against current active production model and promotes if validation criteria are met."""
    registry = ModelRegistry(db_session)
    candidate = registry.get_model(version)

    if not candidate:
        return False, f"Model version '{version}' not found in registry.", {}

    if candidate.status == "production" and candidate.is_active:
        return True, f"Model version '{version}' is already active production.", candidate.to_dict()

    if not candidate.artifact_path or not os.path.exists(candidate.artifact_path):
        return False, f"Artifact file missing for version '{version}' at path: {candidate.artifact_path}", {}

    # Verification: artifact can be loaded
    try:
        art = joblib.load(candidate.artifact_path)
        if "preprocessing" not in art or "models" not in art:
            return False, f"Invalid model artifact structure for '{version}'.", {}
    except Exception as e:
        return False, f"Failed to load artifact for '{version}': {e}", {}

    prod_model = registry.get_production_model()

    if prod_model and not force:
        # Promotion gate validation comparison
        cand_metrics = candidate.validation_metrics or {}
        prod_metrics = prod_model.validation_metrics or {}

        cand_mape = cand_metrics.get("mape", float("inf"))
        prod_mape = prod_metrics.get("mape", float("inf"))

        # Evaluation criteria: Candidate MAPE must be <= Production MAPE (or within 1.0% tolerance)
        if cand_mape > prod_mape + 1.0:
            return False, (
                f"Candidate validation MAPE ({cand_mape:.2f}%) exceeds active production MAPE "
                f"({prod_mape:.2f}%). Promotion rejected."
            ), {}

    # Update active production artifact path in root artifacts folder
    prod_artifact_dest = "artifacts/freight_rate_model.joblib"
    try:
        import shutil
        shutil.copyfile(candidate.artifact_path, prod_artifact_dest)
    except Exception as e:
        return False, f"Failed to promote artifact file: {e}", {}

    # Update Registry Status
    updated = registry.update_status(version, "production", actor=actor, reason="Passed validation gate check")

    return True, f"Successfully promoted candidate '{version}' to active production.", updated.to_dict()
