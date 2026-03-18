from __future__ import annotations

import json
from typing import Any

from prompt_engine.models import PromptState


class PromptCompiler:
    def __init__(self, max_chars: int = 24_000) -> None:
        self.max_chars = max_chars

    def compile(self, state: PromptState) -> str:
        sections: list[str] = []

        if state.role:
            sections.append(f"Role:\n{state.role}")

        objective = state.goal or state.base_prompt
        sections.append(f"Objective:\n{objective}")

        if state.instructions:
            instructions = "\n".join(
                f"{index}. {instruction}" for index, instruction in enumerate(state.instructions, start=1)
            )
            sections.append(f"Instructions:\n{instructions}")

        if state.constraints:
            constraints = "\n".join(f"- {constraint}" for constraint in state.constraints)
            sections.append(f"Constraints:\n{constraints}")

        if state.expected_output:
            expected_output = "\n".join(f"- {item}" for item in state.expected_output)
            sections.append(f"Expected Output:\n{expected_output}")

        if state.output_format is not None:
            sections.append(f"Output Contract:\n{self._render_output_format(state.output_format)}")

        if state.examples:
            examples = "\n\n".join(state.examples)
            sections.append(f"Examples:\n{examples}")

        sections.append(f"Source Prompt:\n{state.base_prompt}")

        if state.missing_info:
            guidance = "\n".join(f"- {item}" for item in state.missing_info)
            sections.append(f"Known Gaps:\n{guidance}")

        compiled = "\n\n".join(sections)
        if len(compiled) <= self.max_chars:
            return compiled
        return compiled[: self.max_chars - 3].rstrip() + "..."

    def _render_output_format(self, output_format: dict[str, Any] | str) -> str:
        if isinstance(output_format, str):
            return output_format
        return json.dumps(output_format, indent=2, sort_keys=True)

