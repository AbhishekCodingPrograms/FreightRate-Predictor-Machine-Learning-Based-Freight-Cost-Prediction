import pandas as pd
import numpy as np
from typing import Tuple

from src import config, data_loader, preprocessing, features, models


def run_prediction_pipeline(
    ensemble: models.FreightRateEnsemble, stats: dict
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    print("Loading validation dataset...")
    val_raw = data_loader.load_validation_data()
    data_loader.verify_data_integrity(val_raw, is_train=False)

    dec_raw = data_loader.load_december_data()

    # Preprocess validation set
    val_prep, _ = preprocessing.preprocess_data(val_raw, stats=stats)
    val_feat = features.extract_features(val_prep)

    # Preprocess December inputs dataset
    # Retrieve route reference coordinates and quote signal from training / validation sets
    train_raw = data_loader.load_train_data()
    lex_sample = train_raw[train_raw["pickup"] == "Lexington"].iloc[0]
    ftw_sample = train_raw[train_raw["delivery"] == "Fort Wayne"].iloc[0]

    dec_prep_df = dec_raw.copy()
    dec_prep_df["pickup_lat"] = lex_sample["pickup_lat"]
    dec_prep_df["pickup_lon"] = lex_sample["pickup_lon"]
    dec_prep_df["delivery_lat"] = ftw_sample["delivery_lat"]
    dec_prep_df["delivery_lon"] = ftw_sample["delivery_lon"]
    dec_prep_df["market_index"] = stats["market_index_median"]

    # Use average Lexington route quote signal
    lex_quote = train_raw[train_raw["pickup"] == "Lexington"]["quote_signal"].mean()
    dec_prep_df["quote_signal"] = lex_quote

    dec_prep, _ = preprocessing.preprocess_data(dec_prep_df, stats=stats)
    dec_feat = features.extract_features(dec_prep)

    feature_cols = features.get_feature_names()

    # Predict
    print("Generating validation predictions (12,000 loads)...")
    val_preds = ensemble.predict(val_feat[feature_cols], val_feat["base_signal"])
    val_df_out = pd.DataFrame({
        config.ID_COL: val_raw[config.ID_COL],
        "predicted_rate": np.round(val_preds, 2),
    })

    print("Generating December predictions (31 daily loads)...")
    dec_preds = ensemble.predict(dec_feat[feature_cols], dec_feat["base_signal"])
    dec_df_out = dec_raw.copy()
    dec_df_out["predicted_rate"] = np.round(dec_preds, 2)
    dec_df_out["date"] = pd.to_datetime(dec_df_out["date"]).dt.strftime("%Y-%m-%d")

    dec_cols = ["pickup", "delivery", "distance", "equipment", "weight", "date", "predicted_rate"]
    dec_df_out = dec_df_out[dec_cols]

    # Export CSVs to outputs and root/data paths
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    val_df_out.to_csv(config.VAL_PREDS_PATH, index=False)
    val_df_out.to_csv(config.BASE_DIR / "validation_predictions.csv", index=False)

    dec_df_out.to_csv(config.DECEMBER_PREDS_PATH, index=False)
    dec_df_out.to_csv(config.DECEMBER_INPUT_PATH, index=False)
    dec_df_out.to_csv(config.DATA_DIR / "december_chart_inputs.csv", index=False)

    print(f"Validation predictions saved: {config.VAL_PREDS_PATH}")
    print(f"December predictions saved: {config.DECEMBER_PREDS_PATH}")

    return val_df_out, dec_df_out
