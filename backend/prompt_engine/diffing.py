from __future__ import annotations

from difflib import unified_diff


def build_prompt_diff(original: str, optimized: str) -> str:
    diff = unified_diff(
        original.splitlines(),
        optimized.splitlines(),
        fromfile="original",
        tofile="optimized",
        lineterm="",
    )
    return "\n".join(diff)

