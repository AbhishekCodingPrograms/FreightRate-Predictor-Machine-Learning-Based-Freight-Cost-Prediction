import logging
import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from src import config, data_loader, data_validation, preprocessing, features, models, artifact, december_workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_prediction_pipeline(
    artifact_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Runs inference using the saved model artifact WITHOUT retraining the model."""
    logger.info("Loading trained model artifact for inference...")
    art = artifact.load_model_artifact(filepath=artifact_path)
    ensemble: models.FreightRateEnsemble = art["ensemble"]
    stats: dict = art["stats"]
    feature_cols: list = art["feature_names"]
    logger.info(f"Loaded model artifact version '{art.get('model_version', '1.0.0')}' created at {art.get('created_at', 'unknown')}.")

    # 1. Load and Validate Target Validation Dataset (12,000 loads)
    logger.info("Loading validation dataset...")
    val_raw = data_loader.load_validation_data()
    data_validation.validate_dataset(val_raw, is_train=False)

    # 2. Preprocess & Feature Extraction using saved training stats
    val_prep, _ = preprocessing.preprocess_data(val_raw, stats=stats)
    val_feat = features.extract_features(val_prep)

    # 3. Generate Predictions for validation dataset
    logger.info("Generating predictions for 12,000 validation loads...")
    val_preds = ensemble.predict(val_feat[feature_cols], val_feat["base_signal"])

    val_df_out = pd.DataFrame({
        config.ID_COL: val_raw[config.ID_COL],
        "predicted_rate": np.round(val_preds, 2),
    })

    # Save validation predictions to outputs directory and root
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    val_df_out.to_csv(config.VAL_PREDS_PATH, index=False)
    val_df_out.to_csv(config.BASE_DIR / "validation_predictions.csv", index=False)
    logger.info(f"Validation predictions saved: {config.VAL_PREDS_PATH}")

    # 4. Generate December Assessment Forecast (31 daily loads)
    logger.info("Generating December 31-day assessment predictions...")
    dec_df_out = december_workflow.process_december_assessment_forecast(
        ensemble=ensemble,
        stats=stats,
        feature_cols=feature_cols,
        output_path=config.DECEMBER_PREDS_PATH,
    )
    logger.info(f"December predictions saved: {config.DECEMBER_PREDS_PATH}")

    return val_df_out, dec_df_out


if __name__ == "__main__":
    run_prediction_pipeline()
