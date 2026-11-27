from fastapi import HTTPException
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, Session
from app.db import Document
from app.schemas import DocumentCreate


async def create_document(body: DocumentCreate, user: CurrentUser, db: Session):
    count = await db.scalar(
        select(func.count()).select_from(Document).where(Document.owner_id == user.id)
    )
    if (count or 0) >= 100:
        raise HTTPException(409, "Limite didattico: 100 documenti per utente")
    document = Document(owner_id=user.id, **body.model_dump())
    db.add(document)
    await db.commit()
    return document
