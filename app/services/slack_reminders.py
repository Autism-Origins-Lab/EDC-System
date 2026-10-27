"""Slack appointment reminders, queued in Slack by the daily scheduled job.

Reminders are scheduled with Slack's chat.scheduleMessage, so Slack posts them
at REMINDER_TIME on the right day even if this computer is off at that moment.
"""

from datetime import date, datetime, time, timedelta

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.config import SLACK_BOT_TOKEN
from app.database.repositories.patients import list_patients

SLACK_CHANNEL = "#tech-ras"
REMINDER_MESSAGES = {
    14: "Reminder: Patient {} has an appointment in 14 days.",
    7: "Reminder: Patient {} has an appointment in 7 days.",
    1: "Reminder: Patient {} has an appointment tomorrow.",
}
REMINDER_PREFIX = "Reminder: Patient "  # only scheduled messages starting with this are ever cancelled
REMINDER_TIME = time(12, 30)  
SLACK_MAX_DAYS_AHEAD = 120  # Slack rejects messages scheduled further out than this
DATE_FMT = ["%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"]

client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None


def parse_date(value: str) -> datetime | None:
    value = value.strip()
    for fmt in DATE_FMT:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def due_reminders(today: date | None = None) -> list[str]:
    """Return the reminder messages due today, without sending anything."""
    today = today or date.today()
    messages = []
    for patient in list_patients():
        scheduled = parse_date(patient["schedule_date"] or "")
        if scheduled is None:
            continue
        template = REMINDER_MESSAGES.get((scheduled.date() - today).days)
        if template is not None:
            messages.append(template.format(patient["subject_id"]))
    return messages


def planned_reminders(now: datetime | None = None) -> list[tuple[int, str]]:
    """Return (post_at unix time, message) for every reminder Slack can be asked to post."""
    now = now or datetime.now()
    latest = now + timedelta(days=SLACK_MAX_DAYS_AHEAD)
    planned = []
    for patient in list_patients():
        scheduled = parse_date(patient["schedule_date"] or "")
        if scheduled is None:
            continue
        for days_before, template in REMINDER_MESSAGES.items():
            post_at = datetime.combine(scheduled.date() - timedelta(days=days_before), REMINDER_TIME)
            if now < post_at <= latest:
                planned.append((int(post_at.timestamp()), template.format(patient["subject_id"])))
    return sorted(planned)


def _queued_reminders() -> dict[tuple[int, str], dict]:
    """Return this app's reminders already queued in Slack, keyed by (post_at, text)."""
    queued = {}
    cursor = None
    while True:
        response = client.chat_scheduledMessages_list(cursor=cursor, limit=100)
        for message in response["scheduled_messages"]:
            if message["text"].startswith(REMINDER_PREFIX):
                queued[(message["post_at"], message["text"])] = message
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return queued


def schedule_reminders(now: datetime | None = None) -> dict[str, list[tuple[int, str]]]:
    """Queue missing reminders in Slack and cancel ones that no longer match an appointment."""
    result = {"scheduled": [], "already_queued": [], "cancelled": [], "failed": []}
    if client is None:
        print("SLACK_BOT_TOKEN is not set; no reminders scheduled.")
        return result

    planned = set(planned_reminders(now))
    queued = _queued_reminders()

    for key, message in queued.items():
        if key in planned:
            result["already_queued"].append(key)
            continue
        try:  # date changed or patient removed since this was queued
            client.chat_deleteScheduledMessage(channel=message["channel_id"], scheduled_message_id=message["id"])
            result["cancelled"].append(key)
        except SlackApiError as e:
            print(f"Error cancelling {key[1]!r}: {e.response['error']}")
            result["failed"].append(key)

    for key in sorted(planned - queued.keys()):
        post_at, text = key
        try:
            client.chat_scheduleMessage(channel=SLACK_CHANNEL, text=text, post_at=post_at)
            result["scheduled"].append(key)
        except SlackApiError as e:
            print(f"Error scheduling {text!r}: {e.response['error']}")
            result["failed"].append(key)

    return result
