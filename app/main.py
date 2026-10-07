from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import logger
from app.core.middleware import RequestTracingMiddleware
from app.core.exceptions import APIError, api_error_handler, generic_exception_handler
from app.services.model_service import model_service
from app.db.database import engine, Base, check_db_connected, get_db_url
from app.db import models  # Ensures ORM models register on Base.metadata
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing model artifact loading and database connectivity on startup."""
    logger.info("Initializing FastAPI Application...")
    try:
        model_service.load_artifact()
        logger.info("Model service initialized successfully.")
    except Exception as exc:
        logger.critical(f"FATAL: Model artifact failed to load on startup: {exc}. Server will start in degraded state.")

    # Non-destructive table check for SQLite/local dev/test fallback
    current_url = get_db_url()
    if current_url.startswith("sqlite"):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("SQLite local tables verified/created non-destructively.")
        except Exception as exc:
            logger.warning(f"Could not verify SQLite tables: {exc}")

    if check_db_connected():
        logger.info("Database connection verified successfully.")
        try:
            from app.db.database import SessionLocal
            from src.mlops.registry import ModelRegistry
            db_sess = SessionLocal()
            try:
                registry = ModelRegistry(db_sess)
                registry.ensure_production_registered(model_service.metadata)
                logger.info("Production model version registry synced successfully.")
            finally:
                db_sess.close()
        except Exception as exc:
            logger.warning(f"Could not sync model registry: {exc}")
    else:
        logger.warning("Database connection is currently unavailable. Operating in degraded state.")

    yield
    logger.info("Shutting down FastAPI Application.")


app = FastAPI(
    title="Spotter Freight Rate Predictor REST API",
    description="Production-grade Machine Learning spot freight cost prediction engine powered by LightGBM, CatBoost & XGBoost Ensemble.",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & Latency Middleware
app.add_middleware(RequestTracingMiddleware)

# Custom Exception Handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register Router (both root and /api/v1 prefix for frontend compatibility)
app.include_router(api_v1_router)
app.include_router(api_v1_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
