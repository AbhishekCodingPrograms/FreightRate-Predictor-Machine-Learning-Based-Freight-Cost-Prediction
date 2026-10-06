import os
import sys
from pathlib import Path

# Add workspace root to sys.path so 'src' and 'app' can be imported in tests
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Configure test database URL before importing app database modules
if "TEST_DATABASE_URL" not in os.environ:
    os.environ["TEST_DATABASE_URL"] = "sqlite:///./freight_test.db"

import pytest
from app.db.database import engine, Base


@pytest.fixture(autouse=True, scope="session")
def initialize_test_db():
    """Ensure database schema is created for test session."""
    Base.metadata.create_all(bind=engine)
    yield
