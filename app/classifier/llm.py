"""LLM-backed classifier behind the same interface as the rule classifier.

Design choice: the LLM only *scores* destinations (and flags task/sensitive).
The deterministic helpers still extract entities/timestamps, and the shared
`apply_policy` still does the routing and ask-rules. That keeps behaviour
consistent across backends and keeps the safety-critical policy out of the model.

Enable with CLASSIFIER=llm (model only) or CLASSIFIER=ensemble (average with
the rule scores). Requires `pip install anthropic` and ANTHROPIC_API_KEY.
"""
from __future__ import annotations

import json

from .. import config
from ..models import Decision, DestinationScore, MatcherScore
from . import base, examples
from .rules import RuleClassifier

_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "description": "destination_key -> relevance score in [0,1]",
            "additionalProperties": {"type": "number"},
        },
        "is_task": {"type": "boolean"},
        "is_sensitive": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["scores", "is_task", "is_sensitive", "reason"],
    "additionalProperties": False,
}


def _system_prompt() -> str:
    lines = ["You classify a short captured note into one knowledge destination.",
             "Destinations (key: description, example keywords):"]
    for d in config.DESTINATIONS:
        lines.append(f"- {d.key}: {d.label} ({', '.join(d.keywords[:6])})")
    lines.append(
        "Return a relevance score in [0,1] for each plausible destination key, "
        "plus whether the note is a task/reminder and whether it is sensitive. "
        "Score only keys that are relevant; omit the rest. Be decisive: a clear "
        "note should have one destination near 0.9.")
    return "\n".join(lines)


class LLMClassifier:
    name = "llm"

    def __init__(self, ensemble: bool = False):
        self.ensemble = ensemble
        self._rules = RuleClassifier()
        try:
            import anthropic  # noqa: F401
            self._client = anthropic.Anthropic()
        except Exception as exc:  # pragma: no cover - depends on env
            self._client = None
            self._init_error = exc

    def classify(self, capture_id: str, text: str,
                 ctx: base.ClassifierContext) -> Decision:
        if self._client is None:
            # Fail safe: fall back to rules rather than erroring the request.
            return self._rules.classify(capture_id, text, ctx)

        try:
            data = self._call_model(text)
        except Exception:
            return self._rules.classify(capture_id, text, ctx)

        llm_scores: dict[str, float] = {
            k: float(v) for k, v in data.get("scores", {}).items()
            if k in config.DESTINATIONS_BY_KEY
        }

        # Deterministic signals stay deterministic.
        entity_hits = base.find_entities(text, ctx.entities)
        timestamps = base.find_timestamps(text)
        ex = examples.best_example(text, ctx.examples)

        if self.ensemble:
            combined = self._ensemble_scores(text, llm_scores, entity_hits, ex)
        else:
            combined = self._llm_only_scores(llm_scores, entity_hits, ex,
                                             data.get("reason", ""))

        signals = {
            "is_task": bool(data.get("is_task")) or base.detect_task(text),
            "is_sensitive": bool(data.get("is_sensitive"))
            or base.detect_sensitive(text),
            "timestamps": timestamps,
            "entities": entity_hits,
            "example_match": ex,
            "podcast_session": None,
        }
        return base.apply_policy(capture_id, text, combined, ctx,
                                 score_signals=signals)

    # --- internals ------------------------------------------------------
    def _call_model(self, text: str) -> dict:
        resp = self._client.messages.create(
            model=config.settings.llm_model,
            max_tokens=1024,
            system=_system_prompt(),
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
            messages=[{"role": "user", "content": text}],
        )
        out = next((b.text for b in resp.content if b.type == "text"), "{}")
        return json.loads(out)

    def _llm_only_scores(self, llm_scores, entity_hits, ex, reason
                         ) -> list[DestinationScore]:
        contrib: dict[str, list[MatcherScore]] = {}
        for key, val in llm_scores.items():
            contrib.setdefault(key, []).append(MatcherScore(
                matcher="llm", destination_key=key, score=round(val, 3),
                explanation=reason[:120] or "model relevance score"))
        self._add_entity_example(contrib, entity_hits, ex)
        return self._to_scores(contrib)

    def _ensemble_scores(self, text, llm_scores, entity_hits, ex
                         ) -> list[DestinationScore]:
        contrib: dict[str, list[MatcherScore]] = {}
        for key, msl in base.merge_keyword_scores(text).items():
            contrib.setdefault(key, []).extend(msl)
        for key, val in llm_scores.items():
            contrib.setdefault(key, []).append(MatcherScore(
                matcher="llm", destination_key=key, score=round(val * 0.6, 3),
                explanation="model relevance (weighted 0.6 in ensemble)"))
        self._add_entity_example(contrib, entity_hits, ex)
        return self._to_scores(contrib)

    @staticmethod
    def _add_entity_example(contrib, entity_hits, ex):
        for e in entity_hits:
            contrib.setdefault(e["destination_key"], []).append(MatcherScore(
                matcher="entity", destination_key=e["destination_key"],
                score=0.6,
                explanation=f"known {e['kind']} '{e['name']}'"))
        if ex and ex["similarity"] > 0.15:
            contrib.setdefault(ex["destination_key"], []).append(MatcherScore(
                matcher="example", destination_key=ex["destination_key"],
                score=round(min(0.5, ex["similarity"]), 3),
                explanation=f"similar saved correction ({ex['similarity']:.0%})"))

    @staticmethod
    def _to_scores(contrib) -> list[DestinationScore]:
        scores = [DestinationScore(
            destination_key=k,
            label=config.DESTINATIONS_BY_KEY[k].label,
            total=round(sum(m.score for m in msl), 3),
            contributions=msl,
        ) for k, msl in contrib.items()]
        scores.sort(key=lambda s: s.total, reverse=True)
        return scores
