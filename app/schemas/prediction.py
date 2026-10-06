from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SinglePredictionRequest(BaseModel):
    load_id: Optional[str] = Field(None, json_schema_extra={"example": "TE-000001"}, description="Unique identifier for the load transaction")
    pickup: str = Field(..., json_schema_extra={"example": "Lexington"}, description="Pickup city or origin location")
    delivery: str = Field(..., json_schema_extra={"example": "Fort Wayne"}, description="Delivery city or destination location")
    pickup_lat: float = Field(..., ge=-90.0, le=90.0, json_schema_extra={"example": 38.0464}, description="Pickup latitude (-90 to 90)")
    pickup_lon: float = Field(..., ge=-180.0, le=180.0, json_schema_extra={"example": -84.4970}, description="Pickup longitude (-180 to 180)")
    delivery_lat: float = Field(..., ge=-90.0, le=90.0, json_schema_extra={"example": 41.0793}, description="Delivery latitude (-90 to 90)")
    delivery_lon: float = Field(..., ge=-180.0, le=180.0, json_schema_extra={"example": -85.1394}, description="Delivery longitude (-180 to 180)")
    distance: float = Field(..., gt=0.0, json_schema_extra={"example": 360.0}, description="Route distance in miles (must be > 0)")
    equipment: str = Field(..., json_schema_extra={"example": "Dry Van"}, description="Equipment type (Dry Van, Reefer, or Flatbed)")
    weight: float = Field(..., gt=0.0, json_schema_extra={"example": 32000.0}, description="Cargo weight in pounds (must be > 0)")
    market_index: Optional[float] = Field(None, gt=0.0, json_schema_extra={"example": 1.05}, description="Market index rate multiplier")
    quote_signal: Optional[float] = Field(None, gt=0.0, json_schema_extra={"example": 5.25}, description="Proprietary quote signal multiplier")
    date: str = Field(..., json_schema_extra={"example": "2025-12-15"}, description="Scheduled pickup date (YYYY-MM-DD)")

    @field_validator("equipment")
    @classmethod
    def validate_equipment(cls, v: str) -> str:
        allowed = {"Dry Van", "Reefer", "Flatbed"}
        if v not in allowed:
            raise ValueError(f"Invalid equipment '{v}'. Allowed types are: {sorted(allowed)}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{v}'. Date must be formatted as YYYY-MM-DD")
        return v


class BatchPredictionRequest(BaseModel):
    loads: List[SinglePredictionRequest] = Field(..., min_length=1, description="List of single prediction load requests")
