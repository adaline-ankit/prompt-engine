from __future__ import annotations

from typing import Any

from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1/responses"
    api_key_env = "OPENAI_API_KEY"

    def _prepare_request(self, request: CompletionRequest) -> tuple[str, dict[str, str], dict[str, Any]]:
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        payload: dict[str, Any] = {
            "model": request.model,
            "input": request.prompt,
            "temperature": request.temperature,
            "max_output_tokens": request.max_output_tokens,
        }
        if request.response_schema:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "prompt_engine_response",
                    "schema": request.response_schema,
                }
            }
        return self.base_url, headers, payload

    def _parse_response(
        self,
        payload: dict[str, Any],
        request: CompletionRequest,
        started: float,
    ) -> CompletionResponse:
        output_text = payload.get("output_text") or self._collect_output_text(payload)
        return CompletionResponse(
            provider=self.name,
            model=request.model,
            output_text=output_text,
            latency_ms=self._elapsed_ms(started),
            usage=payload.get("usage", {}),
            raw_response=payload,
        )

    def _collect_output_text(self, payload: dict[str, Any]) -> str:
        fragments: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                text = content.get("text") or content.get("value")
                if text:
                    fragments.append(text)
        return "\n".join(fragments)

