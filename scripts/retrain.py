"""
CLI Tool to execute model retraining and candidate model registration.
"""

import sys
from app.db.database import SessionLocal
from src.mlops.retrain import run_retraining_pipeline

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"Starting model retraining pipeline (Candidate Tag: {tag or 'auto'})...")

    db = SessionLocal()
    try:
        res = run_retraining_pipeline(db, new_version_tag=tag)
        print("✓ Retraining Complete!")
        print(f"Candidate Version: {res['model_version']}")
        print(f"Artifact Path:     {res['artifact_path']}")
        print(f"Validation RMSE:   ${res['validation_metrics']['rmse']:.2f}")
        print(f"Validation MAPE:   {res['validation_metrics']['mape']:.2f}%")
        print("Note: Candidate model registered in status 'candidate'. It will NOT deploy until promoted.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
