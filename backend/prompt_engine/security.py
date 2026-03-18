from __future__ import annotations

import re


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b")
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def sanitize_text(text: str) -> str:
    return _CONTROL_CHARS.sub("", text).strip()


def mask_pii(text: str) -> str:
    masked = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    masked = _PHONE_RE.sub("[REDACTED_PHONE]", masked)
    return _CARD_RE.sub("[REDACTED_CARD]", masked)

