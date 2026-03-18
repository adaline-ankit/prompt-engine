from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from prompt_engine.config import AppConfig
from prompt_engine.models import CompletionRequest, CompletionResponse
from prompt_engine.observability.metrics import MetricsRecorder
from prompt_engine.providers.anthropic import AnthropicProvider
from prompt_engine.providers.base import BaseProvider
from prompt_engine.providers.exceptions import ProviderError
from prompt_engine.providers.mock import MockProvider
from prompt_engine.providers.openai import OpenAIProvider
from prompt_engine.providers.openrouter import OpenRouterProvider


class ProviderRouter:
    def __init__(self, config: AppConfig, metrics: MetricsRecorder | None = None) -> None:
        self.config = config
        self.metrics = metrics
        self._providers: dict[str, BaseProvider] = {}
        self._provider_classes = {
            "mock": MockProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "openrouter": OpenRouterProvider,
        }

    def get(self, provider_name: str | None = None) -> BaseProvider:
        name = provider_name or self.config.provider.default_provider
        if name not in self._provider_classes:
            raise ProviderError(f"Unsupported provider: {name}")
        if name not in self._providers:
            self._providers[name] = self._provider_classes[name](self.config, self.metrics)
        return self._providers[name]

    def generate(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> CompletionResponse:
        last_error: Exception | None = None
        for name in self._provider_order(provider_name, fallback_providers):
            try:
                return self.get(name).generate(request)
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"All providers failed: {last_error}")

    async def agenerate(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> CompletionResponse:
        last_error: Exception | None = None
        for name in self._provider_order(provider_name, fallback_providers):
            try:
                return await self.get(name).agenerate(request)
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"All providers failed: {last_error}")

    def stream(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> Iterator[str]:
        last_error: Exception | None = None
        for name in self._provider_order(provider_name, fallback_providers):
            try:
                yield from self.get(name).stream(request)
                return
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"All providers failed: {last_error}")

    async def astream(
        self,
        request: CompletionRequest,
        provider_name: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> AsyncIterator[str]:
        last_error: Exception | None = None
        for name in self._provider_order(provider_name, fallback_providers):
            try:
                async for chunk in self.get(name).astream(request):
                    yield chunk
                return
            except Exception as exc:
                last_error = exc
        raise ProviderError(f"All providers failed: {last_error}")

    def _provider_order(
        self,
        provider_name: str | None,
        fallback_providers: list[str] | None,
    ) -> list[str]:
        names = [provider_name or self.config.provider.default_provider]
        names.extend(fallback_providers or self.config.provider.fallback_providers)
        ordered: list[str] = []
        for name in names:
            if name and name not in ordered:
                ordered.append(name)
        return ordered
