"""Correction-example similarity.

When the user corrects a decision we store the (text -> destination) example.
This matcher rewards a candidate destination when the incoming text resembles a
past correction, which is how feedback actually changes future routing — and is
visible in the demo as the "example" matcher score moving after a correction.
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def best_example(text: str, examples: list[dict]) -> dict | None:
    best = None
    best_sim = 0.0
    for ex in examples:
        sim = _similarity(text, ex["text"])
        if sim > best_sim:
            best_sim = sim
            best = ex
    if not best:
        return None
    return {**best, "similarity": round(best_sim, 3)}
