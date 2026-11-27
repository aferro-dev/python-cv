import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path}/test.db", _env_file=None
    )
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def auth(client):
    response = client.post(
        "/api/v1/auth/register", json={"username": "andrea", "password": "study-password-123"}
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
