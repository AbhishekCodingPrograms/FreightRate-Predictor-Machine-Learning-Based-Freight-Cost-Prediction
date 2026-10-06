"""
CLI Tool to safely roll back active production model version to an earlier version.
"""

import sys
from app.db.database import SessionLocal
from src.mlops.rollback import rollback_production_model

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/rollback_model.py <target_version>")
        sys.exit(1)

    version = sys.argv[1]
    print(f"Executing production model rollback to version: '{version}'...")

    db = SessionLocal()
    try:
        success, message, details = rollback_production_model(db, version, actor="operator")
        if success:
            print(f"✓ ROLLBACK SUCCESSFUL: {message}")
            print(f"Active Production Model is now: {details.get('version')}")
        else:
            print(f"✗ ROLLBACK FAILED: {message}")
            sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
