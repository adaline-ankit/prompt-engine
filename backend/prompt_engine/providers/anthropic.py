from __future__ import annotations

from typing import Any

from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    base_url = "https://api.anthropic.com/v1/messages"
    api_key_env = "ANTHROPIC_API_KEY"

    def _prepare_request(self, request: CompletionRequest) -> tuple[str, dict[str, str], dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self._auth_headers()["Authorization"].split(" ", 1)[1],
        }
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        return self.base_url, headers, payload

    def _parse_response(
        self,
        payload: dict[str, Any],
        request: CompletionRequest,
        started: float,
    ) -> CompletionResponse:
        text_blocks = [item.get("text", "") for item in payload.get("content", []) if item.get("type") == "text"]
        return CompletionResponse(
            provider=self.name,
            model=request.model,
            output_text="\n".join(block for block in text_blocks if block),
            latency_ms=self._elapsed_ms(started),
            usage=payload.get("usage", {}),
            raw_response=payload,
        )

