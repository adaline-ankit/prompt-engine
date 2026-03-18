from __future__ import annotations

from typing import Any

from prompt_engine.models import PromptState
from prompt_engine.skills.registry import SkillRegistry


class OptimizationPipeline:
    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    def run(self, state: PromptState, context: dict[str, Any] | None = None) -> tuple[PromptState, list[str]]:
        context = context or {}
        selected_skills, skipped_skills = self.registry.select_skills(state, context)
        if skipped_skills:
            state.metadata.setdefault("skipped_skills", {}).update(skipped_skills)

        for skill in selected_skills:
            state = skill.transform(state, context)

        return state, [skill.name for skill in selected_skills]
