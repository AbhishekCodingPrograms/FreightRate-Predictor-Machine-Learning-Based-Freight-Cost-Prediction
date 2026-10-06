import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_service import model_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "freight-rate-predictor"
    assert "model_loaded" in data


def test_get_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_get_model_info(client):
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_version" in data
    assert "ensemble_weights" in data
    assert "feature_names" in data
    assert "metrics" in data


def test_single_prediction_valid(client):
    payload = {
        "load_id": "TE-000001",
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "market_index": 1.05,
        "quote_signal": 5.25,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["load_id"] == "TE-000001"
    assert data["predicted_rate"] > 0
    assert data["currency"] == "USD"
    assert "rate_per_mile" in data
    assert "confidence_interval" in data
    assert "X-Request-ID" in response.headers


def test_prediction_invalid_latitude(client):
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 150.0,  # Invalid > 90
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_prediction_invalid_longitude(client):
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -250.0,  # Invalid < -180
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_prediction_missing_required_field(client):
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        # missing distance
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_prediction_invalid_equipment(client):
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Hovercraft",  # Invalid
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_prediction_negative_distance(client):
    payload = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": -100.0,  # Invalid
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_batch_prediction_valid(client):
    load_item = {
        "load_id": "TE-000001",
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    payload = {"loads": [load_item, load_item]}
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["predictions"]) == 2


def test_batch_prediction_empty(client):
    payload = {"loads": []}
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 422


def test_batch_prediction_oversized(client):
    load_item = {
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15"
    }
    payload = {"loads": [load_item] * 1005}  # Exceeds max 1000
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "BATCH_SIZE_EXCEEDED"
