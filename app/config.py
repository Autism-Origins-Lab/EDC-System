import os
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "AOL Database"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "patient_data.db"
PREFERENCES_PATH = DATA_DIR / "preferences.json"

load_dotenv(PROJECT_ROOT / ".env")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
