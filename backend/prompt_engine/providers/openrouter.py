from __future__ import annotations

from typing import Any

from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1/chat/completions"
    api_key_env = "OPENROUTER_API_KEY"

    def _prepare_request(self, request: CompletionRequest) -> tuple[str, dict[str, str], dict[str, Any]]:
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
        }
        return self.base_url, headers, payload

    def _parse_response(
        self,
        payload: dict[str, Any],
        request: CompletionRequest,
        started: float,
    ) -> CompletionResponse:
        message = payload.get("choices", [{}])[0].get("message", {})
        return CompletionResponse(
            provider=self.name,
            model=request.model,
            output_text=message.get("content", ""),
            latency_ms=self._elapsed_ms(started),
            usage=payload.get("usage", {}),
            raw_response=payload,
        )

