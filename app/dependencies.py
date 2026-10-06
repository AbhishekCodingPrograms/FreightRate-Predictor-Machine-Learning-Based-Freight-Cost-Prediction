from app.services.model_service import model_service, ModelService
from app.services.prediction_service import prediction_service, PredictionService
from app.db.database import get_db_session

get_db = get_db_session


def get_model_service() -> ModelService:
    return model_service


def get_prediction_service() -> PredictionService:
    return prediction_service


__all__ = ["get_model_service", "get_prediction_service", "get_db_session", "get_db"]
