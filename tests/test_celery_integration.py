"""Test opt-in: richiede un Redis dedicato indicato da TEST_REDIS_URL."""

import os
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.config import Settings


@pytest.mark.skipif(
    not os.getenv("TEST_REDIS_URL"), reason="Set TEST_REDIS_URL to a dedicated Redis"
)
def test_real_broker_and_worker(tmp_path):
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path}/integration.db",
        celery_broker_url=os.environ["TEST_REDIS_URL"],
        llm_provider="demo",
        _env_file=None,
    )
    environment = {
        **os.environ,
        "DATABASE_URL": settings.database_url,
        "CELERY_BROKER_URL": settings.celery_broker_url,
        "ENVIRONMENT": "test",
        "LLM_PROVIDER": "demo",
    }
    with TestClient(create_app(settings)) as client:
        token = client.post(
            "/api/v1/auth/register",
            json={"username": "integration", "password": "integration-password"},
        ).json()
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        client.post(
            "/api/v1/documents",
            headers=headers,
            json={"title": "Celery", "content": "Celery usa Redis come broker per i task."},
        )
        log_path = tmp_path / "worker.log"
        with log_path.open("w+") as logfile:
            worker = subprocess.Popen(
                [
                    ".venv/bin/celery",
                    "-A",
                    "app.tasks:celery_app",
                    "worker",
                    "--pool=solo",
                    "--concurrency=1",
                    "--loglevel=info",
                    "--without-gossip",
                    "--without-mingle",
                    "--without-heartbeat",
                    "-Q",
                    "rag",
                ],
                env=environment,
                stdout=logfile,
                stderr=subprocess.STDOUT,
            )
            try:
                submitted = client.post(
                    "/api/v1/tasks", headers=headers, json={"question": "Celery Redis"}
                )
                assert submitted.status_code == 202, submitted.text
                job_id = submitted.json()["id"]
                deadline = time.monotonic() + 25
                result = {}
                while time.monotonic() < deadline:
                    result = client.get(f"/api/v1/tasks/{job_id}", headers=headers).json()
                    if result["status"] in ("succeeded", "failed") or worker.poll() is not None:
                        break
                    time.sleep(0.1)
                logfile.flush()
                assert result["status"] == "succeeded", log_path.read_text()
                assert result["attempts"] == 1
                assert result["result"]["sources"][0]["title"] == "Celery"
            finally:
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=5)
