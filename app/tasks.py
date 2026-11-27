"""Entrypoint Celery sync -> asyncio.run -> risorse async locali a ogni esecuzione."""

import asyncio
import random

import structlog
from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from app.config import Settings
from app.db import Database, Job
from app.jobs import TERMINAL, transition
from app.llm import LLM, build_llm
from app.queue import create_celery
from app.rag import answer_question
from app.schemas import Question

celery_app = create_celery(Settings())
log = structlog.get_logger()
MAX_RETRIES = 3
TRANSIENT = (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError, TimeoutError)


async def execute_job(
    job_id: str, settings: Settings, retries: int, llm: LLM | None = None
) -> bool:
    """True richiede un retry Celery; False conclude o ignora un job terminale."""
    database = Database(settings.database_url)
    provider = None
    try:
        async with database.sessions() as db:
            job = await db.get(Job, job_id)
            if job is None or job.status in TERMINAL:
                return False
            body = Question.model_validate(job.payload)
            owner_id = job.owner_id
            if not await transition(db, job_id, "running", attempts=Job.attempts + 1, error=None):
                return False
            try:
                provider = llm or build_llm(settings)
                async with asyncio.timeout(settings.llm_timeout_seconds):
                    answer = await answer_question(
                        body, owner_id, db, provider, settings.llm_provider
                    )
                await transition(db, job_id, "succeeded", result=answer.model_dump(mode="json"))
                return False
            except TRANSIENT:
                if retries < MAX_RETRIES:
                    return await transition(
                        db, job_id, "retrying", error="Errore temporaneo del provider"
                    )
                await transition(db, job_id, "failed", error="Tentativi esauriti per il provider")
                return False
            except Exception:
                log.exception("job_failed", job_id=job_id)
                await transition(db, job_id, "failed", error="Elaborazione non riuscita")
                return False
    finally:
        if provider is not None:
            await provider.close()
        await database.engine.dispose()


@celery_app.task(bind=True, name="knowledge.answer", max_retries=MAX_RETRIES)
def answer_task(self, job_id: str):
    retry = asyncio.run(execute_job(job_id, Settings(), self.request.retries))
    if retry:
        # Backoff esponenziale e jitter: massimo quattro esecuzioni complessive.
        countdown = min(60, 2 ** (self.request.retries + 1)) + random.uniform(0, 1)
        raise self.retry(countdown=countdown)
