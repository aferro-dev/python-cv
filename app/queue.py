"""Configurazione condivisa tra producer HTTP e worker Celery."""

from celery import Celery

from app.config import Settings


def create_celery(settings: Settings) -> Celery:
    queue = Celery("knowledge", broker=settings.celery_broker_url, include=["app.tasks"])
    queue.conf.update(
        task_default_queue="rag",
        task_serializer="json",
        accept_content=["json"],
        task_ignore_result=True,
        # Risultati e ownership sono nel DB: niente AsyncResult pubblico.
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        broker_connection_retry_on_startup=True,
        broker_connection_timeout=3,
        broker_transport_options={
            "visibility_timeout": 3600,
            "socket_timeout": 3,
            "socket_connect_timeout": 3,
        },
        task_publish_retry=False,
        timezone="UTC",
        enable_utc=True,
    )
    return queue


def publish_job(queue: Celery, job_id: str) -> None:
    # Solo un ID nel broker: niente password, token, prompt o documenti.
    queue.send_task("knowledge.answer", args=[job_id], task_id=job_id)
