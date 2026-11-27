"""Registro delle rotte, analogo ai routes.ts dei backend Node."""

from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.chat.routes import router as chat_router
from app.api.documents.routes import router as documents_router
from app.api.health.routes import router as health_router
from app.api.tasks.routes import router as tasks_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(documents_router)
router.include_router(tasks_router)
router.include_router(chat_router)
