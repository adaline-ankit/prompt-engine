from __future__ import annotations

from contextlib import contextmanager, nullcontext
from typing import Any

from opentelemetry import trace


@contextmanager
def traced_span(name: str, attributes: dict[str, Any] | None = None, enabled: bool = True):
    if not enabled:
        with nullcontext() as span:
            yield span
        return

    tracer = trace.get_tracer("prompt_engine")
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            if value is None:
                continue
            span.set_attribute(key, value if isinstance(value, (bool, int, float, str)) else str(value))
        yield span

