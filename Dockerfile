FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
COPY inference ./inference
COPY main.py alembic.ini ./
COPY migrations ./migrations
RUN useradd --uid 10001 --create-home service && chown -R service:service /app
USER service
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
