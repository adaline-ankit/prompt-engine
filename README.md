# Prompt Engine

Prompt Engine is a production-ready prompt optimization middleware that takes raw prompts, decomposes intent, applies skills, assembles a higher-signal prompt, and optionally sends it to an LLM provider.

It is designed to work as:

- an MCP server for Cursor, Claude Code, and other agents
- a Python SDK
- a FastAPI service
- a CLI for developers and AI agents
- a pluggable prompt transformation platform

## Core capabilities

- Intent detection with rule-based classification and an LLM-classifier extension point
- Prompt decomposition into goal, constraints, expected output, and missing information
- Skill-driven prompt enrichment and conflict-aware ordering
- Structured output enforcement and hallucination guards
- Provider-agnostic execution with retry, timeout, fallback, and stream interfaces
- MCP tools and prompts over `stdio` and Streamable HTTP
- Prompt diffs, heuristic optimization scoring, tracing, and Prometheus metrics
- Eval harness that runs in CI when skills or prompt logic change

## Project structure

```text
backend/prompt_engine/
  api/             FastAPI application, schemas, rate limiting
  core/            prompt decomposition and compilation
  engine/          intent detection and orchestration
  evals/           evaluation runner and scoring logic
  mcp/             MCP server, tools, prompts, and HTTP app
  observability/   tracing and metrics
  pipeline/        skill execution pipeline
  providers/       mock, OpenAI, Anthropic, OpenRouter adapters
  skills/          skill contracts, registry, built-in skills

config/
  config.yaml      default runtime configuration

evals/
  test_cases.json  sample evaluation corpus
  runner.py        top-level evaluation entrypoint
  scoring.py       scoring entrypoint

sdk/
  python/          usage examples for the Python SDK
  typescript/      API client SDK

examples/
  cursor/          Cursor MCP config examples
  claude-code/     Claude Code MCP setup notes

skills/
  README.md        external plugin authoring guide

tests/
  unit and API smoke tests

extensions/
  vscode-prompt-engine/  VS Code and Cursor extension
  chrome-prompt-engine/  Chrome extension for browser prompt rewriting
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
vibe-prompt-engine run "Extract the customer objections from this transcript and return JSON."
uvicorn prompt_engine.api.app:app --reload
vibe-prompt-engine mcp cursor-config --transport stdio
python evals/runner.py
```

## Extensions

Prompt Engine now ships with first-party extension clients:

- VS Code/Cursor extension in [extensions/vscode-prompt-engine](extensions/vscode-prompt-engine)
- Chrome extension in [extensions/chrome-prompt-engine](extensions/chrome-prompt-engine)

VS Code or Cursor local test:

```bash
cd extensions/vscode-prompt-engine
npm install
npm run build
npm run package
```

Then install `vibe-prompt-engine-vscode-0.1.2.vsix` from:

- VS Code: `Extensions: Install from VSIX...`
- Cursor: `Extensions: Install from VSIX...`

Chrome local test:

1. Open `chrome://extensions`
2. Enable Developer Mode
3. Click `Load unpacked`
4. Select `extensions/chrome-prompt-engine`

Both clients default to the hosted production endpoint:

```text
https://prompt-engine-mcp-pewnieev4a-el.a.run.app
```

## MCP quick start

Local `stdio` server for Cursor:

```bash
uvx vibe-prompt-engine mcp stdio
```

Local or hosted Streamable HTTP server:

```bash
vibe-prompt-engine mcp http --host 127.0.0.1 --port 8001 --path /mcp
```

The FastAPI app also mounts MCP at `/mcp`, so this works too:

```bash
uvicorn prompt_engine.api.app:app --reload --host 0.0.0.0 --port 8000
```

Then point Cursor to:

- `command: vibe-prompt-engine`
- `args: ["mcp", "stdio"]`

Or point Cursor to:

- `url: http://127.0.0.1:8000/mcp`

You can print ready-to-paste Cursor config:

```bash
vibe-prompt-engine mcp cursor-config --transport stdio
vibe-prompt-engine mcp cursor-config --transport http --url http://127.0.0.1:8000/mcp
```

## Public release strategy

For real public adoption, ship Prompt Engine in two channels:

1. `PyPI` for local `stdio` MCP installs via `uvx` or `pipx`
2. Hosted Streamable HTTP MCP at `https://api.your-domain.com/mcp`

Recommended rollout:

1. Publish Python package to PyPI
2. Publish container image to GHCR
3. Deploy hosted image to Cloud Run
4. Give users either:
   - local config using `uvx vibe-prompt-engine mcp stdio`
   - or hosted config using `https://api.your-domain.com/mcp`

Until PyPI trusted publishing is configured, users can install directly from GitHub:

```bash
uvx --from git+https://github.com/adaline-ankit/prompt-engine vibe-prompt-engine mcp stdio
```

Or with `pipx`:

```bash
pipx install git+https://github.com/adaline-ankit/prompt-engine.git
vibe-prompt-engine mcp stdio
```

Release automation and deployment notes are in [RELEASE.md](RELEASE.md) and [deploy/cloudrun/README.md](deploy/cloudrun/README.md).

## Repository

- GitHub: [adaline-ankit/prompt-engine](https://github.com/adaline-ankit/prompt-engine)
- Package: [vibe-prompt-engine on PyPI](https://pypi.org/project/vibe-prompt-engine/)

## CLI examples

```bash
vibe-prompt-engine run "Refactor this Python function to reduce branching."
vibe-prompt-engine run "Classify each support ticket by severity and return JSON." --json
vibe-prompt-engine run "Summarize this design doc" --run-llm --provider mock --stream
vibe-prompt-engine mcp http --host 127.0.0.1 --port 8001
```

## API examples

Optimize:

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Extract the account owner, ARR, and renewal date from this note.",
    "context": {
      "output_schema": {
        "type": "object",
        "properties": {
          "account_owner": {"type": "string"},
          "arr": {"type": "number"},
          "renewal_date": {"type": "string"}
        },
        "required": ["account_owner", "arr", "renewal_date"]
      }
    }
  }'
```

Run against a provider:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize this incident report in bullet points.",
    "provider": "mock",
    "model": "mock-gpt"
  }'
```

MCP over HTTP is available at:

```text
http://localhost:8000/mcp
```

## SDK examples

Python:

```python
from prompt_engine import PromptOptimizationEngine

engine = PromptOptimizationEngine()
result = engine.optimize_prompt(
    "Extract product names, pricing, and discount terms from this email.",
    context={"output_schema": {"type": "object"}},
)
print(result.final_prompt)
```

TypeScript:

```ts
import { PromptEngineClient } from "./sdk/typescript/src";

const client = new PromptEngineClient({ baseUrl: "http://localhost:8000" });
const result = await client.optimize({
  prompt: "Classify these support tickets by severity.",
});
console.log(result.skills_applied);
```

## Providers

- `mock` works locally with no API key and is used in tests and examples.
- `openai`, `anthropic`, and `openrouter` are implemented behind a common provider contract.
- Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENROUTER_API_KEY` to enable remote execution.

## Plugins

Prompt Engine loads built-in skills and can load external Python skill modules from paths listed in `config/config.yaml`.

See [skills/README.md](skills/README.md) for the contract.

## MCP tools

Prompt Engine exposes these MCP tools:

- `optimize_prompt`
- `optimize_and_run`
- `explain_transformations`
- `suggest_output_schema`
- `list_skills`

It also exposes MCP prompts:

- `optimize_task`
- `extract_json`

## Deployment

- Local development via CLI or `uvicorn`
- Containerized deployment via `Dockerfile` and `docker-compose.yml`
- Cloud-ready for ECS, EKS, Cloud Run, Railway, or any ASGI-compatible platform
