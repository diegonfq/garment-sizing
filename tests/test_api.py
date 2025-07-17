import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from src.main import app
from src.core.domain.models import Base
from src.api.v1.dependencies import get_db

# Create a temporary, in-memory SQLite database just for testing.
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the in-memory database
Base.metadata.create_all(bind=engine)

# Create a new dependency that uses the temporary test database instead of the real one.
def override_get_db() -> Generator:
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# We tell our FastAPI app to use this new dependency for all tests.
app.dependency_overrides[get_db] = override_get_db

# Create a TestClient, which is like a browser that can send requests to the app.
# It will be created once for the entire test session.
@pytest.fixture(scope="session")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

def create_garment(client: TestClient):
    """
    Tests that we can successfully create a new garment via the POST endpoint.
    """
    garment_data = {
        "garment_type": "jeans",
        "base_size": "M",
        "measurements": {"Waist": 80.0, "Inseam": 82.0},
        "deltas": {"Waist": {"XS": -5.0, "S": -2.5, "M": 0.0, "L": 2.5, "XL": 5.0}}
    }

    response = client.post("/api/v1/garments/", json=garment_data)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["garment_type"] == "jeans"
    assert response_data["base_size"] == "M"
    assert "id" in response_data

def create_duplicate(client: TestClient):
    """
    Tests that the API correctly prevents creating a garment with a duplicate type.
    """
    duplicate_garment_data = {
        "garment_type": "jeans",  # This type already exists
        "base_size": "S",
        "measurements": {"Waist": 78.0},
        "deltas": {"Waist": {"XS": -2.5, "S": 0.0, "M": 2.5, "L": 5.0, "XL": 7.5}}
    }

    response = client.post("/api/v1/garments/", json=duplicate_garment_data)
    assert response.status_code == 409

def garment_list(client: TestClient):
    """
    Tests that we can retrieve a list of all garments.
    """

    response = client.get("/api/v1/garments/")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) > 0
    assert response_data[0]["garment_type"] == "jeans"
