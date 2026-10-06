"""
CLI Tool to promote a candidate model version to active production after validation gate checks.
"""

import sys
from app.db.database import SessionLocal
from src.mlops.promotion import promote_candidate_model

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/promote_model.py <model_version> [--force]")
        sys.exit(1)

    version = sys.argv[1]
    force = "--force" in sys.argv

    print(f"Promoting candidate model version: '{version}' (Force: {force})...")
    db = SessionLocal()
    try:
        success, message, details = promote_candidate_model(db, version, actor="admin", force=force)
        if success:
            print(f"✓ PROMOTION SUCCESSFUL: {message}")
            print(f"Active Production Model is now: {details.get('version')}")
        else:
            print(f"✗ PROMOTION REJECTED: {message}")
            sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
