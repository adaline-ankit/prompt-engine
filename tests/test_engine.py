from prompt_engine import PromptOptimizationEngine


def test_optimize_prompt_applies_expected_transformations() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_prompt("Extract company, ARR, and renewal date from this note and return JSON.")

    assert result.intent == "extraction"
    assert "role_injection" in result.skills_applied
    assert "structured_output" in result.skills_applied
    assert "Output Contract:" in result.final_prompt
    assert result.optimization_score.overall > 0


def test_optimize_and_run_with_mock_provider() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_and_run(
        "Summarize this design document in bullet points.",
        provider="mock",
        model="mock-gpt",
    )

    assert result.provider == "mock"
    assert "MOCK_PROVIDER_RESPONSE" in result.provider_output

