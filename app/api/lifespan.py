"""Risorse condivise per la durata dell'applicazione."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.db import Database
from app.llm import LLM, build_llm
from app.queue import create_celery
from app.security import passwords


def create_lifespan(config: Settings, llm: LLM | None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = config
        app.state.db = Database(config.database_url)
        app.state.llm = llm or build_llm(config)
        app.state.queue = create_celery(config)
        app.state.slots = asyncio.Semaphore(config.llm_concurrency)
        app.state.dummy_password_hash = passwords.hash("dummy-password-never-used")
        try:
            if config.auto_create_tables:
                await app.state.db.create_tables()
            yield
        finally:
            await app.state.llm.close()
            await app.state.db.engine.dispose()
            app.state.queue.close()

    return lifespan
