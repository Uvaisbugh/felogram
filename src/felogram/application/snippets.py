from __future__ import annotations

import re


def format_snippet(code: str, language: str = "") -> str:
    """Create a lossless fenced snippet for copying into a message draft."""
    language = language.strip()
    if language and re.fullmatch(r"[A-Za-z0-9_+.#-]+", language) is None:
        raise ValueError("Use a language name without spaces or backticks.")
    if not code.strip():
        raise ValueError("Enter some code first.")
    longest_run = max((len(run) for run in re.findall(r"`+", code)), default=0)
    fence = "`" * max(3, longest_run + 1)
    separator = "" if code.endswith("\n") else "\n"
    return f"{fence}{language}\n{code}{separator}{fence}"
