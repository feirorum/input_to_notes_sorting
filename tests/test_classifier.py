from app.models import Action


def test_entity_routes_to_existing_note(service):
    d = service.explain("Flora's feet are now size 34.")
    assert d.destination == "notes/family/flora.md"
    assert d.decision == Action.APPEND
    assert not d.needs_user_confirmation        # entity makes it obvious
    assert "Clothing and sizes" == d.section


def test_task_is_flagged_and_kept_in_inbox(service):
    d = service.explain("Remind me to buy batteries and milk tomorrow.")
    assert d.decision == Action.ASK
    assert d.needs_user_confirmation
    assert any("task" in r.lower() for r in d.ask_reasons)


def test_sensitive_without_destination_asks(service):
    d = service.explain("My bank account password is hunter2.")
    assert d.needs_user_confirmation
    assert any("sensitive" in r.lower() for r in d.ask_reasons)


def test_podcast_timestamp_detected(service):
    d = service.explain("Practical AI 17:43 — context windows explained.")
    assert d.destination == "notes/podcasts/practical-ai.md"
    assert "17:43" in d.signals["timestamps"]
    # proposed content keeps the timestamp formatting
    assert d.proposed_content.startswith("17:43 —")


def test_scores_are_explained(service):
    d = service.explain("We got input from security on the XYZ project.")
    assert d.scores
    top = d.scores[0]
    assert top.contributions
    assert all(c.explanation for c in top.contributions)
    # entity 'XYZ' should win -> work
    assert d.destination_key == "work"


def test_unknown_goes_to_review(service):
    d = service.explain("qwerty zxcvb asdfg")
    assert d.decision == Action.REVIEW
