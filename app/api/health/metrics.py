from fastapi import Request, Response
from prometheus_client import generate_latest


async def metrics(request: Request):
    return Response(
        generate_latest(request.app.state.metrics_registry), media_type="text/plain; version=0.0.4"
    )
