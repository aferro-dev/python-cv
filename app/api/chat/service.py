"""Adattamento HTTP del servizio RAG: timeout, concorrenza e codici di errore."""

import asyncio

import structlog
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User
from app.rag import answer_question
from app.schemas import Answer, Question

log = structlog.get_logger()


async def answer(body: Question, request: Request, user: User, db: AsyncSession) -> Answer:
    config = request.app.state.settings
    try:
        async with asyncio.timeout(config.llm_timeout_seconds):
            async with request.app.state.slots:
                return await answer_question(
                    body, user.id, db, request.app.state.llm, config.llm_provider
                )
    except TimeoutError:
        raise HTTPException(504, "Timeout del provider LLM") from None
    except Exception:
        log.exception("llm_error")
        raise HTTPException(502, "Provider LLM non disponibile") from None
