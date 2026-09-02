from pathlib import Path

APP_NAME = "EDC System"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "patient_data.db"