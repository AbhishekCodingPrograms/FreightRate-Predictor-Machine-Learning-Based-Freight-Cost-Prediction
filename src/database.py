import os
from datetime import datetime
from typing import Generator, Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Environment variable for PostgreSQL or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./freight_rate.db")

# Convert postgres:// to postgresql:// if needed (Heroku/Render standard)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite engine configuration options
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Warning: Failed to connect to DATABASE_URL ({DATABASE_URL}), falling back to SQLite. Error: {e}")
    DATABASE_URL = "sqlite:///./freight_rate.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    load_id = Column(String(64), nullable=True, index=True)
    pickup = Column(String(128), nullable=False)
    delivery = Column(String(128), nullable=False)
    distance = Column(Float, nullable=False)
    equipment = Column(String(64), nullable=False)
    weight = Column(Float, nullable=False)
    date = Column(String(32), nullable=False)
    market_index = Column(Float, nullable=True)
    quote_signal = Column(Float, nullable=True)
    predicted_rate = Column(Float, nullable=False)
    base_signal = Column(Float, nullable=False)
    residual = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "load_id": self.load_id,
            "pickup": self.pickup,
            "delivery": self.delivery,
            "distance": self.distance,
            "equipment": self.equipment,
            "weight": self.weight,
            "date": self.date,
            "market_index": self.market_index,
            "quote_signal": self.quote_signal,
            "predicted_rate": self.predicted_rate,
            "base_signal": self.base_signal,
            "residual": self.residual,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(32), nullable=False)
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model_version": self.model_version,
            "rmse": self.rmse,
            "mae": self.mae,
            "mape": self.mape,
            "r2": self.r2,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
        }


def init_db():
    """Initializes database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_prediction(
    db: Session,
    pickup: str,
    delivery: str,
    distance: float,
    equipment: str,
    weight: float,
    date: str,
    predicted_rate: float,
    base_signal: float,
    residual: float,
    load_id: Optional[str] = None,
    market_index: Optional[float] = None,
    quote_signal: Optional[float] = None,
) -> PredictionLog:
    """Logs a prediction record into the database."""
    log_entry = PredictionLog(
        load_id=load_id,
        pickup=pickup,
        delivery=delivery,
        distance=distance,
        equipment=equipment,
        weight=weight,
        date=date,
        market_index=market_index,
        quote_signal=quote_signal,
        predicted_rate=predicted_rate,
        base_signal=base_signal,
        residual=residual,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_recent_predictions(db: Session, limit: int = 50) -> List[PredictionLog]:
    """Retrieves recent prediction logs."""
    return db.query(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(limit).all()
