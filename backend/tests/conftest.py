import pytest
import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import MagicMock

from app.main import app
from app.api.deps import get_db, get_current_user, get_ingestion_coordinator
from app.models.user import User, RepoAccess
from app.models.enums import RepoRole
from app.services.ingestion.coordinator import IngestionCoordinator

# 1. Setup In-Memory DB (SQLite)
# "check_same_thread=False" is required for SQLite in multithreaded test environments
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 2. Strict UUID for the Mock User (Fixes your 403 error)
MOCK_USER_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a new database session for a test.
    Rolls back transaction after test is complete.
    """
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def mock_get_current_user():
    """Bypasses JWT validation and returns a fixed superuser."""
    return User(
        id=MOCK_USER_ID,
        email="test@codesense.ai",
        external_id="auth0|test-user",
        full_name="Test Engineer",
        is_active=True
    )

class MockExecutor:
    """Fake executor that does nothing, so we don't hit Celery/Redis."""
    def submit(self, run_id):
        pass 

def mock_get_coordinator(db: Session = None):
    return IngestionCoordinator(db, MockExecutor())

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    TestClient with all external dependencies mocked.
    """
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_ingestion_coordinator] = lambda: mock_get_coordinator(session)
    
    # Ensure the Mock User exists in the DB so relationships (like RepoAccess) work
    user = mock_get_current_user()
    session.add(user)
    session.commit()

    yield TestClient(app)
    
    app.dependency_overrides.clear()