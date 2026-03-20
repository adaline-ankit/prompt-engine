from __future__ import annotations

from typing import Any

from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill


class BestPracticePromptingSkill(Skill):
    name = "best_practice_prompting"
    category = "prompt_engineering"
    priority = 15

    def should_trigger(self, state: PromptState, context: dict[str, Any]) -> bool:
        return state.intent != "unknown"

    def transform(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        before = "\n".join(state.instructions)

        self.append_unique(
            state.instructions,
            "Keep instructions explicit and self-contained so the model can follow them without hidden context.",
        )
        self.append_unique(
            state.instructions,
            "Prefer positive directives that describe what to do, and reserve prohibitions for critical failure modes.",
        )
        if state.context_blocks:
            self.append_unique(
                state.instructions,
                "Use the context blocks only when they are relevant to the objective, and ignore unrelated noise.",
            )
        if state.intent in {"extraction", "classification"}:
            self.append_unique(
                state.constraints,
                "If a value is unsupported by the source, return null, unknown, or an explicit gap instead of guessing.",
            )
            self.append_unique(
                state.expected_output,
                "Include grounded evidence or source snippets when the output contract allows it.",
            )
        if state.intent == "reasoning":
            self.append_unique(
                state.instructions,
                "Reason carefully before answering, then return the conclusion and a concise rationale unless the user asks for full working.",
            )
        if state.intent in {"coding", "agent_task"}:
            self.append_unique(
                state.expected_output,
                "Make the result directly actionable for an engineer or operator.",
            )

        self.record_transformation(
            state,
            description="Adds model-agnostic prompt-engineering guidance aligned to explicit instructions, grounded context, and reliable outputs.",
            before=before or None,
            after="\n".join(state.instructions),
        )
        return state
