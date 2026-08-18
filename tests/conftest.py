import os
import pytest
from fastapi.testclient import TestClient

# Set testing environment flag before importing app modules
os.environ["TESTING"] = "1"

from app.main import app
from app.database import init_db, reset_db


@pytest.fixture(autouse=True)
def setup_test_db():
    reset_db()
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

