"""
CLI Tool to ingest delayed actual posted rates into PostgreSQL for true model evaluation.
"""

import sys
import pandas as pd
from app.db.database import SessionLocal
from app.db.models import PredictionOutcome

def ingest_outcomes(csv_path: str):
    print(f"Ingesting delayed actual posted rates from: {csv_path}")
    df = pd.read_csv(csv_path)

    if "load_id" not in df.columns or "posted_rate" not in df.columns:
        print("CSV must contain 'load_id' and 'posted_rate' columns.")
        sys.exit(1)

    db = SessionLocal()
    count = 0
    try:
        for _, row in df.iterrows():
            lid = str(row["load_id"]).trim() if hasattr(str(row["load_id"]), "trim") else str(row["load_id"]).strip()
            rate = float(row["posted_rate"])

            existing = db.query(PredictionOutcome).filter(PredictionOutcome.load_id == lid).first()
            if not existing:
                rec = PredictionOutcome(load_id=lid, actual_posted_rate=rate)
                db.add(rec)
                count += 1

        db.commit()
        print(f"✓ Successfully ingested {count} new actual outcomes into PostgreSQL.")
    finally:
        db.close()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/validation.csv"
    ingest_outcomes(path)
