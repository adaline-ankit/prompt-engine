from __future__ import annotations

import html
import json
from typing import Any

from prompt_engine.models import PromptState


class PromptCompiler:
    def __init__(self, max_chars: int = 24_000) -> None:
        self.max_chars = max_chars

    def compile(self, state: PromptState) -> str:
        sections: list[str] = []

        if state.role:
            sections.append(self._tagged_section("Role", "role", state.role))

        objective = state.goal or state.refined_prompt or state.sanitized_prompt or state.base_prompt
        sections.append(self._tagged_section("Objective", "objective", objective))

        if state.refined_prompt and state.refined_prompt != state.base_prompt:
            sections.append(self._tagged_section("Refined Request", "refined_request", state.refined_prompt))

        if state.instructions:
            sections.append(self._tagged_list_section("Instructions", "instructions", "instruction", state.instructions))

        if state.context_blocks:
            sections.append(self._context_section(state))

        if state.constraints:
            sections.append(self._tagged_list_section("Constraints", "constraints", "constraint", state.constraints))

        if state.expected_output:
            sections.append(
                self._tagged_list_section("Expected Output", "expected_output", "output_item", state.expected_output)
            )

        if state.output_format is not None:
            sections.append(
                self._tagged_section("Output Contract", "output_contract", self._render_output_format(state.output_format))
            )

        if state.examples:
            sections.append(self._tagged_examples_section(state.examples))

        sections.append(self._tagged_section("Source Prompt", "source_prompt", state.base_prompt))

        if state.missing_info:
            sections.append(self._tagged_list_section("Known Gaps", "known_gaps", "gap", state.missing_info))

        compiled = "\n\n".join(sections)
        if len(compiled) <= self.max_chars:
            return compiled
        return compiled[: self.max_chars - 3].rstrip() + "..."

    def _render_output_format(self, output_format: dict[str, Any] | str) -> str:
        if isinstance(output_format, str):
            return output_format
        return json.dumps(output_format, indent=2, sort_keys=True)

    def _tagged_section(self, label: str, tag: str, value: str) -> str:
        escaped = html.escape(value.strip())
        return f"{label}:\n<{tag}>\n{escaped}\n</{tag}>"

    def _tagged_list_section(self, label: str, tag: str, item_tag: str, values: list[str]) -> str:
        items = "\n".join(
            f'  <{item_tag} index="{index}">{html.escape(value)}</{item_tag}>'
            for index, value in enumerate(values, start=1)
        )
        return f"{label}:\n<{tag}>\n{items}\n</{tag}>"

    def _tagged_examples_section(self, examples: list[str]) -> str:
        items = "\n".join(
            f'  <example index="{index}">\n{html.escape(example.strip())}\n  </example>'
            for index, example in enumerate(examples, start=1)
        )
        return f"Examples:\n<examples>\n{items}\n</examples>"

    def _context_section(self, state: PromptState) -> str:
        blocks = []
        for block in state.context_blocks:
            description = f' description="{html.escape(block.description)}"' if block.description else ""
            blocks.append(
                f'  <context_block name="{html.escape(block.name)}"{description}>\n{html.escape(block.content.strip())}\n  </context_block>'
            )
        return "Context:\n<context>\n" + "\n".join(blocks) + "\n</context>"
