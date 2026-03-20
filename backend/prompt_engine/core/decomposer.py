from __future__ import annotations

import re
from typing import Any

from prompt_engine.models import PromptDecomposition


_CONSTRAINT_RE = re.compile(
    r"\b(must|should|avoid|never|only|limit|exactly|required|at most|at least|do not|don't)\b",
    re.IGNORECASE,
)
_OUTPUT_RE = re.compile(
    r"\b(json|yaml|xml|markdown|bullet|table|schema|return|output|respond|format)\b",
    re.IGNORECASE,
)
_EXAMPLE_RE = re.compile(r"\b(example|sample|for instance|e\.g\.)\b", re.IGNORECASE)
_REQUEST_VERB_RE = re.compile(
    r"\b(extract|summarize|classify|analyze|compare|refactor|debug|write|draft|plan|explain|generate|optimize)\b",
    re.IGNORECASE,
)


class PromptDecomposer:
    def decompose(self, prompt: str, context: dict[str, Any] | None = None) -> PromptDecomposition:
        context = context or {}
        lines = [line.strip(" -*\t") for line in prompt.splitlines() if line.strip()]
        goal = self._extract_goal(lines, prompt)
        constraints = self._extract_matches(lines, _CONSTRAINT_RE)
        expected_output = self._extract_matches(lines, _OUTPUT_RE)
        expected_output.extend(self._infer_expected_output(prompt, context))
        missing_info = self._detect_missing_info(prompt, constraints, expected_output, context)

        if context.get("output_schema"):
            expected_output.append("Return output that matches the provided schema.")
        if any(_EXAMPLE_RE.search(line) for line in lines):
            expected_output.append("Use the provided examples as formatting guidance.")

        return PromptDecomposition(
            goal=goal,
            constraints=_unique(constraints),
            expected_output=_unique(expected_output),
            missing_info=_unique(missing_info),
        )

    def _extract_goal(self, lines: list[str], prompt: str) -> str:
        for line in lines:
            if _REQUEST_VERB_RE.search(line):
                return line.rstrip(".")
        if lines:
            return lines[0].rstrip(".")
        sentence = prompt.strip().split(".")[0].strip()
        return sentence or "Respond to the user request faithfully."

    def _extract_matches(self, lines: list[str], pattern: re.Pattern[str]) -> list[str]:
        return [line for line in lines if pattern.search(line)]

    def _detect_missing_info(
        self,
        prompt: str,
        constraints: list[str],
        expected_output: list[str],
        context: dict[str, Any],
    ) -> list[str]:
        missing_info: list[str] = []

        if not constraints:
            missing_info.append("No explicit task constraints were provided.")
        if not expected_output and "output_schema" not in context:
            missing_info.append("No explicit output format was provided.")
        if len(prompt.split()) < 12:
            missing_info.append("Prompt is terse; desired depth or audience may be under-specified.")
        if not any(key in context for key in ("chat_context", "conversation_summary", "selected_text", "surrounding_text")):
            missing_info.append("No surrounding source context was supplied.")

        return missing_info

    def _infer_expected_output(self, prompt: str, context: dict[str, Any]) -> list[str]:
        inferred: list[str] = []
        lowered = prompt.lower()

        if "json" in lowered or context.get("output_schema"):
            inferred.append("Return a machine-readable JSON response.")
        if "bullet" in lowered or "bullet points" in lowered:
            inferred.append("Use concise bullet points.")
        if "table" in lowered:
            inferred.append("Return a table if it improves readability.")

        return inferred


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
