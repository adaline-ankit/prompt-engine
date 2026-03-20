from __future__ import annotations

import re
from typing import Any

from prompt_engine.models import PromptContextBlock, PromptState, TransformationStep


_SHORTHAND_REPLACEMENTS = {
    "plz": "please",
    "pls": "please",
    "thx": "thanks",
    "u": "you",
    "ur": "your",
    "w/": "with",
    "w/o": "without",
    "frm": "from",
    "ctx": "context",
    "msg": "message",
    "txt": "text",
    "req": "request",
    "promt": "prompt",
    "propt": "prompt",
    "reponse": "response",
    "respose": "response",
    "renewl": "renewal",
    "summrize": "summarize",
}

_ACRONYMS = {
    "ai": "AI",
    "api": "API",
    "arr": "ARR",
    "csv": "CSV",
    "json": "JSON",
    "llm": "LLM",
    "qa": "QA",
    "sql": "SQL",
    "ui": "UI",
    "ux": "UX",
    "xml": "XML",
}

_CONTEXT_DESCRIPTIONS = {
    "conversation_summary": "Recent conversation summary",
    "chat_context": "Recent chat window context",
    "conversation_history": "Conversation history",
    "selected_text": "Currently selected text",
    "surrounding_text": "Nearby text around the selection",
    "workspace_context": "Workspace or project context",
    "editor_language": "Active editor language",
    "file_path": "Active file path",
    "page_title": "Browser page title",
    "page_url": "Browser page URL",
    "window_title": "Application window title",
    "user_profile": "User profile or persona",
    "reference_material": "Reference material",
}

_CONFIG_ONLY_KEYS = {
    "api_base_url",
    "audience",
    "detail_level",
    "grounding_mode",
    "include_surrounding_context",
    "inline_toolbar_enabled",
    "output_style",
    "reasoning_depth",
    "structure_preference",
    "tone",
    "use_xml_tags",
    "verbosity",
}


class PromptRefiner:
    def refine(self, state: PromptState, context: dict[str, Any]) -> PromptState:
        normalized_prompt = self._normalize_text(state.sanitized_prompt)
        if normalized_prompt != state.sanitized_prompt:
            state.transformations.append(
                TransformationStep(
                    name="language_normalization",
                    kind="rewrite",
                    description="Normalizes shorthand, capitalization, and punctuation in the source request.",
                    before=state.sanitized_prompt,
                    after=normalized_prompt,
                )
            )
            state.sanitized_prompt = normalized_prompt

        refined_prompt = self._refine_request(normalized_prompt, state.intent)
        state.refined_prompt = refined_prompt
        if refined_prompt != normalized_prompt:
            state.transformations.append(
                TransformationStep(
                    name="request_refinement",
                    kind="rewrite",
                    description="Rewrites the request into clearer, grammar-correct prompt language.",
                    before=normalized_prompt,
                    after=refined_prompt,
                )
            )

        goal = self._refine_goal(state.goal or refined_prompt, state.intent)
        if goal != state.goal:
            state.transformations.append(
                TransformationStep(
                    name="goal_reframing",
                    kind="rewrite",
                    description="Reframes the user's task as a direct, execution-ready objective.",
                    before=state.goal or None,
                    after=goal,
                )
            )
            state.goal = goal

        self._add_best_practice_defaults(state, context)
        self._add_context_blocks(state, context)
        self._add_missing_info_guidance(state, context)
        return state

    def _normalize_text(self, prompt: str) -> str:
        normalized = prompt.replace("\r\n", "\n")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()

        for source, target in _SHORTHAND_REPLACEMENTS.items():
            normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized, flags=re.IGNORECASE)

        words = []
        for token in normalized.split():
            plain = token.rstrip(".,:;!?")
            suffix = token[len(plain) :]
            replacement = _ACRONYMS.get(plain.lower())
            words.append(f"{replacement or plain}{suffix}")
        normalized = " ".join(words)

        if normalized and normalized[0].islower():
            normalized = normalized[0].upper() + normalized[1:]
        if normalized and normalized[-1] not in ".!?":
            normalized = f"{normalized}."
        return normalized

    def _refine_request(self, prompt: str, intent: str) -> str:
        refined = re.sub(r"\b(can you|could you|would you)\b", "", prompt, flags=re.IGNORECASE)
        refined = re.sub(r"\bI need you to\b", "", refined, flags=re.IGNORECASE).strip()
        refined = re.sub(r"\bplease\b\s*", "", refined, flags=re.IGNORECASE).strip()
        refined = refined[:1].upper() + refined[1:] if refined else prompt

        if intent == "extraction" and not re.search(r"\bextract\b", refined, flags=re.IGNORECASE):
            refined = f"Extract the requested fields from the provided input. {refined}"
        elif intent == "summarization" and not re.search(r"\bsummarize\b", refined, flags=re.IGNORECASE):
            refined = f"Summarize the provided material clearly and concisely. {refined}"
        elif intent == "classification" and not re.search(r"\bclassif", refined, flags=re.IGNORECASE):
            refined = f"Classify the provided input according to the requested labels. {refined}"
        elif intent == "coding" and not re.search(r"\b(code|implement|refactor|debug|fix)\b", refined, flags=re.IGNORECASE):
            refined = f"Produce the requested code-focused result. {refined}"

        refined = re.sub(r"\s+", " ", refined).strip()
        if refined and refined[-1] not in ".!?":
            refined = f"{refined}."
        return refined

    def _refine_goal(self, goal: str, intent: str) -> str:
        refined = self._normalize_text(goal)
        if intent == "extraction":
            refined = re.sub(r"\breturn json\b", "return a JSON object", refined, flags=re.IGNORECASE)
            if "provided input" not in refined.lower() and "note" not in refined.lower():
                refined = f"{refined.rstrip('.')} using only the provided input."
        elif intent == "classification":
            refined = f"{refined.rstrip('.')} Use only labels supported by the provided criteria."
        elif intent == "summarization":
            refined = f"{refined.rstrip('.')} Preserve the key facts, decisions, and risks."
        elif intent in {"coding", "agent_task"}:
            refined = f"{refined.rstrip('.')} Make the result implementation-ready."
        elif intent == "reasoning":
            refined = f"{refined.rstrip('.')} Be explicit about assumptions and tradeoffs."
        return refined

    def _add_best_practice_defaults(self, state: PromptState, context: dict[str, Any]) -> None:
        self._append_unique(
            state.instructions,
            "Start from the objective, then follow constraints, context, examples, and the output contract in that order.",
        )
        self._append_unique(
            state.instructions,
            "Use direct, precise language and remove ambiguity, filler, and duplicated guidance.",
        )
        self._append_unique(
            state.instructions,
            "Ground the answer in the supplied input and surrounding context instead of relying on unstated assumptions.",
        )
        self._append_unique(
            state.instructions,
            "If critical information is missing, ask a concise clarifying question or state the exact gap.",
        )
        if state.examples:
            self._append_unique(
                state.instructions,
                "Follow the examples for structure and level of detail, but do not copy their content verbatim.",
            )
        if context.get("output_schema"):
            self._append_unique(
                state.instructions,
                "Treat the provided schema as authoritative and match it exactly.",
            )

    def _add_context_blocks(self, state: PromptState, context: dict[str, Any]) -> None:
        blocks = list(state.context_blocks)

        for key, value in context.items():
            if value in (None, "", [], {}):
                continue
            if key in {"examples", "output_schema", "fallback_providers", "tools", "intent_hint"} | _CONFIG_ONLY_KEYS:
                continue
            block = self._coerce_context_block(key, value)
            if block is not None:
                blocks.append(block)

        unique_blocks: list[PromptContextBlock] = []
        seen: set[tuple[str, str]] = set()
        for block in blocks:
            fingerprint = (block.name, block.content)
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_blocks.append(block)

        if unique_blocks != state.context_blocks:
            state.context_blocks = unique_blocks
            state.transformations.append(
                TransformationStep(
                    name="context_enrichment",
                    kind="analysis",
                    description="Adds structured context blocks from the editor, browser, and request metadata.",
                    after=", ".join(block.name for block in unique_blocks) or None,
                )
            )

    def _coerce_context_block(self, key: str, value: Any) -> PromptContextBlock | None:
        if isinstance(value, str):
            content = value.strip()
        elif isinstance(value, list):
            content = "\n".join(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            content = "\n".join(f"{name}: {item}" for name, item in value.items() if item not in (None, "", [], {}))
        else:
            content = str(value).strip()

        if not content:
            return None

        name = key.lower().replace(" ", "_")
        return PromptContextBlock(
            name=name,
            content=content[:4000],
            description=_CONTEXT_DESCRIPTIONS.get(name),
        )

    def _add_missing_info_guidance(self, state: PromptState, context: dict[str, Any]) -> None:
        if not state.context_blocks and state.intent in {"summarization", "extraction", "classification"}:
            self._append_unique(
                state.missing_info,
                "No supporting source content was supplied; surrounding conversation or source text may be required.",
            )

        if not context.get("audience") and state.intent in {"summarization", "reasoning", "conversational"}:
            self._append_unique(
                state.missing_info,
                "Audience is not specified; tone and level of detail may need adjustment.",
            )

    def _append_unique(self, values: list[str], item: str) -> None:
        if item not in values:
            values.append(item)
