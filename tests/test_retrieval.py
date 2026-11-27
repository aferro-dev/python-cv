import pytest
from pydantic import ValidationError

from app.config import Settings
from app.db import Document
from app.retrieval import retrieve


def test_bm25_relevance_and_empty():
    docs = [
        Document(id="1", title="API", content="FastAPI Pydantic validazione " * 100),
        Document(id="2", title="Cucina", content="pasta pomodoro"),
    ]
    hits = retrieve(docs, "FASTAPI", 2)
    assert len(hits) == 2
    assert all(hit.document_id == "1" for hit in hits)
    assert all(len(hit.excerpt) <= 1000 for hit in hits)
    assert retrieve(docs, "astronave", 3) == []
    assert retrieve([], "Python", 3) == []


def test_production_config_requires_secrets_and_migrations():
    with pytest.raises(ValidationError):
        Settings(environment="production", _env_file=None)
    with pytest.raises(ValidationError):
        Settings(llm_provider="openai", openai_api_key=None, _env_file=None)
