"""
CLI Script to execute an offline monitoring run for Data Quality, Feature Drift, and Delayed Outcome Performance.
"""

import sys
from app.db.database import SessionLocal
from src.mlops.monitoring_service import MonitoringService

def main():
    print("=" * 60)
    print("FREIGHTRATE PREDICTOR - EXECUTING MONITORING RUN")
    print("=" * 60)

    db = SessionLocal()
    try:
        service = MonitoringService(db)
        res = service.run_monitoring_cycle(limit=1000)
        print(f"Run ID:              {res['run_id']}")
        print(f"Timestamp:           {res['timestamp']}")
        print(f"Predictions Checked: {res['prediction_count']}")
        print(f"Data Quality Status: {res['data_quality_status']}")
        print(f"Feature Drift Status:{res['drift_status']}")
        print(f"Performance Status:  {res['performance_status']}")
        print(f"Alert Count:         {res['alert_count']}")
        print("=" * 60)
    finally:
        db.close()

if __name__ == "__main__":
    main()
