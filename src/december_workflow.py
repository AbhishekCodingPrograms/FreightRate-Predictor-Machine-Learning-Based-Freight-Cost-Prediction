import pandas as pd  # type: ignore  # pyrefly: ignore
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from src import config, data_loader, preprocessing, features, models


def process_december_assessment_forecast(
    ensemble: models.FreightRateEnsemble,
    stats: Dict[str, Any],
    feature_cols: list,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Isolated assessment workflow for 31-day December forecast generation.
    
    Reads input from data/december-chart-inputs.csv (IMMUTABLE).
    Writes output exclusively to outputs/december_predictions.csv.
    """
    dec_raw = data_loader.load_december_data()

    # Retrieve route reference coordinates and quote signal from training stats/reference data
    train_raw = data_loader.load_train_data()
    lex_rows = train_raw[train_raw["pickup"] == "Lexington"]
    ftw_rows = train_raw[train_raw["delivery"] == "Fort Wayne"]

    lex_lat = float(lex_rows["pickup_lat"].iloc[0]) if len(lex_rows) > 0 else stats.get("pickup_lat_median", 38.0464)
    lex_lon = float(lex_rows["pickup_lon"].iloc[0]) if len(lex_rows) > 0 else stats.get("pickup_lon_median", -84.4970)
    ftw_lat = float(ftw_rows["delivery_lat"].iloc[0]) if len(ftw_rows) > 0 else stats.get("delivery_lat_median", 41.0793)
    ftw_lon = float(ftw_rows["delivery_lon"].iloc[0]) if len(ftw_rows) > 0 else stats.get("delivery_lon_median", -85.1394)
    lex_quote = float(lex_rows["quote_signal"].mean()) if len(lex_rows) > 0 else stats.get("quote_signal_mean", 5.25)

    dec_prep_df = dec_raw.copy()
    dec_prep_df["pickup_lat"] = lex_lat
    dec_prep_df["pickup_lon"] = lex_lon
    dec_prep_df["delivery_lat"] = ftw_lat
    dec_prep_df["delivery_lon"] = ftw_lon
    dec_prep_df["market_index"] = stats.get("market_index_median", 1.0)
    dec_prep_df["quote_signal"] = lex_quote

    dec_prep, _ = preprocessing.preprocess_data(dec_prep_df, stats=stats)
    dec_feat = features.extract_features(dec_prep)

    preds = ensemble.predict(dec_feat[feature_cols], dec_feat["base_signal"])

    dec_df_out = dec_raw.copy()
    dec_df_out["predicted_rate"] = np.round(preds, 2)
    dec_df_out["date"] = pd.to_datetime(dec_df_out["date"]).dt.strftime("%Y-%m-%d")

    dec_cols = ["pickup", "delivery", "distance", "equipment", "weight", "date", "predicted_rate"]
    dec_df_out = dec_df_out[dec_cols]

    # Save ONLY to outputs/december_predictions.csv (NEVER overwrite data/december-chart-inputs.csv)
    save_path = output_path or config.DECEMBER_PREDS_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    dec_df_out.to_csv(save_path, index=False)

    return dec_df_out
