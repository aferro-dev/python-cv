from fastapi import APIRouter

from app.api.documents.create import create_document
from app.api.documents.delete import delete_document
from app.api.documents.list import list_documents
from app.api.documents.read import get_document
from app.schemas import DocumentRead

router = APIRouter()

router.add_api_route(
    "/api/v1/documents",
    create_document,
    methods=["POST"],
    response_model=DocumentRead,
    status_code=201,
    tags=["documents"],
)
router.add_api_route(
    "/api/v1/documents",
    list_documents,
    methods=["GET"],
    response_model=list[DocumentRead],
    tags=["documents"],
)
router.add_api_route(
    "/api/v1/documents/{document_id}",
    get_document,
    methods=["GET"],
    response_model=DocumentRead,
    tags=["documents"],
)
router.add_api_route(
    "/api/v1/documents/{document_id}",
    delete_document,
    methods=["DELETE"],
    status_code=204,
    tags=["documents"],
)
