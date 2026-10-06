from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db.models import ModelVersion, PredictionRequest, Prediction


class ModelVersionRepository:
    @staticmethod
    def get_by_version(db: Session, version: str) -> Optional[ModelVersion]:
        stmt = select(ModelVersion).where(ModelVersion.version == version)
        rec = db.scalars(stmt).first()
        if rec:
            return rec

        clean_v = version.replace("freight-rate-", "").lstrip("v")
        all_mv = db.scalars(select(ModelVersion)).all()
        for mv in all_mv:
            if mv.version.replace("freight-rate-", "").lstrip("v") == clean_v:
                return mv
        return None

    @staticmethod
    def get_active(db: Session) -> Optional[ModelVersion]:
        stmt = select(ModelVersion).where(ModelVersion.is_active.is_(True)).order_by(ModelVersion.id.desc())
        return db.scalars(stmt).first()

    @staticmethod
    def create_or_update_version(db: Session, metadata: Dict[str, Any]) -> ModelVersion:
        version = metadata.get("model_version", "unknown")
        existing = ModelVersionRepository.get_by_version(db, version)
        if existing:
            existing.model_type = metadata.get("model_type", "ResidualEnsemble")
            existing.target_strategy = metadata.get("target_strategy", "rate_minus_signal")
            existing.ensemble_weights = metadata.get("ensemble_weights")
            existing.validation_metrics = metadata.get("metrics")
            existing.training_period = metadata.get("training_period", "2025-01 to 2025-11")
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        mv = ModelVersion(
            version=version,
            model_type=metadata.get("model_type", "ResidualEnsemble"),
            target_strategy=metadata.get("target_strategy", "rate_minus_signal"),
            ensemble_weights=metadata.get("ensemble_weights"),
            validation_metrics=metadata.get("metrics"),
            training_period=metadata.get("training_period", "2025-01 to 2025-11"),
            is_active=True,
        )
        db.add(mv)
        db.commit()
        db.refresh(mv)
        return mv


class PredictionRepository:
    @staticmethod
    def create_prediction_request(
        db: Session,
        request_id: str,
        request_type: str,
        batch_size: int = 1,
        status: str = "COMPLETED"
    ) -> PredictionRequest:
        req = PredictionRequest(
            request_id=request_id,
            request_type=request_type,
            batch_size=batch_size,
            status=status,
            created_at=datetime.utcnow(),
        )
        db.add(req)
        return req

    @staticmethod
    def save_single_prediction(
        db: Session,
        request_id: str,
        pred_dict: Dict[str, Any],
        input_data: Optional[Dict[str, Any]] = None
    ) -> Prediction:
        # Create request tracking entry if missing
        req_stmt = select(PredictionRequest).where(PredictionRequest.request_id == request_id)
        if not db.scalars(req_stmt).first():
            PredictionRepository.create_prediction_request(db, request_id, request_type="single", batch_size=1)

        ci = pred_dict.get("confidence_interval")
        lower_val = ci.get("lower") if isinstance(ci, dict) else (ci.lower if ci else 0.0)
        upper_val = ci.get("upper") if isinstance(ci, dict) else (ci.upper if ci else 0.0)

        ts = pred_dict.get("prediction_timestamp")
        if isinstance(ts, str):
            try:
                parsed_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                parsed_ts = datetime.utcnow()
        else:
            parsed_ts = ts or datetime.utcnow()

        prediction = Prediction(
            request_id=request_id,
            load_id=pred_dict.get("load_id"),
            predicted_rate=pred_dict.get("predicted_rate"),
            rate_per_mile=pred_dict.get("rate_per_mile"),
            confidence_interval_lower=lower_val,
            confidence_interval_upper=upper_val,
            base_signal=pred_dict.get("base_signal"),
            residual=pred_dict.get("residual"),
            model_version=pred_dict.get("model_version"),
            prediction_timestamp=parsed_ts,
            input_data=input_data,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return prediction

    @staticmethod
    def save_batch_predictions(
        db: Session,
        request_id: str,
        predictions_data: List[Dict[str, Any]],
        inputs_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Prediction]:
        # Track batch request
        PredictionRepository.create_prediction_request(
            db, request_id=request_id, request_type="batch", batch_size=len(predictions_data)
        )

        objects = []
        for i, pred_dict in enumerate(predictions_data):
            ci = pred_dict.get("confidence_interval")
            lower_val = ci.get("lower") if isinstance(ci, dict) else (ci.lower if ci else 0.0)
            upper_val = ci.get("upper") if isinstance(ci, dict) else (ci.upper if ci else 0.0)

            ts = pred_dict.get("prediction_timestamp")
            if isinstance(ts, str):
                try:
                    parsed_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    parsed_ts = datetime.utcnow()
            else:
                parsed_ts = ts or datetime.utcnow()

            inp = inputs_data[i] if inputs_data and i < len(inputs_data) else None

            objects.append(
                Prediction(
                    request_id=request_id,
                    load_id=pred_dict.get("load_id"),
                    predicted_rate=pred_dict.get("predicted_rate"),
                    rate_per_mile=pred_dict.get("rate_per_mile"),
                    confidence_interval_lower=lower_val,
                    confidence_interval_upper=upper_val,
                    base_signal=pred_dict.get("base_signal"),
                    residual=pred_dict.get("residual"),
                    model_version=pred_dict.get("model_version"),
                    prediction_timestamp=parsed_ts,
                    input_data=inp,
                )
            )

        db.add_all(objects)
        db.commit()
        for obj in objects:
            db.refresh(obj)
        return objects

    @staticmethod
    def get_prediction_by_id(db: Session, prediction_id: int) -> Optional[Prediction]:
        stmt = select(Prediction).where(Prediction.id == prediction_id)
        return db.scalars(stmt).first()

    @staticmethod
    def list_predictions(
        db: Session,
        load_id: Optional[str] = None,
        model_version: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Prediction], int]:
        stmt = select(Prediction)
        count_stmt = select(func.count(Prediction.id))

        if load_id:
            stmt = stmt.where(Prediction.load_id == load_id)
            count_stmt = count_stmt.where(Prediction.load_id == load_id)

        if model_version:
            stmt = stmt.where(Prediction.model_version == model_version)
            count_stmt = count_stmt.where(Prediction.model_version == model_version)

        if start_date:
            stmt = stmt.where(Prediction.prediction_timestamp >= start_date)
            count_stmt = count_stmt.where(Prediction.prediction_timestamp >= start_date)

        if end_date:
            stmt = stmt.where(Prediction.prediction_timestamp <= end_date)
            count_stmt = count_stmt.where(Prediction.prediction_timestamp <= end_date)

        total_count = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Prediction.id.desc()).offset(offset).limit(limit)
        results = list(db.scalars(stmt).all())

        return results, total_count
