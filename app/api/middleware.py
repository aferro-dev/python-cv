"""Osservabilità HTTP; registro Prometheus isolato per ogni app."""

import time
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from prometheus_client import CollectorRegistry, Counter, Histogram

log = structlog.get_logger()


def configure_observability(app: FastAPI) -> None:
    registry = CollectorRegistry()
    app.state.metrics_registry = registry
    requests = Counter(
        "api_requests_total", "HTTP requests", ["method", "route", "status"], registry=registry
    )
    latency = Histogram("api_request_seconds", "HTTP latency", ["route"], registry=registry)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = str(uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", "unmatched")
        duration = time.perf_counter() - start
        requests.labels(request.method, route, str(response.status_code)).inc()
        latency.labels(route).observe(duration)
        response.headers["X-Request-ID"] = request_id
        log.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            route=route,
            status=response.status_code,
            duration=duration,
        )
        return response
