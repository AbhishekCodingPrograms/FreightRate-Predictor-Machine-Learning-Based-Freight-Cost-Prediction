import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment database before app imports
os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app
from app.db.database import Base, get_db_session
from app.db.models import Prediction, PredictionRequest
from app.db.repositories import PredictionRepository, ModelVersionRepository
from app.services.model_service import model_service

# Create in-memory SQLite engine for testing
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    """Create fresh tables for every test and isolate app dependency overrides."""
    app.dependency_overrides[get_db_session] = override_get_db_session
    Base.metadata.create_all(bind=test_engine)
    if not model_service.is_loaded:
        model_service.load_artifact()
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.pop(get_db_session, None)


client = TestClient(app)


def test_db_model_version_repository():
    session = TestingSessionLocal()
    mv_data = {
        "model_version": "freight-rate-v1.0.0",
        "model_type": "ResidualEnsemble",
        "target_strategy": "rate_minus_signal",
        "ensemble_weights": {"lgb": 0.35, "cat": 0.35, "xgb": 0.30},
        "metrics": {"mae": 105.2, "rmse": 152.4},
    }
    mv = ModelVersionRepository.create_or_update_version(session, mv_data)
    assert mv.id is not None
    assert mv.version == "freight-rate-v1.0.0"

    fetched = ModelVersionRepository.get_by_version(session, "freight-rate-v1.0.0")
    assert fetched is not None
    assert fetched.model_type == "ResidualEnsemble"
    session.close()


def test_single_prediction_persistence():
    payload = {
        "load_id": "TEST-DB-001",
        "pickup": "Lexington",
        "delivery": "Fort Wayne",
        "pickup_lat": 38.0464,
        "pickup_lon": -84.4970,
        "delivery_lat": 41.0793,
        "delivery_lon": -85.1394,
        "distance": 360.0,
        "equipment": "Dry Van",
        "weight": 32000.0,
        "date": "2025-12-15",
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["load_id"] == "TEST-DB-001"
    assert data["predicted_rate"] > 0
    assert data["request_id"] is not None
    assert data["id"] is not None

    # Verify directly in test DB
    session = TestingSessionLocal()
    record = session.query(Prediction).filter_by(id=data["id"]).first()
    assert record is not None
    assert record.load_id == "TEST-DB-001"
    assert record.predicted_rate == data["predicted_rate"]
    assert record.input_data["equipment"] == "Dry Van"
    session.close()


def test_batch_prediction_persistence():
    payload = {
        "loads": [
            {
                "load_id": "BATCH-001",
                "pickup": "Lexington",
                "delivery": "Fort Wayne",
                "pickup_lat": 38.0464,
                "pickup_lon": -84.4970,
                "delivery_lat": 41.0793,
                "delivery_lon": -85.1394,
                "distance": 360.0,
                "equipment": "Dry Van",
                "weight": 32000.0,
                "date": "2025-12-15",
            },
            {
                "load_id": "BATCH-002",
                "pickup": "Chicago",
                "delivery": "Detroit",
                "pickup_lat": 41.8781,
                "pickup_lon": -87.6298,
                "delivery_lat": 42.3314,
                "delivery_lon": -83.0458,
                "distance": 280.0,
                "equipment": "Reefer",
                "weight": 40000.0,
                "date": "2025-12-16",
            },
        ]
    }
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 2
    assert len(data["predictions"]) == 2
    req_id = data["predictions"][0]["request_id"]
    assert req_id == data["predictions"][1]["request_id"]

    session = TestingSessionLocal()
    records = session.query(Prediction).filter_by(request_id=req_id).all()
    assert len(records) == 2
    load_ids = [r.load_id for r in records]
    assert "BATCH-001" in load_ids
    assert "BATCH-002" in load_ids

    req_record = session.query(PredictionRequest).filter_by(request_id=req_id).first()
    assert req_record is not None
    assert req_record.request_type == "batch"
    assert req_record.batch_size == 2
    session.close()


def test_predictions_history_query_and_filtering():
    # Make two predictions
    p1 = {
        "load_id": "FILTER-001",
        "pickup": "Dallas",
        "delivery": "Houston",
        "pickup_lat": 32.7767,
        "pickup_lon": -96.7970,
        "delivery_lat": 29.7604,
        "delivery_lon": -95.3698,
        "distance": 240.0,
        "equipment": "Flatbed",
        "weight": 45000.0,
        "date": "2025-12-10",
    }
    p2 = {
        "load_id": "FILTER-002",
        "pickup": "Atlanta",
        "delivery": "Miami",
        "pickup_lat": 33.7490,
        "pickup_lon": -84.3880,
        "delivery_lat": 25.7617,
        "delivery_lon": -80.1918,
        "distance": 660.0,
        "equipment": "Dry Van",
        "weight": 25000.0,
        "date": "2025-12-12",
    }
    res1 = client.post("/api/v1/predict", json=p1)
    res2 = client.post("/api/v1/predict", json=p2)
    id1 = res1.json()["id"]

    # Query history with load_id filter
    history_res = client.get("/api/v1/predictions?load_id=FILTER-001")
    assert history_res.status_code == 200
    hdata = history_res.json()
    assert hdata["total"] == 1
    assert hdata["items"][0]["load_id"] == "FILTER-001"

    # Query single prediction lookup by ID
    single_res = client.get(f"/api/v1/predictions/{id1}")
    assert single_res.status_code == 200
    sdata = single_res.json()
    assert sdata["id"] == id1
    assert sdata["load_id"] == "FILTER-001"

    # Missing prediction lookup
    missing_res = client.get("/api/v1/predictions/999999")
    assert missing_res.status_code == 404
    assert "not found" in missing_res.json()["detail"].lower()


def test_pagination():
    # Insert multiple records
    session = TestingSessionLocal()
    for i in range(15):
        PredictionRepository.save_single_prediction(
            session,
            request_id=f"req-pag-{i}",
            pred_dict={
                "load_id": f"LOAD-{i}",
                "predicted_rate": 1000.0 + i,
                "rate_per_mile": 2.5,
                "confidence_interval": {"lower": 700.0, "upper": 1300.0},
                "base_signal": 900.0,
                "residual": 100.0 + i,
                "model_version": "freight-rate-v1.0.0",
                "prediction_timestamp": datetime.utcnow().isoformat(),
            }
        )
    session.close()

    res = client.get("/api/v1/predictions?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 15
    assert len(data["items"]) == 5
    assert data["limit"] == 5
    assert data["offset"] == 0

    res_page2 = client.get("/api/v1/predictions?limit=5&offset=5")
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) == 5
    assert data2["offset"] == 5


def test_health_and_readiness_with_db():
    health_res = client.get("/health")
    assert health_res.status_code == 200
    hdata = health_res.json()
    assert hdata["status"] == "healthy"
    assert hdata["model_loaded"] is True
    assert hdata["database_connected"] is True

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    rdata = ready_res.json()
    assert rdata["status"] == "ready"
    assert rdata["database_connected"] is True


def test_model_info_with_db_metadata():
    res = client.get("/api/v1/model/info")
    assert res.status_code == 200
    data = res.json()
    assert "database_metadata" in data
    assert data["database_metadata"]["version"] == data["model_version"]
