from fastapi import APIRouter
from app.api.v1.routes import health, prediction, model, monitoring, models_mlops

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(prediction.router)
api_v1_router.include_router(model.router)
api_v1_router.include_router(monitoring.router)
api_v1_router.include_router(models_mlops.router)
