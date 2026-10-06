import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd  # type: ignore  # pyrefly: ignore
from sqlalchemy.orm import Session

from app.services.model_service import model_service
from app.schemas.prediction import SinglePredictionRequest, BatchPredictionRequest
from app.schemas.response import SinglePredictionResponse, BatchPredictionResponse, ConfidenceInterval
from app.core.exceptions import PredictionError, BatchSizeExceededError
from app.config import settings
from app.db.repositories import PredictionRepository
from app.core.logging import logger
from src import preprocessing, features, models


class PredictionService:
    """Inference service leveraging pre-loaded artifact with optional DB persistence."""

    def predict_single(
        self,
        request: SinglePredictionRequest,
        db: Optional[Session] = None,
        request_id: Optional[str] = None
    ) -> SinglePredictionResponse:
        """Executes single load rate prediction and persists result if DB session provided."""
        req_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
        ensemble = model_service.get_ensemble()
        stats = model_service.get_stats()
        feature_cols = model_service.get_feature_names()

        row = {
            "pickup": request.pickup,
            "delivery": request.delivery,
            "pickup_lat": request.pickup_lat,
            "pickup_lon": request.pickup_lon,
            "delivery_lat": request.delivery_lat,
            "delivery_lon": request.delivery_lon,
            "distance": request.distance,
            "equipment": request.equipment,
            "weight": request.weight,
            "date": request.date,
            "market_index": request.market_index if request.market_index is not None else stats["market_index_median"],
            "quote_signal": request.quote_signal if request.quote_signal is not None else stats["quote_signal_median"],
        }

        try:
            df_single = pd.DataFrame([row])
            df_prep, _ = preprocessing.preprocess_data(df_single, stats=stats)
            df_feat = features.extract_features(df_prep)

            preds = ensemble.predict(df_feat[feature_cols], df_feat["base_signal"])
            pred_rate = round(float(preds[0]), 2)
            base_sig = round(float(df_feat["base_signal"].iloc[0]), 2)
            res_val = round(pred_rate - base_sig, 2)
            rate_per_mile = round(pred_rate / max(request.distance, 0.1), 2)

            std_err = 150.0
            ci_lower = round(max(10.0, pred_rate - 1.96 * std_err), 2)
            ci_upper = round(pred_rate + 1.96 * std_err, 2)

            model_version = model_service.get_model_version()
            ts = datetime.utcnow().isoformat()

            response_data = SinglePredictionResponse(
                id=None,
                request_id=req_id,
                load_id=request.load_id,
                predicted_rate=pred_rate,
                rate_per_mile=rate_per_mile,
                currency="USD",
                base_signal=base_sig,
                residual=res_val,
                confidence_interval=ConfidenceInterval(lower=ci_lower, upper=ci_upper),
                model_version=model_version,
                prediction_timestamp=ts,
            )

            if db is not None:
                try:
                    db_record = PredictionRepository.save_single_prediction(
                        db,
                        request_id=req_id,
                        pred_dict=response_data.model_dump(),
                        input_data=row,
                    )
                    response_data.id = db_record.id
                except Exception as db_exc:
                    logger.error(f"Database persistence failed for single prediction {req_id}: {db_exc}")
                    raise PredictionError(f"Database persistence failed: {db_exc}")

            return response_data

        except PredictionError:
            raise
        except Exception as exc:
            raise PredictionError(f"Single prediction calculation failed: {exc}")

    def predict_batch(
        self,
        request: BatchPredictionRequest,
        db: Optional[Session] = None,
        request_id: Optional[str] = None
    ) -> BatchPredictionResponse:
        """Executes high-throughput batch rate prediction with single DB transaction bulk insert."""
        if len(request.loads) > settings.MAX_BATCH_SIZE:
            raise BatchSizeExceededError(max_size=settings.MAX_BATCH_SIZE, actual_size=len(request.loads))

        req_id = request_id or f"batch-{uuid.uuid4().hex[:12]}"
        ensemble = model_service.get_ensemble()
        stats = model_service.get_stats()
        feature_cols = model_service.get_feature_names()

        rows = []
        for req in request.loads:
            rows.append({
                "pickup": req.pickup,
                "delivery": req.delivery,
                "pickup_lat": req.pickup_lat,
                "pickup_lon": req.pickup_lon,
                "delivery_lat": req.delivery_lat,
                "delivery_lon": req.delivery_lon,
                "distance": req.distance,
                "equipment": req.equipment,
                "weight": req.weight,
                "date": req.date,
                "market_index": req.market_index if req.market_index is not None else stats["market_index_median"],
                "quote_signal": req.quote_signal if req.quote_signal is not None else stats["quote_signal_median"],
            })

        try:
            df_batch = pd.DataFrame(rows)
            df_prep, _ = preprocessing.preprocess_data(df_batch, stats=stats)
            df_feat = features.extract_features(df_prep)

            preds = ensemble.predict(df_feat[feature_cols], df_feat["base_signal"])
            base_sigs = df_feat["base_signal"].values
            distances = df_batch["distance"].values

            responses: List[SinglePredictionResponse] = []
            pred_dicts_to_save: List[Dict[str, Any]] = []
            std_err = 150.0
            timestamp = datetime.utcnow().isoformat()
            version = model_service.get_model_version()

            for i, req in enumerate(request.loads):
                pred_rate = round(float(preds[i]), 2)
                base_sig = round(float(base_sigs[i]), 2)
                res_val = round(pred_rate - base_sig, 2)
                rpm = round(pred_rate / max(float(distances[i]), 0.1), 2)
                ci_lower = round(max(10.0, pred_rate - 1.96 * std_err), 2)
                ci_upper = round(pred_rate + 1.96 * std_err, 2)

                resp = SinglePredictionResponse(
                    id=None,
                    request_id=req_id,
                    load_id=req.load_id,
                    predicted_rate=pred_rate,
                    rate_per_mile=rpm,
                    currency="USD",
                    base_signal=base_sig,
                    residual=res_val,
                    confidence_interval=ConfidenceInterval(lower=ci_lower, upper=ci_upper),
                    model_version=version,
                    prediction_timestamp=timestamp,
                )
                responses.append(resp)
                pred_dicts_to_save.append(resp.model_dump())

            if db is not None:
                try:
                    db_records = PredictionRepository.save_batch_predictions(
                        db,
                        request_id=req_id,
                        predictions_data=pred_dicts_to_save,
                        inputs_data=rows,
                    )
                    for i, record in enumerate(db_records):
                        responses[i].id = record.id
                except Exception as db_exc:
                    logger.error(f"Database persistence failed for batch prediction {req_id}: {db_exc}")
                    raise PredictionError(f"Batch database persistence failed: {db_exc}")

            return BatchPredictionResponse(
                count=len(responses),
                predictions=responses,
            )
        except BatchSizeExceededError:
            raise
        except PredictionError:
            raise
        except Exception as exc:
            raise PredictionError(f"Batch prediction calculation failed: {exc}")


prediction_service = PredictionService()
