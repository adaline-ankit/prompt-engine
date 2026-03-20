from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from prompt_engine.config import AppConfig
from prompt_engine.models import PromptState
from prompt_engine.skills.base import Skill
from prompt_engine.skills.builtins import (
    BestPracticePromptingSkill,
    HallucinationGuardSkill,
    RoleInjectionSkill,
    StructuredOutputSkill,
)


class SkillRegistry:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.skills: dict[str, Skill] = {}
        self.load_errors: dict[str, str] = {}
        self.register_many(
            [
                RoleInjectionSkill(),
                BestPracticePromptingSkill(),
                HallucinationGuardSkill(),
                StructuredOutputSkill(),
            ]
        )
        self.load_plugins(config.skills.plugin_paths)

    def register(self, skill: Skill) -> None:
        self.skills[skill.name] = skill

    def register_many(self, skills: list[Skill]) -> None:
        for skill in skills:
            self.register(skill)

    def load_plugins(self, plugin_paths: list[str]) -> None:
        for plugin_path in plugin_paths:
            path = Path(plugin_path)
            if not path.exists():
                continue
            if path.is_file() and path.suffix == ".py":
                self._load_plugin_file(path)
                continue
            for file_path in sorted(path.glob("*.py")):
                if file_path.name.startswith("_"):
                    continue
                self._load_plugin_file(file_path)

    def select_skills(
        self,
        state: PromptState,
        context: dict[str, Any],
    ) -> tuple[list[Skill], dict[str, str]]:
        enabled_skills = set(self.config.skills.enabled_skills)
        overrides = self.config.skills.skill_priority
        candidates = [
            skill
            for skill in self.skills.values()
            if skill.name in enabled_skills and skill.should_trigger(state, context)
        ]
        candidates.sort(key=lambda skill: (skill.effective_priority(overrides), skill.name))

        selected: list[Skill] = []
        skipped: dict[str, str] = {}

        for skill in candidates:
            conflict = next(
                (
                    active_skill.name
                    for active_skill in selected
                    if skill.name in active_skill.conflicts_with or active_skill.name in skill.conflicts_with
                ),
                None,
            )
            if conflict:
                skipped[skill.name] = f"conflicts with higher-priority skill {conflict}"
                continue
            selected.append(skill)

        if self.load_errors:
            skipped.update({name: f"plugin load error: {reason}" for name, reason in self.load_errors.items()})

        return selected, skipped

    def _load_plugin_file(self, file_path: Path) -> None:
        module_name = f"prompt_engine_plugin_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            self.load_errors[file_path.name] = "unable to create module spec"
            return

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            factory = getattr(module, "register", None) or getattr(module, "register_skills", None)
            if factory is None:
                self.load_errors[file_path.name] = "register() or register_skills() not found"
                return
            registered = factory()
            skills = registered if isinstance(registered, list) else [registered]
            self.register_many(skills)
        except Exception as exc:  # pragma: no cover - defensive plugin boundary
            self.load_errors[file_path.name] = str(exc)
