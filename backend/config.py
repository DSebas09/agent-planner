import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parent

# models.py
TASK_TITLE_MAX_LENGTH: int = 200
PRIORITY_MAX_LENGTH: int = 10
ENERGY_LEVEL_MAX_LENGTH: int = 10
TASK_STATUS_MAX_LENGTH: int = 20
AGENT_LOG_TRIGGER_MAX_LENGTH: int = 50
AGENT_LOG_MESSAGE_MAX_LENGTH: int = 1000

# scheduler.py
INTERRUPTION_THRESHOLD: float = 20.0

# database.py
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_BASE_DIR}/agent_planner.db")
