from __future__ import annotations

from typing import Any

from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill


class HallucinationGuardSkill(Skill):
    name = "hallucination_guard"
    category = "safety"
    priority = 20

    def should_trigger(self, state: PromptState, context: dict[str, Any]) -> bool:
        return state.intent != "conversational"

    def transform(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        before = "\n".join(state.constraints)
        self.append_unique(
            state.constraints,
            "Do not invent facts, APIs, files, or results that are not grounded in the prompt or supplied context.",
        )
        self.append_unique(state.constraints, "If critical information is missing, state the gap explicitly.")
        self.append_unique(state.instructions, "Make assumptions explicit instead of implying certainty.")
        self.record_transformation(
            state,
            description="Adds anti-hallucination constraints and assumption handling guidance.",
            before=before or None,
            after="\n".join(state.constraints),
        )
        return state

