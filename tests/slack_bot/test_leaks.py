from datetime import datetime

from app.database.repositories.forms import save_telephone_screening
from app.database.repositories.patients import create_patient, update_patient
from app.services import slack_reminders


def test_schedule_date_attacks_never_leak_birthday(temp_database, monkeypatch):
    """Malicious schedule dates must never get a patient's date of birth into a Slack reminder."""
    birthday = "2021-03-14"
    now = datetime(2026, 11, 17, 8, 0)
    payloads = [
        birthday,                                   # the DOB typed in as the schedule date
        "03/14/21",                                 # same, in another accepted format
        "2021-03-14 00:00:00.000000",               # same, with a time attached
        "{date_of_birth}",                          # format-string tricks
        "{0[date_of_birth]}",
        "%(date_of_birth)s",
        "' || (SELECT date_of_birth FROM patients) || '",                     # SQL injection
        "2026-12-01'; UPDATE patients SET subject_id = date_of_birth; --",
    ]

    for i, payload in enumerate(payloads):
        patient_id = create_patient(f"ATTACK-{i:02d}")
        update_patient(patient_id, {"date_of_birth": birthday})
        save_telephone_screening(patient_id, {"schedule_date": payload})
    control_id = create_patient("CONTROL-01")  # proves reminders really are being produced
    update_patient(control_id, {"date_of_birth": birthday})
    save_telephone_screening(control_id, {"schedule_date": "2026-12-01"})

    class RecordingSlack:
        def __init__(self):
            self.sent = []

        def chat_scheduledMessages_list(self, **_):
            return {"scheduled_messages": [], "response_metadata": {}}

        def chat_scheduleMessage(self, *, text, post_at, **_):
            self.sent.append((post_at, text))
            return {"ok": True}

    fake = RecordingSlack()
    monkeypatch.setattr(slack_reminders, "client", fake)
    slack_reminders.schedule_reminders(now=now)

    texts = [text for _, text in fake.sent]
    assert any("CONTROL-01" in text for text in texts), "no reminders sent, so the test proves nothing"

    leak_patterns = ["2021-03-14", "03/14/21", "03/14/2021", "3/14", "2021"]
    for post_at, text in fake.sent:
        assert not any(p in text for p in leak_patterns), f"birthday leaked in message: {text!r}"
        send_day = datetime.fromtimestamp(post_at).date()
        assert abs((send_day - datetime(2021, 3, 14).date()).days) > 14, f"send time reveals birthday: {text!r}"
