# This script is intended to be run once a day by launchd (see edu.aol.slack-reminders.plist).
# 		.venv/bin/python -m scripts.send_slack_reminders
# 		.venv/bin/python -m scripts.send_slack_reminders --dry-run
# It queues a Slack reminder 14, 7, and 1 day before every appointment. Slack holds the
# queued messages and posts them on the right day, even if this computer is off then.

import argparse
from datetime import datetime

from app.database.migrations.runner import run_migrations
from app.services.slack_reminders import SLACK_CHANNEL, planned_reminders, schedule_reminders


def _print_reminders(title: str, reminders: list[tuple[int, str]]) -> None:
	print(f"{title}: {len(reminders)}")
	for post_at, text in reminders:
		print(f"  {datetime.fromtimestamp(post_at):%Y-%m-%d %H:%M}  {text}")


def main() -> None:
	parser = argparse.ArgumentParser(description="Queue upcoming appointment reminders in Slack.")
	parser.add_argument("--dry-run", action="store_true", help="Print the planned reminders without contacting Slack.")
	args = parser.parse_args()

	run_migrations()
	print(f"[{datetime.now():%Y-%m-%d %H:%M}] Syncing appointment reminders for {SLACK_CHANNEL}")

	if args.dry_run:
		_print_reminders("Dry run, reminders that should be queued", planned_reminders())
		return

	result = schedule_reminders()
	_print_reminders("Newly scheduled", result["scheduled"])
	_print_reminders("Already queued", result["already_queued"])
	_print_reminders("Cancelled (date changed or patient removed)", result["cancelled"])
	if result["failed"]:
		_print_reminders("FAILED", result["failed"])


if __name__ == "__main__":
	main()
