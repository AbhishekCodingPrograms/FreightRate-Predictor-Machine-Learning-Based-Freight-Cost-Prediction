import pytest
from fastapi.testclient import TestClient
from src.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data


def test_predict_endpoint():
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15",
        "market_index": 1.0,
        "quote_signal": 5.25,
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_rate" in data
    assert data["predicted_rate"] > 0
    assert "rate_per_mile" in data
    assert "base_signal" in data
    assert "confidence_interval" in data


def test_december_forecast_endpoint():
    response = client.get("/api/v1/december-forecast")
    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data
    assert len(data["forecast"]) == 31
    assert "summary" in data


def test_model_metrics_endpoint():
    response = client.get("/api/v1/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "feature_importances" in data
    assert "ensemble_weights" in data
