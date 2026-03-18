from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

from prompt_engine.config import AppConfig
from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.observability.metrics import MetricsRecorder
from prompt_engine.providers.base import BaseProvider


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(self, config: AppConfig, metrics: MetricsRecorder | None = None) -> None:
        super().__init__(config, metrics)

    def generate(self, request: CompletionRequest) -> CompletionResponse:
        started = time.perf_counter()
        text = self._build_mock_output(request)
        latency_ms = self._elapsed_ms(started)
        self._record_metrics("success", latency_ms)
        return CompletionResponse(
            provider=self.name,
            model=request.model,
            output_text=text,
            latency_ms=latency_ms,
            usage={"prompt_tokens": max(1, len(request.prompt.split())), "completion_tokens": max(1, len(text.split()))},
            raw_response={"mock": True},
        )

    async def agenerate(self, request: CompletionRequest) -> CompletionResponse:
        return self.generate(request)

    def stream(self, request: CompletionRequest) -> Iterator[str]:
        for chunk in self._chunk_text(self._build_mock_output(request), chunk_size=48):
            yield chunk

    async def astream(self, request: CompletionRequest) -> AsyncIterator[str]:
        for chunk in self.stream(request):
            yield chunk

    def _prepare_request(self, request: CompletionRequest) -> tuple[str, dict[str, str], dict[str, Any]]:
        return ("mock://local", {}, {})

    def _parse_response(
        self,
        payload: dict[str, Any],
        request: CompletionRequest,
        started: float,
    ) -> CompletionResponse:
        raise NotImplementedError("MockProvider bypasses HTTP parsing.")

    def _build_mock_output(self, request: CompletionRequest) -> str:
        if request.response_schema:
            return json.dumps(_mock_schema_payload(request.response_schema), indent=2)
        return "\n".join(
            [
                "MOCK_PROVIDER_RESPONSE",
                "Summary: The optimized prompt was received successfully.",
                f"Model: {request.model}",
                f"Prompt Preview: {request.prompt[:200]}",
            ]
        )


def _mock_schema_payload(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type", "object")
    if schema_type == "object":
        properties = schema.get("properties", {})
        return {key: _mock_schema_payload(value) for key, value in properties.items()}
    if schema_type == "array":
        item_schema = schema.get("items", {"type": "string"})
        return [_mock_schema_payload(item_schema)]
    if schema_type in {"number", "integer"}:
        return 0
    if schema_type == "boolean":
        return False
    return "mock-value"

