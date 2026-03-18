from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from prompt_engine.models import PromptState, TransformationStep


class Skill(ABC):
    name: str
    category: str = "prompt_engineering"
    priority: int = 100
    conflicts_with: frozenset[str] = frozenset()

    @abstractmethod
    def should_trigger(self, state: PromptState, context: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def transform(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        raise NotImplementedError

    def effective_priority(self, overrides: dict[str, int]) -> int:
        return overrides.get(self.name, self.priority)

    def record_transformation(
        self,
        state: PromptState,
        description: str,
        before: str | None = None,
        after: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        state.transformations.append(
            TransformationStep(
                name=self.name,
                kind=self.category,
                description=description,
                before=before,
                after=after,
                metadata=metadata or {},
            )
        )

    def append_unique(self, values: list[str], item: str) -> None:
        if item not in values:
            values.append(item)

