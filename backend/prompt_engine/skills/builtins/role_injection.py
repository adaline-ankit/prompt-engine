from __future__ import annotations

from typing import Any

from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill


class RoleInjectionSkill(Skill):
    name = "role_injection"
    category = "prompt_engineering"
    priority = 10

    _ROLE_MAP = {
        "coding": "You are a senior software engineer optimizing for correctness, maintainability, and concrete implementation details.",
        "reasoning": "You are a rigorous analyst who explains tradeoffs, assumptions, and conclusions clearly.",
        "classification": "You are a precise classifier that labels inputs consistently and avoids unsupported guesses.",
        "extraction": "You are an information extraction system that returns only grounded fields from the provided input.",
        "summarization": "You are an expert summarizer that preserves the most important details without fluff.",
        "agent_task": "You are an execution-focused AI agent that translates instructions into dependable, verifiable actions.",
        "tool_usage": "You are a tool-using assistant that formats requests so external tools can be called predictably.",
        "conversational": "You are a concise and helpful assistant.",
    }

    def should_trigger(self, state: PromptState, context: dict[str, Any]) -> bool:
        return True

    def transform(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        before = state.role
        state.role = self._ROLE_MAP.get(state.intent, self._ROLE_MAP["conversational"])
        self.append_unique(state.instructions, "Prioritize the user's objective before optional elaboration.")
        self.record_transformation(
            state,
            description="Injects an intent-specific role and a directness instruction.",
            before=before,
            after=state.role,
        )
        return state

