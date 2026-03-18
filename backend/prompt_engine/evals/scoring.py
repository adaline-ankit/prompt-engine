from __future__ import annotations

from typing import Any

from prompt_engine.models import OptimizedPrompt
from prompt_engine.scoring import estimate_tokens


def score_case(case: dict[str, Any], runs: list[OptimizedPrompt]) -> dict[str, Any]:
    result = runs[0]
    expectations = case.get("expectations", {})
    required_sections = expectations.get("required_sections", [])
    required_skills = expectations.get("required_skills", [])
    expected_intent = expectations.get("intent")

    intent_score = 1.0 if not expected_intent or result.intent == expected_intent else 0.0
    skill_score = _coverage_score(required_skills, result.skills_applied)
    section_score = _section_score(required_sections, result.final_prompt)
    semantic_score = _semantic_score(expectations.get("expected_keywords", []), result.final_prompt)
    hallucination_risk = 0.0 if "hallucination_guard" in result.skills_applied else 0.5
    consistency_score = _consistency_score(runs)
    token_efficiency = _token_efficiency(case["prompt"], result.final_prompt)

    overall = round(
        (
            intent_score * 0.15
            + skill_score * 0.15
            + section_score * 0.2
            + semantic_score * 0.15
            + (1 - hallucination_risk) * 0.15
            + consistency_score * 0.1
            + token_efficiency * 0.1
        ),
        3,
    )

    return {
        "id": case["id"],
        "intent_score": intent_score,
        "skill_score": skill_score,
        "structure_score": section_score,
        "semantic_score": semantic_score,
        "hallucination_risk": hallucination_risk,
        "consistency_score": consistency_score,
        "token_efficiency": token_efficiency,
        "overall": overall,
        "pass": overall >= expectations.get("passing_score", 0.75),
    }


def _coverage_score(required: list[str], actual: list[str]) -> float:
    if not required:
        return 1.0
    covered = sum(1 for item in required if item in actual)
    return round(covered / len(required), 3)


def _section_score(required_sections: list[str], final_prompt: str) -> float:
    if not required_sections:
        return 1.0
    covered = sum(1 for section in required_sections if section in final_prompt)
    return round(covered / len(required_sections), 3)


def _semantic_score(expected_keywords: list[str], final_prompt: str) -> float:
    if not expected_keywords:
        return 1.0
    lowered = final_prompt.lower()
    covered = sum(1 for keyword in expected_keywords if keyword.lower() in lowered)
    return round(covered / len(expected_keywords), 3)


def _consistency_score(runs: list[OptimizedPrompt]) -> float:
    prompts = {run.final_prompt for run in runs}
    return 1.0 if len(prompts) == 1 else round(1 / len(prompts), 3)


def _token_efficiency(original_prompt: str, final_prompt: str) -> float:
    raw_tokens = estimate_tokens(original_prompt)
    final_tokens = estimate_tokens(final_prompt)
    ceiling = max(raw_tokens * 4, 1)
    if final_tokens <= ceiling:
        return 1.0
    return round(ceiling / final_tokens, 3)

