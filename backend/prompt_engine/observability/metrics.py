from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


_OPTIMIZATION_COUNTER = Counter(
    "prompt_engine_optimizations_total",
    "Total number of optimization requests.",
    ["intent", "status"],
)
_OPTIMIZATION_LATENCY = Histogram(
    "prompt_engine_optimization_latency_seconds",
    "Latency for prompt optimization requests.",
    ["intent"],
)
_PROVIDER_COUNTER = Counter(
    "prompt_engine_provider_requests_total",
    "Total number of provider execution requests.",
    ["provider", "status"],
)
_PROVIDER_LATENCY = Histogram(
    "prompt_engine_provider_latency_seconds",
    "Latency for provider execution requests.",
    ["provider"],
)


class MetricsRecorder:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def record_optimization(self, intent: str, status: str, latency_seconds: float) -> None:
        if not self.enabled:
            return
        _OPTIMIZATION_COUNTER.labels(intent=intent, status=status).inc()
        _OPTIMIZATION_LATENCY.labels(intent=intent).observe(latency_seconds)

    def record_provider_request(self, provider: str, status: str, latency_seconds: float) -> None:
        if not self.enabled:
            return
        _PROVIDER_COUNTER.labels(provider=provider, status=status).inc()
        _PROVIDER_LATENCY.labels(provider=provider).observe(latency_seconds)

    def render(self) -> tuple[bytes, str]:
        return generate_latest(), CONTENT_TYPE_LATEST

