import anyio
from fastapi.testclient import TestClient

from prompt_engine.api.app import create_app
from prompt_engine.mcp.server import build_mcp_server, infer_output_schema
from prompt_engine import PromptOptimizationEngine


def test_mcp_server_exposes_expected_tools_and_prompts() -> None:
    server = build_mcp_server()

    tools = anyio.run(server.list_tools)
    prompts = anyio.run(server.list_prompts)

    tool_names = {tool.name for tool in tools}
    prompt_names = {prompt.name for prompt in prompts}

    assert "optimize_prompt" in tool_names
    assert "optimize_and_run" in tool_names
    assert "explain_transformations" in tool_names
    assert "suggest_output_schema" in tool_names
    assert "list_skills" in tool_names
    assert "optimize_task" in prompt_names
    assert "extract_json" in prompt_names


def test_mcp_optimize_tool_runs_end_to_end() -> None:
    server = build_mcp_server()

    _, result = anyio.run(
        server.call_tool,
        "optimize_prompt",
        {"prompt": "Extract the owner and ARR from this note and return JSON."},
    )

    assert result["intent"] == "extraction"
    assert "structured_output" in result["skills_applied"]
    assert "Output Contract:" in result["final_prompt"]


def test_schema_suggestion_is_grounded_in_intent() -> None:
    engine = PromptOptimizationEngine()
    result = infer_output_schema(engine, "Extract owner, arr, and renewal date from this CRM note.")

    assert result.intent == "extraction"
    assert set(result.inferred_fields) >= {"owner", "arr", "renewal_date"}
    assert result.output_schema["type"] == "object"


def test_api_mounts_mcp_endpoint() -> None:
    with TestClient(create_app(), base_url="http://127.0.0.1") as client:
        response = client.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})

    assert response.status_code != 500
