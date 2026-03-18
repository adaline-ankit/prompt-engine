from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from prompt_engine.config import AppConfig, load_config
from prompt_engine.engine.optimizer import PromptOptimizationEngine
from prompt_engine.mcp.models import SchemaSuggestion, SkillCatalog, SkillDescriptor, TransformationExplanation


DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8001
DEFAULT_HTTP_PATH = "/mcp"


def build_mcp_server(
    config_path: str | Path | None = None,
    *,
    host: str = DEFAULT_HTTP_HOST,
    port: int = DEFAULT_HTTP_PORT,
    streamable_http_path: str = DEFAULT_HTTP_PATH,
) -> FastMCP:
    config = load_config(config_path)
    engine = PromptOptimizationEngine(config)
    transport_security = _build_transport_security(config, host)
    server = FastMCP(
        name="Prompt Engine",
        instructions=(
            "Use Prompt Engine to optimize raw prompts, inspect transformations, "
            "suggest output schemas, and optionally run optimized prompts via configured providers."
        ),
        host=host,
        port=port,
        streamable_http_path=streamable_http_path,
        debug=config.environment == "development",
        log_level="INFO",
        transport_security=transport_security,
    )

    @server.tool(
        name="optimize_prompt",
        description="Optimize a raw prompt into a structured, higher-signal prompt with trace metadata.",
        structured_output=True,
    )
    def optimize_prompt(prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        result = engine.optimize_prompt(prompt, context or {})
        return result.model_dump()

    @server.tool(
        name="optimize_and_run",
        description="Optimize a prompt and execute it against a provider.",
        structured_output=True,
    )
    def optimize_and_run(
        prompt: str,
        context: dict[str, Any] | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        result = engine.optimize_and_run(prompt, provider=provider, model=model, context=context or {})
        return result.model_dump()

    @server.tool(
        name="explain_transformations",
        description="Return a compact explanation of the prompt optimization pipeline for a given prompt.",
        structured_output=True,
    )
    def explain_transformations(prompt: str, context: dict[str, Any] | None = None) -> TransformationExplanation:
        result = engine.optimize_prompt(prompt, context or {})
        decomposition = result.metadata.get("decomposition", {})
        guidance = list(decomposition.get("missing_info", []))
        if not guidance:
            guidance.append("No major specification gaps detected.")
        return TransformationExplanation(
            intent=result.intent,
            goal=str(decomposition.get("goal", "")),
            skills_applied=result.skills_applied,
            transformations=[step.model_dump() for step in result.transformations],
            guidance=guidance,
        )

    @server.tool(
        name="suggest_output_schema",
        description="Infer a JSON schema skeleton that fits the prompt intent.",
        structured_output=True,
    )
    def suggest_output_schema(prompt: str, context: dict[str, Any] | None = None) -> SchemaSuggestion:
        return infer_output_schema(engine, prompt, context or {})

    @server.tool(
        name="list_skills",
        description="List built-in and plugin skills known to Prompt Engine.",
        structured_output=True,
    )
    def list_skills() -> SkillCatalog:
        return SkillCatalog(
            skills=[
                SkillDescriptor(
                    name=skill.name,
                    category=skill.category,
                    priority=skill.effective_priority(config.skills.skill_priority),
                    conflicts_with=sorted(skill.conflicts_with),
                    enabled=skill.name in config.skills.enabled_skills,
                )
                for skill in sorted(engine.registry.skills.values(), key=lambda skill: skill.name)
            ],
            enabled_skills=list(config.skills.enabled_skills),
        )

    @server.prompt(
        name="optimize_task",
        description="Prepare a task for Prompt Engine optimization before handing it to an agent or model.",
    )
    def optimize_task(task: str, output_requirements: str = "Use the most reliable output format for this task.") -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": (
                    "Use Prompt Engine to optimize this task before executing it.\n"
                    f"Task: {task}\n"
                    f"Output requirements: {output_requirements}"
                ),
            }
        ]

    @server.prompt(
        name="extract_json",
        description="Prepare an extraction request with explicit JSON output expectations.",
    )
    def extract_json(source_text: str, fields: str) -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": (
                    "Optimize this extraction task and enforce structured JSON output.\n"
                    f"Source text: {source_text}\n"
                    f"Fields to extract: {fields}"
                ),
            }
        ]

    return server


def infer_output_schema(
    engine: PromptOptimizationEngine,
    prompt: str,
    context: dict[str, Any] | None = None,
) -> SchemaSuggestion:
    context = context or {}
    if context.get("output_schema"):
        return SchemaSuggestion(
            intent=engine.detector.detect(prompt, context).intent,
            output_schema=context["output_schema"],
            rationale="Using the schema supplied by the caller.",
            inferred_fields=sorted(context["output_schema"].get("properties", {}).keys()),
        )

    intent = engine.detector.detect(prompt, context).intent
    inferred_fields = _extract_fields(prompt)

    if intent == "classification":
        schema = {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "confidence": {"type": "number"},
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["label"],
        }
        rationale = "Classification tasks benefit from a stable label and optional confidence/evidence fields."
    elif intent == "extraction":
        properties = {
            field: {"type": "string"} for field in (inferred_fields or ["result"])
        }
        properties["evidence"] = {"type": "array", "items": {"type": "string"}}
        schema = {
            "type": "object",
            "properties": properties,
            "required": [field for field in inferred_fields] or ["result"],
        }
        rationale = "Extraction tasks benefit from one object keyed by extracted fields plus grounded evidence."
    elif intent == "summarization":
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary"],
        }
        rationale = "Summaries are more reusable when broken into concise bullet arrays."
    elif intent in {"coding", "agent_task"}:
        schema = {
            "type": "object",
            "properties": {
                "outcome": {"type": "string"},
                "key_decisions": {"type": "array", "items": {"type": "string"}},
                "artifacts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["outcome"],
        }
        rationale = "Execution-oriented tasks work best with outcome, decisions, and artifact references."
    else:
        schema = {
            "type": "object",
            "properties": {
                "response": {"type": "string"},
            },
            "required": ["response"],
        }
        rationale = "A generic object keeps downstream integrations stable when the task shape is ambiguous."

    return SchemaSuggestion(
        intent=intent,
        output_schema=schema,
        rationale=rationale,
        inferred_fields=inferred_fields,
    )


def build_cursor_stdio_config(config_path: str | Path | None = None) -> dict[str, Any]:
    env: dict[str, str] = {}
    if config_path:
        env["PROMPT_ENGINE_CONFIG"] = str(Path(config_path).resolve())
    return {
        "mcpServers": {
            "prompt-engine": {
                "command": "prompt-engine",
                "args": ["mcp", "stdio"],
                "env": env,
            }
        }
    }


def build_cursor_http_config(url: str = f"http://{DEFAULT_HTTP_HOST}:{DEFAULT_HTTP_PORT}{DEFAULT_HTTP_PATH}") -> dict[str, Any]:
    return {
        "mcpServers": {
            "prompt-engine": {
                "url": url,
            }
        }
    }


def _extract_fields(prompt: str) -> list[str]:
    match = re.search(r"\bextract\b(?P<fields>.+?)(?:\bfrom\b|\breturn\b|$)", prompt, flags=re.IGNORECASE)
    if not match:
        return []
    raw_fields = match.group("fields")
    cleaned = re.sub(r"\b(the|following|these|this)\b", "", raw_fields, flags=re.IGNORECASE)
    parts = re.split(r",| and ", cleaned)
    fields = []
    for part in parts:
        value = re.sub(r"[^a-zA-Z0-9_ ]", "", part).strip().lower().replace(" ", "_")
        if value:
            fields.append(value)
    seen: set[str] = set()
    ordered: list[str] = []
    for field in fields:
        if field not in seen:
            seen.add(field)
            ordered.append(field)
    return ordered


def dump_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2)


def _build_transport_security(config: AppConfig, host: str) -> TransportSecuritySettings:
    allowed_hosts = {
        host,
        f"{host}:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
    }
    allowed_origins = {
        "http://127.0.0.1:*",
        "https://127.0.0.1:*",
        "http://localhost:*",
        "https://localhost:*",
    }

    for origin in config.security.allow_origins:
        if origin == "*":
            continue
        allowed_origins.add(origin)

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=sorted(allowed_hosts),
        allowed_origins=sorted(allowed_origins),
    )
