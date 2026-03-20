from __future__ import annotations

import hashlib
import json
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

from prompt_engine.cache import TTLCache
from prompt_engine.config import AppConfig, load_config
from prompt_engine.core import PromptCompiler, PromptDecomposer, PromptRefiner
from prompt_engine.diffing import build_prompt_diff
from prompt_engine.engine.detector import HybridIntentDetector
from prompt_engine.models import CompletionRequest, OptimizedPrompt, PromptState, RunResponse, TransformationStep
from prompt_engine.observability.metrics import MetricsRecorder
from prompt_engine.observability.tracing import traced_span
from prompt_engine.pipeline import OptimizationPipeline
from prompt_engine.providers.factory import ProviderRouter
from prompt_engine.scoring import compute_optimization_score, estimate_tokens
from prompt_engine.security import mask_pii, sanitize_text
from prompt_engine.skills.registry import SkillRegistry


class PromptOptimizationEngine:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self.metrics = MetricsRecorder(self.config.observability.enable_metrics)
        self.detector = HybridIntentDetector()
        self.decomposer = PromptDecomposer()
        self.refiner = PromptRefiner()
        self.compiler = PromptCompiler(max_chars=self.config.output.max_prompt_chars)
        self.registry = SkillRegistry(self.config)
        self.pipeline = OptimizationPipeline(self.registry)
        self.providers = ProviderRouter(self.config, self.metrics)
        self.cache = (
            TTLCache(
                ttl_seconds=self.config.cache.ttl_seconds,
                max_entries=self.config.cache.max_entries,
            )
            if self.config.cache.enabled
            else None
        )

    def optimize(self, prompt: str, context: dict[str, Any] | None = None) -> OptimizedPrompt:
        return self.optimize_prompt(prompt, context)

    def optimize_prompt(self, input_prompt: str, context: dict[str, Any] | None = None) -> OptimizedPrompt:
        started = time.perf_counter()
        context = dict(context or {})
        working_prompt = sanitize_text(input_prompt)
        if self.config.security.pii_masking:
            working_prompt = mask_pii(working_prompt)

        cache_key = self._cache_key(working_prompt, context)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.metrics.record_optimization(cached.intent, "cache_hit", 0.0)
                return cached

        with traced_span(
            "prompt_engine.optimize",
            {"environment": self.config.environment},
            enabled=self.config.observability.enable_tracing,
        ):
            intent_prediction = self.detector.detect(working_prompt, context)
            decomposition = self.decomposer.decompose(working_prompt, context)
            state = PromptState(
                base_prompt=working_prompt,
                sanitized_prompt=working_prompt,
                intent=intent_prediction.intent,
                goal=decomposition.goal,
                constraints=list(decomposition.constraints),
                expected_output=list(decomposition.expected_output),
                missing_info=list(decomposition.missing_info),
                metadata={
                    "context": context,
                    "intent_prediction": intent_prediction.model_dump(),
                },
            )
            state.transformations.extend(
                [
                    TransformationStep(
                        name="intent_detection",
                        kind="analysis",
                        description=f"Detected intent as {intent_prediction.intent}.",
                        after=intent_prediction.intent,
                        metadata=intent_prediction.model_dump(),
                    ),
                    TransformationStep(
                        name="prompt_decomposition",
                        kind="analysis",
                        description="Extracted goal, constraints, expected output, and missing information.",
                        after=decomposition.goal,
                        metadata=decomposition.model_dump(),
                    ),
                ]
            )

            if context.get("output_schema"):
                state.output_format = {
                    "type": "json_schema",
                    "schema": context["output_schema"],
                }

            examples = context.get("examples")
            if isinstance(examples, list):
                state.examples.extend(str(example) for example in examples)
            elif examples:
                state.examples.append(str(examples))

            state = self.refiner.refine(state, context)
            state.instructions.extend(self._default_instructions(state.intent, context))
            state, skills_applied = self.pipeline.run(state, context)
            final_prompt = self.compiler.compile(state)

        score = compute_optimization_score(state, final_prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        result = OptimizedPrompt(
            original_prompt=working_prompt,
            final_prompt=final_prompt,
            intent=state.intent,
            skills_applied=skills_applied,
            transformations=state.transformations,
            metadata={
                **state.metadata,
                "decomposition": decomposition.model_dump(),
            },
            optimization_score=score,
            prompt_diff=build_prompt_diff(working_prompt, final_prompt),
            token_estimate=estimate_tokens(final_prompt),
            latency_ms=latency_ms,
        )

        if self.cache:
            self.cache.set(cache_key, result)

        self.metrics.record_optimization(result.intent, "success", latency_ms / 1000)
        return result

    def optimize_and_run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> RunResponse:
        optimized = self.optimize_prompt(prompt, context)
        request = self._build_completion_request(optimized.final_prompt, model, context)
        completion = self.providers.generate(
            request,
            provider_name=provider,
            fallback_providers=(context or {}).get("fallback_providers"),
        )
        return self._build_run_response(optimized, completion)

    async def optimize_and_run_async(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> RunResponse:
        optimized = self.optimize_prompt(prompt, context)
        request = self._build_completion_request(optimized.final_prompt, model, context)
        completion = await self.providers.agenerate(
            request,
            provider_name=provider,
            fallback_providers=(context or {}).get("fallback_providers"),
        )
        return self._build_run_response(optimized, completion)

    def stream_run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[OptimizedPrompt, Iterator[str]]:
        optimized = self.optimize_prompt(prompt, context)
        request = self._build_completion_request(optimized.final_prompt, model, context, stream=True)
        return optimized, self.providers.stream(
            request,
            provider_name=provider,
            fallback_providers=(context or {}).get("fallback_providers"),
        )

    async def astream_run(
        self,
        prompt: str,
        provider: str | None = None,
        model: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[OptimizedPrompt, AsyncIterator[str]]:
        optimized = self.optimize_prompt(prompt, context)
        request = self._build_completion_request(optimized.final_prompt, model, context, stream=True)
        return optimized, self.providers.astream(
            request,
            provider_name=provider,
            fallback_providers=(context or {}).get("fallback_providers"),
        )

    def _build_completion_request(
        self,
        final_prompt: str,
        model: str | None,
        context: dict[str, Any] | None,
        stream: bool = False,
    ) -> CompletionRequest:
        context = context or {}
        return CompletionRequest(
            prompt=final_prompt,
            model=model or self.config.provider.default_model,
            stream=stream,
            response_schema=context.get("output_schema"),
        )

    def _build_run_response(self, optimized: OptimizedPrompt, completion) -> RunResponse:
        return RunResponse(
            original_prompt=optimized.original_prompt,
            optimized_prompt=optimized.final_prompt,
            intent=optimized.intent,
            skills_applied=optimized.skills_applied,
            transformations=optimized.transformations,
            provider=completion.provider,
            model=completion.model,
            provider_output=completion.output_text,
            usage=completion.usage,
            metadata=optimized.metadata,
            optimization_score=optimized.optimization_score,
            prompt_diff=optimized.prompt_diff,
            token_estimate=optimized.token_estimate,
            latency_ms=optimized.latency_ms + completion.latency_ms,
            provider_latency_ms=completion.latency_ms,
        )

    def _default_instructions(self, intent: str, context: dict[str, Any]) -> list[str]:
        instructions = [
            "Complete the request directly and keep the response tightly aligned to the requested deliverable.",
            "Use the provided context and source material before falling back to generic knowledge.",
        ]
        if audience := context.get("audience"):
            instructions.append(f"Target audience: {audience}.")
        if tone := context.get("tone"):
            instructions.append(f"Use a {tone} tone.")
        if context.get("output_schema"):
            instructions.append("Follow the provided schema exactly.")
        if intent == "coding":
            instructions.append("Return implementation-ready technical details, not generic advice.")
        elif intent == "reasoning":
            instructions.append("Return a concise conclusion with the key rationale and tradeoffs.")
        elif intent in {"extraction", "classification"}:
            instructions.append("Use only values that are grounded in the supplied input or context.")
        elif intent == "summarization":
            instructions.append("Preserve the most important facts, owners, dates, and risks.")
        if context.get("conversation_summary") or context.get("chat_context"):
            instructions.append("Use the recent conversation context only when it materially improves the answer.")
        return instructions

    def _cache_key(self, prompt: str, context: dict[str, Any]) -> str:
        payload = json.dumps({"prompt": prompt, "context": context}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
