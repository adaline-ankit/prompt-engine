from __future__ import annotations

from typing import Any

from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill


class StructuredOutputSkill(Skill):
    name = "structured_output"
    category = "prompt_engineering"
    priority = 30

    def should_trigger(self, state: PromptState, context: dict[str, Any]) -> bool:
        return state.output_format is None or state.intent in {
            "classification",
            "extraction",
            "summarization",
            "agent_task",
            "coding",
        }

    def transform(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        before = str(state.output_format) if state.output_format else None

        if context.get("output_schema"):
            state.output_format = {
                "type": "json_schema",
                "schema": context["output_schema"],
            }
            self.append_unique(state.expected_output, "Return only data that matches the supplied schema.")
        elif state.intent in {"classification", "extraction"}:
            state.output_format = {
                "type": "json_object",
                "schema": {
                    "result": "primary result or extracted fields",
                    "confidence": "0-1 confidence score if available",
                    "evidence": ["short grounded evidence snippets"],
                },
            }
            self.append_unique(state.expected_output, "Return a machine-readable JSON object.")
        elif state.intent in {"coding", "agent_task"}:
            state.output_format = {
                "type": "markdown_sections",
                "sections": ["Outcome", "Key Decisions", "Artifacts"],
            }
            self.append_unique(state.expected_output, "Return concise markdown sections for actionability.")
        else:
            state.output_format = "Return a concise markdown bullet list."
            self.append_unique(state.expected_output, "Use concise bullet points.")

        self.append_unique(state.constraints, "Follow the requested output contract exactly.")
        self.record_transformation(
            state,
            description="Defines an explicit output contract for downstream reliability.",
            before=before,
            after=str(state.output_format),
        )
        return state

