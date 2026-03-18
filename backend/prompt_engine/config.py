from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


DEFAULT_CONFIG_PATH = Path(os.getenv("PROMPT_ENGINE_CONFIG", "config/config.yaml"))


class ProviderSettings(BaseModel):
    default_provider: str = "mock"
    default_model: str = "mock-gpt"
    timeout_seconds: float = 30.0
    max_retries: int = 2
    fallback_providers: list[str] = Field(default_factory=lambda: ["mock"])


class SkillSettings(BaseModel):
    enabled_skills: list[str] = Field(
        default_factory=lambda: ["role_injection", "hallucination_guard", "structured_output"]
    )
    skill_priority: dict[str, int] = Field(default_factory=dict)
    plugin_paths: list[str] = Field(default_factory=lambda: ["skills"])


class OutputSettings(BaseModel):
    default_output_format: str = "markdown_sections"
    max_prompt_chars: int = 24_000


class SecuritySettings(BaseModel):
    pii_masking: bool = False
    rate_limit_per_minute: int = 60
    allow_origins: list[str] = Field(default_factory=lambda: ["*"])


class ObservabilitySettings(BaseModel):
    service_name: str = "prompt-engine"
    enable_metrics: bool = True
    enable_tracing: bool = True


class CacheSettings(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 300
    max_entries: int = 256


class AppConfig(BaseModel):
    environment: str = "development"
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    skills: SkillSettings = Field(default_factory=SkillSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path or DEFAULT_CONFIG_PATH)
    payload: dict = {}

    if config_path.exists():
        payload = yaml.safe_load(config_path.read_text()) or {}

    config = AppConfig.model_validate(payload)
    _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: AppConfig) -> None:
    provider = os.getenv("PROMPT_ENGINE_DEFAULT_PROVIDER")
    model = os.getenv("PROMPT_ENGINE_DEFAULT_MODEL")

    if provider:
        config.provider.default_provider = provider
    if model:
        config.provider.default_model = model

