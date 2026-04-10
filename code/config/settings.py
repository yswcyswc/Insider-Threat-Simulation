"""
config/settings.py - all simulation parameters in one place.
"""

from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# __ Schedule _____________________________________________
WORK_HOURS_START = 9     # 09:00
WORK_HOURS_END = 17      # 17:00
SIMULATION_DAYS = 5

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400

# data
EMPLOYEE_CSV = DATA_DIR / "employees.csv"
ACTION_DEFINITIONS_CSV = DATA_DIR / "action_definitions.csv"


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _load_action_definitions(csv_path: Path):
    action_duration_ranges: dict[str, dict[str, tuple[int, int]]] = {}
    suspicious_states: set[str] = set()
    email_sensitive_actions: set[str] = set()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "profile",
            "behavior",
            "min_seconds",
            "max_seconds",
            "is_suspicious",
            "uses_email_multiplier",
        }

        missing = required_columns.difference(reader.fieldnames or [])
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Missing required action definition columns: {missing_list}")

        for row in reader:
            profile = row["profile"].strip()
            behavior = row["behavior"].strip()
            min_seconds = int(row["min_seconds"])
            max_seconds = int(row["max_seconds"])

            if min_seconds > max_seconds:
                raise ValueError(
                    f"Invalid duration range for {profile}/{behavior}: "
                    f"{min_seconds} > {max_seconds}"
                )

            action_duration_ranges.setdefault(profile, {})[behavior] = (
                min_seconds,
                max_seconds,
            )

            if _parse_bool(row["is_suspicious"]):
                suspicious_states.add(behavior)

            if _parse_bool(row["uses_email_multiplier"]):
                email_sensitive_actions.add(behavior)

    if not action_duration_ranges:
        raise ValueError(f"No action definitions loaded from {csv_path}")

    return action_duration_ranges, suspicious_states, email_sensitive_actions


# __ Risk _________________________________________________
SUSPICIOUS_THRESHOLD = 20

# How much risk each profile adds per tick
RISK_INCREMENT = {
    "normal": 0.2,
    "stressed": 0.5,
    "malicious": 0.8,
}

# Very gradual recovery while an agent is idle/off-hours.
IDLE_RISK_RECOVERY_PER_SECOND = 0.000002

# __ Email sessions per work hour __________________________
SESSIONS_PER_HOUR = {
    "normal": 2,
    "stressed": 2,
    "malicious": 3,
}

ACTION_DURATION_RANGES, SUSPICIOUS_STATES, EMAIL_SENSITIVE_ACTIONS = _load_action_definitions(
    ACTION_DEFINITIONS_CSV
)

# Some categories naturally take longer to inspect or handle.
EMAIL_CATEGORY_DURATION_MULTIPLIER = {
    "normal": 1.0,
    "phishing": 1.15,
    "malicious": 1.3,
}

# __ Email state transitions _______________________________
NORMAL_TRANSITIONS = {
    "OPEN_CLIENT": {"VIEW_INBOX": 0.7, "COMPOSE": 0.2, "SEARCH": 0.1},
    "VIEW_INBOX": {"READ_EMAIL": 0.8, "DELETE": 0.2},
    "READ_EMAIL": {"REPLY": 0.6, "FORWARD": 0.2, "DONE": 0.2},
    "COMPOSE": {"DONE": 1.0},
    "SEARCH": {"DONE": 1.0},
    "DELETE": {"DONE": 1.0},
    "REPLY": {"DONE": 1.0},
    "FORWARD": {"DONE": 1.0},
}

SUSPICIOUS_TRANSITIONS = {
    "READ_EMAIL": {"REPLY": 0.3, "FORWARD": 0.1, "CLICK_LINK": 0.4, "DONE": 0.2},
    "REPLY": {"FWD_EXTERNAL": 0.5, "DONE": 0.5},
    "FORWARD": {"LEAK_ATTACH": 0.5, "DONE": 0.5},
    "SEARCH": {"SEARCH_SENSITIVE": 0.7, "DONE": 0.3},
}


# __ Inbox generation _____________________________________
EMAIL_CATEGORY_WEIGHTS = {
    "normal": 0.75,
    "phishing": 0.15,
    "malicious": 0.10,
}
INBOX_INITIAL_SIZE = 20
INBOX_MAX_SIZE = 50

# __ Output ________________________________________________
OUTPUT_CSV = OUTPUT_DIR / "simulation_log.csv"
RANDOM_SEED = 42
