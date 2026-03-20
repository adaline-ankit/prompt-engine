from __future__ import annotations

from collections.abc import Callable
from typing import Any

from prompt_engine.models import IntentPrediction, IntentType


IntentClassifier = Callable[[str, dict[str, Any]], IntentPrediction | None]


class HybridIntentDetector:
    def __init__(self, classifier: IntentClassifier | None = None, llm_threshold: float = 0.45) -> None:
        self.classifier = classifier
        self.llm_threshold = llm_threshold

    def detect(self, prompt: str, context: dict[str, Any] | None = None) -> IntentPrediction:
        context = context or {}

        hinted_intent = context.get("intent_hint")
        if hinted_intent in _KNOWN_INTENTS:
            return IntentPrediction(
                intent=hinted_intent,
                confidence=0.99,
                method="context_hint",
                candidates={hinted_intent: 0.99},
            )

        scores = {intent: 0.0 for intent in _INTENT_ORDER if intent != "unknown"}
        lowered = f"{prompt}\n{context}".lower()
        for source, target in _PROMPT_NORMALIZATIONS.items():
            lowered = lowered.replace(source, target)

        for intent, keywords in _INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in lowered:
                    scores[intent] += 1.0

        if context.get("output_schema"):
            scores["extraction"] += 1.5
            scores["classification"] += 0.5
        if "```" in prompt or "def " in lowered or "class " in lowered:
            scores["coding"] += 2.0
        if any(token in lowered for token in ("return json", "return a json", "extract", "fields", "schema")):
            scores["extraction"] += 1.0
        if any(token in lowered for token in ("summarize", "summary", "recap", "brief")):
            scores["summarization"] += 0.8
        if any(token in lowered for token in ("exec update", "status update", "key updates")):
            scores["summarization"] += 0.6
        if any(token in lowered for token in ("classify", "label", "sentiment", "severity")):
            scores["classification"] += 0.8
        if any(token in lowered for token in ("analyze", "compare", "tradeoff", "reason")):
            scores["reasoning"] += 0.8
        if context.get("channel") == "agent":
            scores["agent_task"] += 2.0
        if context.get("tools"):
            scores["tool_usage"] += 2.0
        if any(key in context for key in ("chat_context", "conversation_summary", "selected_text", "surrounding_text")):
            scores["summarization"] += 0.25
            scores["extraction"] += 0.25

        selected_intent, selected_score = max(scores.items(), key=lambda item: item[1], default=("conversational", 0.0))
        total_score = sum(scores.values())
        confidence = round(selected_score / total_score, 3) if total_score else 0.35

        rule_prediction = IntentPrediction(
            intent=selected_intent if selected_score > 0 else "conversational",
            confidence=confidence,
            method="rules",
            candidates={key: round(value, 3) for key, value in scores.items() if value > 0},
        )

        if self.classifier and rule_prediction.confidence < self.llm_threshold:
            llm_prediction = self.classifier(prompt, context)
            if llm_prediction is not None:
                llm_prediction.method = "rules+llm"
                return llm_prediction

        return rule_prediction


_PROMPT_NORMALIZATIONS = {
    "summrize": "summarize",
    "renewl": "renewal",
    "frm": "from",
    "plz": "please",
}

_INTENT_ORDER: tuple[IntentType, ...] = (
    "coding",
    "reasoning",
    "classification",
    "extraction",
    "summarization",
    "agent_task",
    "tool_usage",
    "conversational",
    "unknown",
)

_KNOWN_INTENTS: set[IntentType] = set(_INTENT_ORDER)

_INTENT_KEYWORDS: dict[IntentType, tuple[str, ...]] = {
    "coding": ("bug", "code", "function", "api", "sql", "refactor", "typescript", "python", "javascript", "debug"),
    "reasoning": ("analyze", "compare", "why", "reason", "tradeoff", "derive", "evaluate", "pros and cons"),
    "classification": ("classify", "category", "label", "sentiment", "severity", "tag this"),
    "extraction": ("extract", "parse", "fields", "entities", "pull out", "return json", "structured data"),
    "summarization": ("summarize", "summary", "recap", "tl;dr", "brief", "key points", "exec update"),
    "agent_task": ("create", "modify", "implement", "build", "deploy", "write file", "ship", "release"),
    "tool_usage": ("tool", "function call", "browser", "search", "lookup", "call the api"),
    "conversational": ("hello", "thanks", "how are you"),
    "unknown": tuple(),
}
