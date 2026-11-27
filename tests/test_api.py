import asyncio

import jwt
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


def test_health_and_validation(client, auth):
    assert client.get("/health/ready").status_code == 200
    assert client.get("/api/v1/documents").status_code == 401
    assert (
        client.post(
            "/api/v1/documents", headers=auth, json={"title": " ", "content": "x"}
        ).status_code
        == 422
    )
    assert (
        client.post("/api/v1/chat", headers=auth, json={"question": "x", "top_k": 99}).status_code
        == 422
    )
    assert "api_requests_total" in client.get("/metrics").text
    assert client.get("/").headers["x-request-id"]


def test_auth(client, auth):
    body = {"username": "andrea", "password": "study-password-123"}
    assert client.post("/api/v1/auth/register", json=body).status_code == 409
    assert client.post("/api/v1/auth/token", json=body).status_code == 200
    body["password"] = "wrong-password"
    assert client.post("/api/v1/auth/token", json=body).status_code == 401
    token = jwt.encode({"sub": "x", "exp": 1}, "invalid" * 8, algorithm="HS256")
    assert (
        client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )


def test_document_isolation_rag_and_delete(client, auth):
    created = client.post(
        "/api/v1/documents",
        headers=auth,
        json={"title": "FastAPI", "content": "FastAPI usa Pydantic per validare i dati."},
    )
    assert created.status_code == 201
    document_id = created.json()["id"]
    other = client.post(
        "/api/v1/auth/register", json={"username": "other", "password": "other-password"}
    ).json()
    other_auth = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get("/api/v1/documents", headers=other_auth).json() == []
    assert client.get(f"/api/v1/documents/{document_id}", headers=other_auth).status_code == 404
    assert client.delete(f"/api/v1/documents/{document_id}", headers=other_auth).status_code == 404
    empty = client.post("/api/v1/chat", headers=other_auth, json={"question": "FastAPI"}).json()
    assert empty["sources"] == []
    result = client.post("/api/v1/chat", headers=auth, json={"question": "FastAPI Pydantic"})
    assert result.status_code == 200
    assert result.json()["sources"][0]["document_id"] == document_id
    assert "[1]" in result.json()["answer"]
    streamed = client.post("/api/v1/chat/stream", headers=auth, json={"question": "FastAPI"})
    assert "event: sources" in streamed.text
    assert "event: delta" in streamed.text
    assert "event: done" in streamed.text
    assert client.get("/api/v1/documents?limit=1&offset=1", headers=auth).json() == []
    assert client.delete(f"/api/v1/documents/{document_id}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/documents/{document_id}", headers=auth).status_code == 404


class BrokenLLM:
    async def generate(self, *args):
        raise RuntimeError("private provider details")

    async def close(self):
        pass


class SlowLLM(BrokenLLM):
    async def generate(self, *args):
        await asyncio.sleep(1)
        return "too late"


def test_provider_errors(tmp_path):
    for provider, expected in [(BrokenLLM(), 502), (SlowLLM(), 504)]:
        settings = Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path}/{expected}.db",
            llm_timeout_seconds=0.01,
            _env_file=None,
        )
        with TestClient(create_app(settings, provider)) as client:
            token = client.post(
                "/api/v1/auth/register", json={"username": "test", "password": "password-123"}
            ).json()
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            client.post(
                "/api/v1/documents",
                headers=headers,
                json={"title": "Python", "content": "Python async"},
            )
            response = client.post("/api/v1/chat", headers=headers, json={"question": "Python"})
            assert response.status_code == expected
            assert "private" not in response.text
