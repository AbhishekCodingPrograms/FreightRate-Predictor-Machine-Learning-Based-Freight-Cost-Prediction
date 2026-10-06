import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, PredictionLog, log_prediction, get_recent_predictions


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_log_prediction(db_session):
    entry = log_prediction(
        db=db_session,
        pickup="Lexington",
        delivery="Fort Wayne",
        distance=360.0,
        equipment="Dry Van",
        weight=32000.0,
        date="2025-12-15",
        predicted_rate=2045.50,
        base_signal=1890.00,
        residual=155.50,
    )

    assert entry.id is not None
    assert entry.predicted_rate == 2045.50

    logs = get_recent_predictions(db_session, limit=10)
    assert len(logs) == 1
    assert logs[0].pickup == "Lexington"
