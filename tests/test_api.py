from fastapi.testclient import TestClient

from prompt_engine.api.app import create_app


def test_optimize_endpoint_returns_prompt_metadata() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/optimize",
        json={
            "prompt": "Extract the owner and ARR from this note and return JSON.",
            "context": {"conversation_summary": "Owner is Dana. ARR is $120000."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "extraction"
    assert "structured_output" in body["skills_applied"]
    assert "Output Contract:" in body["final_prompt"]
    assert "Context:" in body["final_prompt"]
    assert "conversation_summary" in body["final_prompt"]


def test_run_endpoint_uses_mock_provider() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/run",
        json={
            "prompt": "Summarize this incident report.",
            "provider": "mock",
            "model": "mock-gpt",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert "MOCK_PROVIDER_RESPONSE" in body["provider_output"]
