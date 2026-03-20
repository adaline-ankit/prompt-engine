from prompt_engine import PromptOptimizationEngine


def test_optimize_prompt_applies_expected_transformations() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_prompt("Extract company, ARR, and renewal date from this note and return JSON.")

    assert result.intent == "extraction"
    assert "role_injection" in result.skills_applied
    assert "best_practice_prompting" in result.skills_applied
    assert "structured_output" in result.skills_applied
    assert "Output Contract:" in result.final_prompt
    assert "<objective>" in result.final_prompt
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


def test_optimizer_rewrites_shorthand_and_injects_context() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_prompt(
        "plz extract company arr and renewl date frm this chat and return json",
        context={
            "conversation_summary": "Customer said Acme renewed for $240000 on 2026-04-01.",
            "page_title": "CRM follow-up",
        },
    )

    assert "renewal date" in result.final_prompt.lower()
    assert "Context:" in result.final_prompt
    assert "conversation_summary" in result.final_prompt
    assert "crm follow-up" in result.final_prompt.lower()
    assert "Refined Request:" in result.final_prompt


def test_optimizer_preserves_source_and_surrounding_context_for_summaries() -> None:
    engine = PromptOptimizationEngine()
    result = engine.optimize_prompt(
        "summrize this for exec update",
        context={
            "selected_text": "Incident started at 09:14 UTC and affected checkout.",
            "surrounding_text": "Mitigation shipped at 09:42 UTC. Follow-up owner: Priya.",
            "audience": "executive team",
        },
    )

    assert result.intent == "summarization"
    assert "executive team" in result.final_prompt.lower()
    assert "follow-up owner" in result.final_prompt.lower()
    assert "<context_block name=\"selected_text\"" in result.final_prompt
