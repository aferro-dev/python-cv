"""Servizio condiviso tra richiesta HTTP e worker: nessuna dipendenza da FastAPI."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document
from app.llm import LLM
from app.retrieval import retrieve
from app.schemas import Answer, Question


async def answer_question(
    body: Question, owner_id: str, db: AsyncSession, llm: LLM, provider: str
) -> Answer:
    documents = list(await db.scalars(select(Document).where(Document.owner_id == owner_id)))
    sources = await asyncio.to_thread(retrieve, documents, body.question, body.top_k)
    if not sources:
        return Answer(
            answer="Non ho trovato fonti pertinenti nella tua knowledge base.",
            sources=[],
            provider=provider,
        )
    result = await llm.generate(body.question, sources, body.max_output_tokens)
    return Answer(answer=result, sources=sources, provider=provider)
