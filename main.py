"""Entrypoint compatibile con `uvicorn main:app`."""

from app.api import create_app

app = create_app()
