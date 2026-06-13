"""Rule-based, fully explainable classifier.

Runs a set of independent matchers, each of which contributes scored, annotated
votes to destinations. The contributions are summed per destination and handed
to the shared policy. No matcher hides its reasoning — every number you see in
the demo's middle pane comes straight from a MatcherScore here.
"""
from __future__ import annotations

from .. import config
from ..models import Decision, DestinationScore, MatcherScore
from . import base, examples


class RuleClassifier:
    name = "rules"

    def classify(self, capture_id: str, text: str,
                 ctx: base.ClassifierContext) -> Decision:
        contributions: dict[str, list[MatcherScore]] = {}

        def add(ms: MatcherScore) -> None:
            contributions.setdefault(ms.destination_key, []).append(ms)

        # 1) keyword matcher
        for key, msl in base.merge_keyword_scores(text).items():
            for ms in msl:
                add(ms)

        # 2) entity matcher (strongest signal)
        entity_hits = base.find_entities(text, ctx.entities)
        for e in entity_hits:
            add(MatcherScore(
                matcher="entity",
                destination_key=e["destination_key"],
                score=0.6,
                explanation=f"mentions known {e['kind']} '{e['name']}' "
                            f"-> {e['note_path']}",
            ))

        # 3) example-similarity matcher (learned corrections)
        ex = examples.best_example(text, ctx.examples)
        if ex and ex["similarity"] > 0.15:
            add(MatcherScore(
                matcher="example",
                destination_key=ex["destination_key"],
                score=round(min(0.5, ex["similarity"]), 3),
                explanation=f"similar to saved correction '{ex.get('title','')}' "
                            f"({ex['similarity']:.0%})",
            ))

        # 4) podcast matcher
        timestamps = base.find_timestamps(text)
        low = text.lower()
        podcast_signal = ("podcast" in low or "episode" in low or
                          bool(timestamps))
        podcast_session = None
        if podcast_signal:
            base_score = 0.35 + (0.15 if timestamps else 0.0)
            add(MatcherScore(
                matcher="podcast",
                destination_key="podcasts",
                score=round(base_score, 3),
                explanation=("timestamp(s) present" if timestamps
                             else "mentions a podcast/episode"),
            ))
            podcast_session = self._session_hint(text, ctx)

        # --- assemble per-destination totals ---------------------------
        scores: list[DestinationScore] = []
        for key, msl in contributions.items():
            total = round(sum(m.score for m in msl), 3)
            scores.append(DestinationScore(
                destination_key=key,
                label=config.DESTINATIONS_BY_KEY[key].label,
                total=total,
                contributions=msl,
            ))
        scores.sort(key=lambda s: s.total, reverse=True)

        signals = {
            "is_task": base.detect_task(text),
            "is_sensitive": base.detect_sensitive(text),
            "timestamps": timestamps,
            "entities": entity_hits,
            "example_match": ex,
            "podcast_session": podcast_session,
        }
        return base.apply_policy(capture_id, text, scores, ctx,
                                 score_signals=signals)

    @staticmethod
    def _session_hint(text: str, ctx: base.ClassifierContext) -> dict | None:
        """Count recent captures that look like the same podcast session.

        Prototype heuristic: other recent captures that also carry a timestamp.
        A real version would key on podcast title + a time window.
        """
        related = [t for t in ctx.recent_texts
                   if base.find_timestamps(t) and t.strip() != text.strip()]
        if not related:
            return None
        return {"related_timestamped_captures": len(related),
                "hint": "Group with other timestamped notes from this session."}
