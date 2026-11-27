from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, User


async def owned_document(document_id: str, user: User, db: AsyncSession) -> Document:
    document = await db.scalar(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    if document is None:
        raise HTTPException(404, "Documento non trovato")
    return document
