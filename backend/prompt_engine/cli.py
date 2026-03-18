from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml

from prompt_engine.config import load_config
from prompt_engine.engine.optimizer import PromptOptimizationEngine
from prompt_engine.mcp.cli import app as mcp_app


app = typer.Typer(
    add_completion=False,
    help="Optimize prompts and optionally run them against an LLM provider.",
    no_args_is_help=True,
)
app.add_typer(mcp_app, name="mcp")


@app.callback()
def main() -> None:
    """Prompt Engine command group."""


@app.command("run")
def run_command(
    prompt: str,
    context_file: Path | None = typer.Option(None, "--context-file", help="Path to a JSON or YAML context file."),
    provider: str | None = typer.Option(None, "--provider", help="Provider to use when --run-llm is enabled."),
    model: str | None = typer.Option(None, "--model", help="Model override for provider execution."),
    run_llm: bool = typer.Option(False, "--run-llm", help="Execute the optimized prompt against a provider."),
    stream: bool = typer.Option(False, "--stream", help="Stream provider output when --run-llm is enabled."),
    show_diff: bool = typer.Option(True, "--show-diff/--hide-diff", help="Print a unified diff."),
    as_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    config_path: Path = typer.Option(Path("config/config.yaml"), "--config", help="Config file path."),
) -> None:
    context = _load_context(context_file)
    engine = PromptOptimizationEngine(load_config(config_path))

    if run_llm and stream:
        optimized, chunks = engine.stream_run(prompt, provider=provider, model=model, context=context)
        typer.echo(f"Intent: {optimized.intent}")
        typer.echo(f"Skills: {', '.join(optimized.skills_applied)}")
        typer.echo("\nStreaming provider output:\n")
        for chunk in chunks:
            typer.echo(chunk, nl=False)
        typer.echo("")
        return

    if run_llm:
        result = engine.optimize_and_run(prompt, provider=provider, model=model, context=context)
        if as_json:
            typer.echo(json.dumps(result.model_dump(), indent=2))
            return
        typer.echo(f"Intent: {result.intent}")
        typer.echo(f"Skills: {', '.join(result.skills_applied)}")
        typer.echo(f"Provider: {result.provider}/{result.model}")
        typer.echo("\nOptimized Prompt:\n")
        typer.echo(result.optimized_prompt)
        typer.echo("\nProvider Output:\n")
        typer.echo(result.provider_output)
        if show_diff and result.prompt_diff:
            typer.echo("\nDiff:\n")
            typer.echo(result.prompt_diff)
        return

    result = engine.optimize_prompt(prompt, context=context)
    if as_json:
        typer.echo(json.dumps(result.model_dump(), indent=2))
        return

    typer.echo(f"Intent: {result.intent}")
    typer.echo(f"Skills: {', '.join(result.skills_applied)}")
    typer.echo("\nOptimized Prompt:\n")
    typer.echo(result.final_prompt)
    if show_diff and result.prompt_diff:
        typer.echo("\nDiff:\n")
        typer.echo(result.prompt_diff)


def _load_context(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    content = path.read_text()
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(content) or {}
    return json.loads(content)


if __name__ == "__main__":
    app()
