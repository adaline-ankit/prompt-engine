from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillDescriptor(BaseModel):
    name: str
    category: str
    priority: int
    conflicts_with: list[str] = Field(default_factory=list)
    enabled: bool


class SkillCatalog(BaseModel):
    skills: list[SkillDescriptor]
    enabled_skills: list[str]


class TransformationExplanation(BaseModel):
    intent: str
    goal: str
    skills_applied: list[str]
    transformations: list[dict[str, Any]]
    guidance: list[str]


class SchemaSuggestion(BaseModel):
    intent: str
    output_schema: dict[str, Any]
    rationale: str
    inferred_fields: list[str] = Field(default_factory=list)
