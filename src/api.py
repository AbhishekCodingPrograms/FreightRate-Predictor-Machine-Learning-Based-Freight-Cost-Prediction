import io
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src import config, data_loader, preprocessing, features, models, artifact, database

from contextlib import asynccontextmanager

# Global variables for loaded model artifact
MODEL_ARTIFACT: Optional[Dict[str, Any]] = None



def get_loaded_artifact() -> Dict[str, Any]:
    global MODEL_ARTIFACT
    if MODEL_ARTIFACT is None:
        try:
            MODEL_ARTIFACT = artifact.load_model_artifact()
        except FileNotFoundError:
            print("Model artifact not found on startup. Training pipeline...")
            from src import train
            final_ensemble, stats, metrics = train.run_training_pipeline()
            MODEL_ARTIFACT = {
                "ensemble": final_ensemble,
                "stats": stats,
                "feature_names": features.get_feature_names(),
                "metrics": metrics,
            }
    assert MODEL_ARTIFACT is not None
    return MODEL_ARTIFACT



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model artifact on startup
    get_loaded_artifact()
    yield


# Initialize Database
database.init_db()

app = FastAPI(
    title="Spotter Freight Rate Predictor API",
    description="Machine Learning-based Spot Freight Rate Prediction Engine powered by LightGBM, CatBoost & XGBoost Ensemble",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request / Response Schemas
class PredictionInput(BaseModel):
    pickup: str = Field(..., json_schema_extra={"example": "Lexington"})
    delivery: str = Field(..., json_schema_extra={"example": "Fort Wayne"})
    distance: float = Field(..., gt=0, json_schema_extra={"example": 360.0})
    equipment: str = Field(..., json_schema_extra={"example": "Dry Van"})
    weight: float = Field(..., gt=0, json_schema_extra={"example": 32000.0})
    date: str = Field(..., json_schema_extra={"example": "2025-12-15"})
    market_index: Optional[float] = Field(None, json_schema_extra={"example": 1.05})
    quote_signal: Optional[float] = Field(None, json_schema_extra={"example": 5.25})
    pickup_lat: Optional[float] = Field(None, json_schema_extra={"example": 38.0464})
    pickup_lon: Optional[float] = Field(None, json_schema_extra={"example": -84.4970})
    delivery_lat: Optional[float] = Field(None, json_schema_extra={"example": 41.0793})
    delivery_lon: Optional[float] = Field(None, json_schema_extra={"example": -85.1394})



class PredictionResponse(BaseModel):
    predicted_rate: float
    rate_per_mile: float
    base_signal: float
    residual: float
    confidence_interval: Dict[str, float]
    inputs: Dict[str, Any]
    logged_id: Optional[int] = None


@app.get("/health")
def health_check():
    art = get_loaded_artifact()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": art.get("model_version", "1.0.0"),
        "model_loaded": art.get("ensemble") is not None,
        "database": database.DATABASE_URL.split("://")[0],
    }


@app.get("/api/v1/model/metrics")
def get_model_metrics():
    art = get_loaded_artifact()
    ensemble: models.FreightRateEnsemble = art["ensemble"]
    feature_names = art["feature_names"]
    importances = ensemble.get_feature_importances(feature_names).to_dict(orient="records")

    return {
        "metrics": art.get("metrics", {}),
        "ensemble_weights": ensemble.weights,
        "feature_importances": importances,
    }


@app.post("/api/v1/predict", response_model=PredictionResponse)
def predict_single_load(
    input_data: PredictionInput,
    db: Session = Depends(database.get_db)
):
    art = get_loaded_artifact()
    ensemble: models.FreightRateEnsemble = art["ensemble"]
    stats: dict = art["stats"]

    # Provide default coordinates and quote_signal if missing
    pickup_lat = input_data.pickup_lat or 38.0464
    pickup_lon = input_data.pickup_lon or -84.4970
    delivery_lat = input_data.delivery_lat or 41.0793
    delivery_lon = input_data.delivery_lon or -85.1394
    market_index = input_data.market_index if input_data.market_index is not None else stats["market_index_median"]
    quote_signal = input_data.quote_signal if input_data.quote_signal is not None else 5.25

    row = {
        "pickup": input_data.pickup,
        "delivery": input_data.delivery,
        "pickup_lat": pickup_lat,
        "pickup_lon": pickup_lon,
        "delivery_lat": delivery_lat,
        "delivery_lon": delivery_lon,
        "distance": input_data.distance,
        "equipment": input_data.equipment,
        "weight": input_data.weight,
        "date": input_data.date,
        "market_index": market_index,
        "quote_signal": quote_signal,
    }

    df_single = pd.DataFrame([row])
    df_prep, _ = preprocessing.preprocess_data(df_single, stats=stats)
    df_feat = features.extract_features(df_prep)
    feature_cols = art["feature_names"]

    pred_rate = float(ensemble.predict(df_feat[feature_cols], df_feat["base_signal"])[0])
    pred_rate = round(pred_rate, 2)
    base_sig = round(float(df_feat["base_signal"].iloc[0]), 2)
    res_val = round(pred_rate - base_sig, 2)
    rate_per_mile = round(pred_rate / max(input_data.distance, 1e-5), 2)

    # 95% Confidence Interval based on validation residual std (~$150)
    std_err = 150.0
    ci_lower = round(max(10.0, pred_rate - 1.96 * std_err), 2)
    ci_upper = round(pred_rate + 1.96 * std_err, 2)

    # Save prediction to DB log
    log_entry = database.log_prediction(
        db=db,
        pickup=input_data.pickup,
        delivery=input_data.delivery,
        distance=input_data.distance,
        equipment=input_data.equipment,
        weight=input_data.weight,
        date=input_data.date,
        predicted_rate=pred_rate,
        base_signal=base_sig,
        residual=res_val,
        market_index=market_index,
        quote_signal=quote_signal,
    )

    return PredictionResponse(
        predicted_rate=pred_rate,
        rate_per_mile=rate_per_mile,
        base_signal=base_sig,
        residual=res_val,
        confidence_interval={"lower": ci_lower, "upper": ci_upper},
        inputs=row,
        logged_id=log_entry.id,
    )


@app.get("/api/v1/december-forecast")
def get_december_forecast():
    art = get_loaded_artifact()
    ensemble: models.FreightRateEnsemble = art["ensemble"]
    stats: dict = art["stats"]

    dec_raw = data_loader.load_december_data()
    # Preprocess
    train_raw = data_loader.load_train_data()
    lex_sample = train_raw[train_raw["pickup"] == "Lexington"].iloc[0]
    ftw_sample = train_raw[train_raw["delivery"] == "Fort Wayne"].iloc[0]
    lex_quote = float(train_raw[train_raw["pickup"] == "Lexington"]["quote_signal"].mean())

    dec_prep_df = dec_raw.copy()
    dec_prep_df["pickup_lat"] = lex_sample["pickup_lat"]
    dec_prep_df["pickup_lon"] = lex_sample["pickup_lon"]
    dec_prep_df["delivery_lat"] = ftw_sample["delivery_lat"]
    dec_prep_df["delivery_lon"] = ftw_sample["delivery_lon"]
    dec_prep_df["market_index"] = stats["market_index_median"]
    dec_prep_df["quote_signal"] = lex_quote

    dec_prep, _ = preprocessing.preprocess_data(dec_prep_df, stats=stats)
    dec_feat = features.extract_features(dec_prep)

    feature_cols = art["feature_names"]
    preds = ensemble.predict(dec_feat[feature_cols], dec_feat["base_signal"])

    result = []
    for i in range(len(dec_raw)):
        d = dec_raw.iloc[i]
        rate = round(float(preds[i]), 2)
        result.append({
            "date": pd.to_datetime(d["date"]).strftime("%Y-%m-%d"),
            "pickup": d["pickup"],
            "delivery": d["delivery"],
            "distance": float(d["distance"]),
            "equipment": d["equipment"],
            "weight": float(d["weight"]),
            "predicted_rate": rate,
            "rate_per_mile": round(rate / float(d["distance"]), 2),
        })

    rates = [r["predicted_rate"] for r in result]
    summary = {
        "min_rate": min(rates),
        "max_rate": max(rates),
        "avg_rate": round(float(np.mean(rates)), 2),
        "total_days": len(rates),
    }

    return {"forecast": result, "summary": summary}


@app.get("/api/v1/history")
def get_history(limit: int = 50, db: Session = Depends(database.get_db)):
    logs = database.get_recent_predictions(db, limit=limit)
    return [log.to_dict() for log in logs]


@app.post("/api/v1/predict/batch")
async def batch_predict(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")


    content = await file.read()
    df_raw = pd.read_csv(io.BytesIO(content))

    required_cols = ["pickup", "delivery", "distance", "equipment", "weight", "date"]
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {missing}")

    art = get_loaded_artifact()
    ensemble: models.FreightRateEnsemble = art["ensemble"]
    stats: dict = art["stats"]

    df = df_raw.copy()
    if "pickup_lat" not in df.columns: df["pickup_lat"] = 38.0464
    if "pickup_lon" not in df.columns: df["pickup_lon"] = -84.4970
    if "delivery_lat" not in df.columns: df["delivery_lat"] = 41.0793
    if "delivery_lon" not in df.columns: df["delivery_lon"] = -85.1394
    if "market_index" not in df.columns: df["market_index"] = stats["market_index_median"]
    if "quote_signal" not in df.columns: df["quote_signal"] = 5.25

    df["date"] = pd.to_datetime(df["date"])
    df_prep, _ = preprocessing.preprocess_data(df, stats=stats)
    df_feat = features.extract_features(df_prep)

    preds = ensemble.predict(df_feat[art["feature_names"]], df_feat["base_signal"])

    df_out = df_raw.copy()
    df_out["predicted_rate"] = np.round(preds, 2)
    df_out["rate_per_mile"] = np.round(preds / np.maximum(df_raw["distance"].values, 1e-5), 2)

    return JSONResponse(content=df_out.to_dict(orient="records"))


# Mount frontend static directory if exists
frontend_dir = config.BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def read_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
        return "Spotter Freight Rate Predictor API is running."
