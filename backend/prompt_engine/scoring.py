from __future__ import annotations

import math

from prompt_engine.models import OptimizationScore, PromptState


def estimate_tokens(text: str) -> int:
    words = max(len(text.split()), 1)
    return math.ceil(words / 0.75)


def compute_optimization_score(state: PromptState, final_prompt: str) -> OptimizationScore:
    clarity = _bounded(
        (0.35 if state.goal else 0.0)
        + (0.25 if state.role else 0.0)
        + min(0.3, len(state.instructions) * 0.08)
        + (0.1 if state.refined_prompt else 0.0)
    )

    structure = _bounded(
        (0.2 if state.role else 0.0)
        + min(0.2, len(state.constraints) * 0.05)
        + min(0.2, len(state.expected_output) * 0.1)
        + (0.25 if state.output_format else 0.0)
        + (0.15 if "Source Prompt:" in final_prompt else 0.0)
        + (0.1 if "Context:" in final_prompt else 0.0)
    )

    completeness = _bounded(
        0.4
        + min(0.25, len(state.instructions) * 0.05)
        + min(0.2, len(state.constraints) * 0.04)
        + (0.2 if state.output_format else 0.0)
        + min(0.1, len(state.context_blocks) * 0.03)
        - min(0.45, len(state.missing_info) * 0.15)
    )

    overall = round(((clarity * 0.35) + (structure * 0.35) + (completeness * 0.30)), 3)
    return OptimizationScore(
        clarity=round(clarity, 3),
        structure=round(structure, 3),
        completeness=round(completeness, 3),
        overall=overall,
    )


def _bounded(score: float) -> float:
    return max(0.0, min(score, 1.0))
