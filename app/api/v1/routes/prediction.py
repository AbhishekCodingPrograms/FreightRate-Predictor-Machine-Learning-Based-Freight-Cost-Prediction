from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.prediction import SinglePredictionRequest, BatchPredictionRequest
from app.schemas.response import (
    SinglePredictionResponse,
    BatchPredictionResponse,
    PredictionListResponse,
    PredictionDetailResponse,
    ConfidenceInterval,
)
from app.services.prediction_service import PredictionService
from app.dependencies import get_prediction_service, get_db_session
from app.db.repositories import PredictionRepository

import numpy as np
import pandas as pd
from app.services.model_service import ModelService
from app.dependencies import get_model_service
from src import data_loader, preprocessing, features

router = APIRouter(tags=["Predictions"])


@router.post(
    "/predict",
    response_model=SinglePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Freight Rate (Single Load)",
    description="Calculates spot freight rate prediction, rate per mile, base signal, ML residual offset, and 95% confidence interval."
)
def predict_single(
    request: SinglePredictionRequest,
    pred_svc: PredictionService = Depends(get_prediction_service),
    db: Session = Depends(get_db_session)
) -> SinglePredictionResponse:
    return pred_svc.predict_single(request, db=db)


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Freight Rate (Batch Loads)",
    description="Processes batch freight rate predictions efficiently for up to 1,000 load records preserving load IDs and order."
)
def predict_batch(
    request: BatchPredictionRequest,
    pred_svc: PredictionService = Depends(get_prediction_service),
    db: Session = Depends(get_db_session)
) -> BatchPredictionResponse:
    return pred_svc.predict_batch(request, db=db)


@router.get(
    "/predictions",
    response_model=PredictionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Prediction History",
    description="Retrieves persistent prediction history filtered by load_id, model_version, and date range with bounded pagination."
)
@router.get(
    "/history",
    response_model=PredictionListResponse,
    include_in_schema=False
)
def list_predictions(
    load_id: Optional[str] = Query(None, description="Filter by unique load transaction ID"),
    model_version: Optional[str] = Query(None, description="Filter by model version string"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD or ISO datetime)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD or ISO datetime)"),
    limit: int = Query(50, ge=1, le=100, description="Page size limit (1 to 100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db_session)
) -> PredictionListResponse:
    parsed_start = None
    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD or ISO format.")

    parsed_end = None
    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD or ISO format.")

    records, total_count = PredictionRepository.list_predictions(
        db,
        load_id=load_id,
        model_version=model_version,
        start_date=parsed_start,
        end_date=parsed_end,
        limit=limit,
        offset=offset
    )

    items = []
    for rec in records:
        items.append(
            PredictionDetailResponse(
                id=rec.id,
                request_id=rec.request_id,
                load_id=rec.load_id,
                predicted_rate=rec.predicted_rate,
                rate_per_mile=rec.rate_per_mile,
                base_signal=rec.base_signal,
                residual=rec.residual,
                confidence_interval=ConfidenceInterval(
                    lower=rec.confidence_interval_lower,
                    upper=rec.confidence_interval_upper,
                ),
                model_version=rec.model_version,
                prediction_timestamp=rec.prediction_timestamp.isoformat() if rec.prediction_timestamp else "",
                input_data=rec.input_data,
            )
        )

    return PredictionListResponse(
        total=total_count,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Prediction By ID",
    description="Retrieves a single persisted prediction record by its primary key ID."
)
def get_prediction_by_id(
    prediction_id: int,
    db: Session = Depends(get_db_session)
) -> PredictionDetailResponse:
    rec = PredictionRepository.get_prediction_by_id(db, prediction_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction record with ID '{prediction_id}' not found."
        )

    return PredictionDetailResponse(
        id=rec.id,
        request_id=rec.request_id,
        load_id=rec.load_id,
        predicted_rate=rec.predicted_rate,
        rate_per_mile=rec.rate_per_mile,
        base_signal=rec.base_signal,
        residual=rec.residual,
        confidence_interval=ConfidenceInterval(
            lower=rec.confidence_interval_lower,
            upper=rec.confidence_interval_upper,
        ),
        model_version=rec.model_version,
        prediction_timestamp=rec.prediction_timestamp.isoformat() if rec.prediction_timestamp else "",
        input_data=rec.input_data,
    )


@router.get(
    "/december-forecast",
    summary="Get December 31-Day Assessment Forecast",
    description="Generates daily spot rate predictions for the 31 December assessment load schedule."
)
def get_december_forecast(
    model_svc: ModelService = Depends(get_model_service)
):
    model_svc._ensure_loaded()
    ensemble = model_svc.get_ensemble()
    stats = model_svc.get_stats()
    feature_cols = model_svc.get_feature_names()

    dec_raw = data_loader.load_december_data()
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
            "rate_per_mile": round(rate / max(float(d["distance"]), 0.1), 2),
        })

    rates = [r["predicted_rate"] for r in result]
    summary = {
        "min_rate": min(rates) if rates else 0.0,
        "max_rate": max(rates) if rates else 0.0,
        "avg_rate": round(float(np.mean(rates)), 2) if rates else 0.0,
        "total_days": len(rates),
    }

    return {"forecast": result, "summary": summary}

