from fastapi import APIRouter
from app.api.v1.routes import health, prediction, model, monitoring, models_mlops

# Prefixed Router (/api/v1)
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(prediction.router)
api_v1_router.include_router(model.router)
api_v1_router.include_router(monitoring.router)
api_v1_router.include_router(models_mlops.router)

# Root-level Router (fallback without prefix for max client compatibility)
root_api_router = APIRouter()
root_api_router.include_router(health.router)
root_api_router.include_router(prediction.router)
root_api_router.include_router(model.router)
root_api_router.include_router(monitoring.router)
root_api_router.include_router(models_mlops.router)
