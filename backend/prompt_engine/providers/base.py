from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx

from prompt_engine.config import AppConfig
from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.observability.metrics import MetricsRecorder
from prompt_engine.providers.exceptions import ProviderError


class BaseProvider(ABC):
    name = "base"
    base_url = ""
    api_key_env: str | None = None

    def __init__(self, config: AppConfig, metrics: MetricsRecorder | None = None) -> None:
        self.config = config
        self.metrics = metrics

    def generate(self, request: CompletionRequest) -> CompletionResponse:
        url, headers, payload = self._prepare_request(request)
        started = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(self.config.provider.max_retries + 1):
            try:
                with httpx.Client(timeout=self.config.provider.timeout_seconds) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                result = self._parse_response(response.json(), request, started)
                self._record_metrics("success", result.latency_ms)
                return result
            except Exception as exc:
                last_error = exc
                if attempt >= self.config.provider.max_retries:
                    self._record_metrics("error", self._elapsed_ms(started))
                    raise ProviderError(f"{self.name} request failed: {exc}") from exc
                time.sleep(0.5 * (2**attempt))

        raise ProviderError(f"{self.name} request failed: {last_error}")

    async def agenerate(self, request: CompletionRequest) -> CompletionResponse:
        url, headers, payload = self._prepare_request(request)
        started = time.perf_counter()
        last_error: Exception | None = None

        for attempt in range(self.config.provider.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.config.provider.timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                result = self._parse_response(response.json(), request, started)
                self._record_metrics("success", result.latency_ms)
                return result
            except Exception as exc:
                last_error = exc
                if attempt >= self.config.provider.max_retries:
                    self._record_metrics("error", self._elapsed_ms(started))
                    raise ProviderError(f"{self.name} request failed: {exc}") from exc
                await asyncio.sleep(0.5 * (2**attempt))

        raise ProviderError(f"{self.name} request failed: {last_error}")

    def stream(self, request: CompletionRequest) -> Iterator[str]:
        response = self.generate(request.model_copy(update={"stream": False}))
        yield from self._chunk_text(response.output_text)

    async def astream(self, request: CompletionRequest) -> AsyncIterator[str]:
        response = await self.agenerate(request.model_copy(update={"stream": False}))
        for chunk in self._chunk_text(response.output_text):
            yield chunk

    @abstractmethod
    def _prepare_request(self, request: CompletionRequest) -> tuple[str, dict[str, str], dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def _parse_response(
        self,
        payload: dict[str, Any],
        request: CompletionRequest,
        started: float,
    ) -> CompletionResponse:
        raise NotImplementedError

    def _auth_headers(self) -> dict[str, str]:
        if not self.api_key_env:
            return {}
        import os

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise ProviderError(f"Missing {self.api_key_env} for provider {self.name}")
        return {"Authorization": f"Bearer {api_key}"}

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    def _record_metrics(self, status: str, latency_ms: int) -> None:
        if self.metrics:
            self.metrics.record_provider_request(self.name, status, latency_ms / 1000)

    def _chunk_text(self, text: str, chunk_size: int = 80) -> Iterator[str]:
        for index in range(0, len(text), chunk_size):
            yield text[index : index + chunk_size]

