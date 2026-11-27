"""Bootstrap HTTP: configura l'applicazione e monta le rotte."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.lifespan import create_lifespan
from app.api.middleware import configure_observability
from app.api.routes import router
from app.config import Settings
from app.llm import LLM


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    config = settings or Settings()
    app = FastAPI(
        title="Python & LLM Knowledge API", version="0.2.0", lifespan=create_lifespan(config, llm)
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    configure_observability(app)
    app.include_router(router)
    return app
