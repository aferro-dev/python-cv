import asyncio
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings
from app.db import Database
from app.llm import DemoLLM
from app.tasks import execute_job


@pytest.fixture
def task_client(tmp_path, monkeypatch):
    settings = Settings(
        environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path}/jobs.db", _env_file=None
    )
    publish = Mock()
    monkeypatch.setattr("app.api.tasks.submit.publish_job", publish)
    with TestClient(create_app(settings)) as client:
        token = client.post(
            "/api/v1/auth/register", json={"username": "owner", "password": "owner-password"}
        ).json()
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        client.post(
            "/api/v1/documents",
            headers=headers,
            json={"title": "Python", "content": "Python usa asyncio per I/O concorrente."},
        )
        yield client, headers, settings, publish


def submit(client, headers):
    response = client.post("/api/v1/tasks", headers=headers, json={"question": "Python asyncio"})
    assert response.status_code == 202
    assert response.headers["location"].endswith(response.json()["id"])
    return response.json()["id"]


def test_task_success_and_redelivery(task_client):
    client, headers, settings, publish = task_client
    job_id = submit(client, headers)
    assert publish.call_args.args[1] == job_id
    assert client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()["status"] == "queued"
    assert asyncio.run(execute_job(job_id, settings, 0)) is False
    result = client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()
    assert result["status"] == "succeeded"
    assert result["attempts"] == 1
    assert result["result"]["sources"]
    # Una riconsegna successiva al completamento non chiama di nuovo il provider.
    assert asyncio.run(execute_job(job_id, settings, 0)) is False
    assert client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()["attempts"] == 1
    assert client.delete(f"/api/v1/tasks/{job_id}", headers=headers).json()["status"] == "succeeded"


def test_ownership_and_cancel_before_execution(task_client):
    client, headers, settings, _ = task_client
    job_id = submit(client, headers)
    token = client.post(
        "/api/v1/auth/register", json={"username": "other", "password": "other-password"}
    ).json()
    other = {"Authorization": f"Bearer {token['access_token']}"}
    assert client.get("/api/v1/tasks", headers=other).json() == []
    assert client.get(f"/api/v1/tasks/{job_id}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/tasks/{job_id}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/tasks/{job_id}", headers=headers).json()["status"] == "cancelled"
    assert asyncio.run(execute_job(job_id, settings, 0)) is False
    assert client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()["attempts"] == 0
    assert client.get("/api/v1/tasks?limit=1&offset=1", headers=headers).json() == []


class TimeoutLLM(DemoLLM):
    async def generate(self, *args):
        raise TimeoutError()


class BrokenLLM(DemoLLM):
    async def generate(self, *args):
        raise ValueError("private credentials")


def test_retry_exhaustion_and_permanent_failure(task_client):
    client, headers, settings, _ = task_client
    job_id = submit(client, headers)
    assert asyncio.run(execute_job(job_id, settings, 0, TimeoutLLM())) is True
    assert client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()["status"] == "retrying"
    assert asyncio.run(execute_job(job_id, settings, 3, TimeoutLLM())) is False
    assert client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()["status"] == "failed"
    other_id = submit(client, headers)
    assert asyncio.run(execute_job(other_id, settings, 0, BrokenLLM())) is False
    result = client.get(f"/api/v1/tasks/{other_id}", headers=headers).json()
    assert result["status"] == "failed"
    assert "private" not in str(result)


def test_publish_failure_is_persisted(task_client):
    client, headers, settings, publish = task_client
    publish.side_effect = ConnectionError("private broker details")
    response = client.post("/api/v1/tasks", headers=headers, json={"question": "Python"})
    assert response.status_code == 503
    assert "private" not in response.text
    jobs = client.get("/api/v1/tasks", headers=headers).json()
    assert jobs[0]["status"] == "failed"
    assert asyncio.run(execute_job(jobs[0]["id"], settings, 0)) is False


def test_cancel_during_generation_wins(task_client):
    client, headers, settings, _ = task_client
    job_id = submit(client, headers)

    class CancellingLLM(DemoLLM):
        async def generate(self, *args):
            from app.jobs import transition

            database = Database(settings.database_url)
            try:
                async with database.sessions() as db:
                    await transition(db, job_id, "cancelled")
            finally:
                await database.engine.dispose()
            return "Un risultato che non deve essere salvato"

    asyncio.run(execute_job(job_id, settings, 0, CancellingLLM()))
    result = client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()
    assert result["status"] == "cancelled"
    assert result["result"] is None


def test_celery_retry_schedules_backoff(monkeypatch):
    from celery.exceptions import Retry

    from app.tasks import answer_task

    execute = Mock(return_value=True)

    async def need_retry(*args):
        return execute(*args)

    monkeypatch.setattr("app.tasks.execute_job", need_retry)
    retry = Mock(side_effect=Retry())
    monkeypatch.setattr(answer_task, "retry", retry)
    with pytest.raises(Retry):
        answer_task.run("job-id")
    assert 2 <= retry.call_args.kwargs["countdown"] <= 3
