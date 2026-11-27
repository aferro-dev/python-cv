from types import SimpleNamespace
from unittest.mock import AsyncMock

from pydantic import SecretStr

from app.config import Settings
from app.llm import OpenAILLM
from app.schemas import Source


async def test_openai_adapter_contract_without_network():
    settings = Settings(llm_provider="openai", openai_api_key=SecretStr("test-key"), _env_file=None)
    provider = OpenAILLM(settings)
    real_client = provider.client
    create = AsyncMock(return_value=SimpleNamespace(output_text="Risposta [1]"))
    close = AsyncMock()
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=create), close=close)
    try:
        source = Source(document_id="1", title="API", excerpt="FastAPI usa Pydantic", score=1)
        assert await provider.generate("Come?", [source], 64) == "Risposta [1]"
        arguments = create.call_args.kwargs
        assert arguments["store"] is False
        assert arguments["max_output_tokens"] == 64
        assert "[1] FastAPI usa Pydantic" in arguments["input"]
        await provider.close()
        close.assert_awaited_once()
    finally:
        await real_client.close()
