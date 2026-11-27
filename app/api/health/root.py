from fastapi import Request


async def root(request: Request):
    return {
        "service": "knowledge-api",
        "docs": "/docs",
        "provider": request.app.state.settings.llm_provider,
    }
