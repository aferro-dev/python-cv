from app.api.dependencies import CurrentUser, Session
from app.api.documents.service import owned_document


async def get_document(document_id: str, user: CurrentUser, db: Session):
    return await owned_document(document_id, user, db)
