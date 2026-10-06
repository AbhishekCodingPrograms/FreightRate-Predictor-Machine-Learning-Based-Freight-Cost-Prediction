import os
import shutil
import joblib
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.mlops.registry import ModelRegistry


def rollback_production_model(
    db_session: Session,
    target_version: str,
    actor: str = "operator"
) -> Tuple[bool, str, Dict[str, Any]]:
    """Safely rolls back production model reference to an earlier version while preserving historical records."""
    registry = ModelRegistry(db_session)
    target_model = registry.get_model(target_version)

    if not target_model:
        return False, f"Target rollback version '{target_version}' not found in registry.", {}

    if not target_model.artifact_path or not os.path.exists(target_model.artifact_path):
        return False, f"Target artifact file missing at: {target_model.artifact_path}", {}

    # Verify target artifact loadability
    try:
        joblib.load(target_model.artifact_path)
    except Exception as e:
        return False, f"Corrupted rollback artifact: {e}", {}

    # Overwrite production artifact location if target is a different file
    prod_artifact_dest = "artifacts/freight_rate_model.joblib"
    if os.path.abspath(target_model.artifact_path) != os.path.abspath(prod_artifact_dest):
        try:
            shutil.copyfile(target_model.artifact_path, prod_artifact_dest)
        except Exception as e:
            return False, f"Failed to restore artifact file: {e}", {}

    # Update Registry Status
    updated = registry.update_status(target_version, "production", actor=actor, reason=f"Rollback to {target_version}")

    return True, f"Successfully rolled back production model to version '{target_version}'.", updated.to_dict()
