from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ConfidenceInterval(BaseModel):
    lower: float = Field(..., description="Lower bound of 95% confidence interval")
    upper: float = Field(..., description="Upper bound of 95% confidence interval")


class SinglePredictionResponse(BaseModel):
    id: Optional[int] = Field(None, description="Database record primary key ID")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    load_id: Optional[str] = Field(None, description="Load ID if provided in request")
    predicted_rate: float = Field(..., description="Predicted total freight rate in USD")
    rate_per_mile: float = Field(..., description="Predicted freight rate per mile ($/mi)")
    currency: str = Field("USD", description="Currency unit")
    base_signal: float = Field(..., description="Baseline signal (distance * quote_signal)")
    residual: float = Field(..., description="ML model residual offset")
    confidence_interval: ConfidenceInterval = Field(..., description="95% prediction interval")
    model_version: str = Field(..., description="Trained model version")
    prediction_timestamp: str = Field(..., description="UTC timestamp of inference execution")


class BatchPredictionResponse(BaseModel):
    count: int = Field(..., description="Total records processed in batch")
    predictions: List[SinglePredictionResponse] = Field(..., description="Ordered list of prediction responses")


class PredictionDetailResponse(BaseModel):
    id: int = Field(..., description="Prediction record primary key ID")
    request_id: str = Field(..., description="Request tracking ID")
    load_id: Optional[str] = Field(None, description="Load ID if provided")
    predicted_rate: float = Field(..., description="Predicted spot rate")
    rate_per_mile: float = Field(..., description="Rate per mile")
    base_signal: Optional[float] = Field(None, description="Base signal value")
    residual: Optional[float] = Field(None, description="Residual offset value")
    confidence_interval: ConfidenceInterval = Field(..., description="95% confidence interval")
    model_version: str = Field(..., description="Model version string")
    prediction_timestamp: str = Field(..., description="Execution timestamp")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Sanitized request input payload")


class PredictionListResponse(BaseModel):
    total: int = Field(..., description="Total matching prediction records count")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Pagination offset")
    items: List[PredictionDetailResponse] = Field(..., description="List of stored predictions")


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Service health status")
    service: str = Field(..., description="Service name")
    model_loaded: bool = Field(..., description="Whether trained model artifact is loaded in memory")
    database_connected: bool = Field(..., description="Whether database connection is healthy")
    timestamp: str = Field(..., description="UTC server timestamp")


class ModelInfoResponse(BaseModel):
    model_version: str = Field(..., description="Model version")
    created_at: str = Field(..., description="Model training timestamp")
    random_seed: int = Field(..., description="Random seed used in training")
    target_strategy: str = Field(..., description="Target formulation used")
    ensemble_weights: Dict[str, float] = Field(..., description="Model ensemble weights")
    feature_count: int = Field(..., description="Number of engineered features")
    feature_names: List[str] = Field(..., description="List of feature column names")
    metrics: Dict[str, Any] = Field(..., description="Out-Of-Time validation metrics summary")
    database_metadata: Optional[Dict[str, Any]] = Field(None, description="Database model version metadata if available")
