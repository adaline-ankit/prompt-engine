from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


IntentType = Literal[
    "coding",
    "reasoning",
    "classification",
    "extraction",
    "summarization",
    "agent_task",
    "tool_usage",
    "conversational",
    "unknown",
]


class IntentPrediction(BaseModel):
    intent: IntentType = "unknown"
    confidence: float = 0.0
    method: str = "rules"
    candidates: dict[str, float] = Field(default_factory=dict)


class PromptDecomposition(BaseModel):
    goal: str = ""
    constraints: list[str] = Field(default_factory=list)
    expected_output: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)


class TransformationStep(BaseModel):
    name: str
    kind: str
    description: str
    before: str | None = None
    after: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationScore(BaseModel):
    clarity: float
    structure: float
    completeness: float
    overall: float


class PromptContextBlock(BaseModel):
    name: str
    content: str
    description: str | None = None


class PromptState(BaseModel):
    base_prompt: str
    sanitized_prompt: str
    refined_prompt: str | None = None
    role: str | None = None
    intent: IntentType = "unknown"
    goal: str = ""
    instructions: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_output: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    context_blocks: list[PromptContextBlock] = Field(default_factory=list)
    output_format: dict[str, Any] | str | None = None
    transformations: list[TransformationStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizedPrompt(BaseModel):
    original_prompt: str
    final_prompt: str
    intent: IntentType
    skills_applied: list[str]
    transformations: list[TransformationStep]
    metadata: dict[str, Any] = Field(default_factory=dict)
    optimization_score: OptimizationScore
    prompt_diff: str
    token_estimate: int
    latency_ms: int


class CompletionRequest(BaseModel):
    prompt: str
    model: str
    max_output_tokens: int = 600
    temperature: float = 0.0
    stream: bool = False
    response_schema: dict[str, Any] | None = None


class CompletionResponse(BaseModel):
    provider: str
    model: str
    output_text: str
    latency_ms: int
    usage: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class OptimizeRequest(BaseModel):
    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)


class RunRequest(BaseModel):
    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)
    provider: str | None = None
    model: str | None = None
    stream: bool = False


class RunResponse(BaseModel):
    original_prompt: str
    optimized_prompt: str
    intent: IntentType
    skills_applied: list[str]
    transformations: list[TransformationStep]
    provider: str
    model: str
    provider_output: str
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    optimization_score: OptimizationScore
    prompt_diff: str
    token_estimate: int
    latency_ms: int
    provider_latency_ms: int
