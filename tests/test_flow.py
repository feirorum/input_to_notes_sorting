from app.models import Action, CaptureStatus, CorrectIn
from app.storage import vault as vault_mod


def test_capture_then_process_appends_and_audits(service):
    cap = service.capture("Flora's feet are now size 34.", "test", "quick_note")
    assert service.db.get_capture(cap.id)["status"] == "new"

    d = service.process(cap.id)
    assert d.decision == Action.APPEND

    content = vault_mod.read_note("notes/family/flora.md")
    assert "size 34" in content
    assert service.db.get_capture(cap.id)["status"] == CaptureStatus.PROCESSED.value

    audit = service.db.latest_audit_for_capture(cap.id)
    assert audit["undo_available"] == 1


def test_undo_restores_previous_content(service):
    cap = service.capture("Flora's feet are now size 34.", "test", "quick_note")
    before = vault_mod.read_note("notes/family/flora.md")
    service.process(cap.id)
    assert vault_mod.read_note("notes/family/flora.md") != before

    assert service.undo(cap.id) is True
    assert vault_mod.read_note("notes/family/flora.md") == before
    assert service.db.get_capture(cap.id)["status"] == CaptureStatus.NEW.value


def test_correction_learns_example_that_changes_future_scores(service):
    # An ambiguous-ish note the rules wouldn't confidently send to learning.
    text = "Notes on transformers from the meetup."
    cap = service.capture(text, "test", "quick_note")
    service.process(cap.id)

    # Correct it to learning; save as example.
    service.correct(cap.id, CorrectIn(destination_key="learning",
                                      action=Action.CREATE, save_example=True))

    # A similar new note should now pick up an 'example' matcher contribution.
    d = service.explain("More notes on transformers from the meetup today.")
    matchers = {c.matcher for s in d.scores for c in s.contributions}
    assert "example" in matchers


def test_create_new_long_lived_note_asks_when_moderate(service):
    # A new person not in the registry -> would create a long-lived note.
    cap = service.capture("Grandma's birthday is in March.", "test", "quick_note")
    d = service.process(cap.id)
    # Either review or pending, but must not silently auto-create with low conf.
    assert d.needs_user_confirmation
