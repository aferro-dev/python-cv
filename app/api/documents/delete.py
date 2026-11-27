from app.api.dependencies import CurrentUser, Session
from app.api.documents.service import owned_document


async def delete_document(document_id: str, user: CurrentUser, db: Session):
    await db.delete(await owned_document(document_id, user, db))
    await db.commit()
