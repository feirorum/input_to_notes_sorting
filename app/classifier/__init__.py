"""Classifier package: explainable rule-based scoring + optional LLM backend.

Public entry point: build_classifier(settings) -> Classifier with .classify().
"""
from __future__ import annotations

from .. import config
from .base import Classifier, ClassifierContext  # noqa: F401
from .rules import RuleClassifier


def build_classifier(kind: str | None = None) -> "Classifier":
    kind = (kind or config.settings.classifier).lower()
    if kind == "rules":
        return RuleClassifier()
    if kind in ("llm", "ensemble"):
        # Imported lazily so the `anthropic` package is only required when used.
        from .llm import LLMClassifier
        return LLMClassifier(ensemble=(kind == "ensemble"))
    raise ValueError(f"unknown classifier kind: {kind}")
