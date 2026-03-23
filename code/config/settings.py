"""
config/settings.py
All simulation parameters in one place.
"""

# ---------------------------------------------------------------------------
# SCHEDULE
# ---------------------------------------------------------------------------
WORK_HOURS_START = 9      # inclusive
WORK_HOURS_END   = 18     # exclusive
SIMULATION_DAYS  = 5
TICKS_PER_HOUR   = 1      # 1 tick = 1 hour

# ---------------------------------------------------------------------------
# RISK THRESHOLD
# Each agent accumulates a risk score each tick.
# Suspicious email actions only unlock once this threshold is crossed.
# ---------------------------------------------------------------------------
SUSPICIOUS_THRESHOLD = 10

# Risk score added per tick, by profile
RISK_INCREMENT = {
    "normal_employee":   0.5,
    "developer":         0.5,
    "stressed_employee": 1.5,
    "malicious_insider": 2.5,
}

# ---------------------------------------------------------------------------
# AGENT PROFILES
# ---------------------------------------------------------------------------
AGENT_PROFILES = {
    "normal_employee": {
        "stress_level":   "low",
        "predisposition": "low",
        "system_role":    "novice",
    },
    "developer": {
        "stress_level":   "low",
        "predisposition": "low",
        "system_role":    "advanced",
    },
    "stressed_employee": {
        "stress_level":   "high",
        "predisposition": "medium",
        "system_role":    "advanced",
    },
    "malicious_insider": {
        "stress_level":   "high",
        "predisposition": "high",
        "system_role":    "advanced",
    },
}

# ---------------------------------------------------------------------------
# EMAIL TRANSITIONS — NORMAL MODE (suspicious pathway locked)
# ---------------------------------------------------------------------------
NORMAL_TRANSITIONS = {
    "OPEN_CLIENT": {
        "VIEW_INBOX":   0.70,
        "COMPOSE_NEW":  0.20,
        "SEARCH_INBOX": 0.10,
    },
    "VIEW_INBOX": {
        "READ_EMAIL":     0.65,
        "FLAG_STAR":      0.10,
        "DELETE_ARCHIVE": 0.15,
        "MOVE_FOLDER":    0.10,
    },
    "READ_EMAIL": {
        "REPLY":       0.45,
        "REPLY_ALL":   0.20,
        "ATTACH_SEND": 0.20,
        "DONE":        0.15,
    },
    "REPLY":          {"DONE": 1.0},
    "REPLY_ALL":      {"DONE": 1.0},
    "ATTACH_SEND":    {"DONE": 1.0},
    "SEARCH_INBOX":   {"DONE": 1.0},
    "COMPOSE_NEW":    {"DONE": 1.0},
    "FLAG_STAR":      {"DONE": 1.0},
    "DELETE_ARCHIVE": {"DONE": 1.0},
    "MOVE_FOLDER":    {"DONE": 1.0},
    "DONE":           {"DONE": 1.0},
}

# ---------------------------------------------------------------------------
# EMAIL TRANSITIONS — SUSPICIOUS MODE (unlocked after threshold)
# Only the states that differ from NORMAL_TRANSITIONS are listed here.
# All other states fall back to NORMAL_TRANSITIONS.
# ---------------------------------------------------------------------------
SUSPICIOUS_TRANSITIONS = {
    "READ_EMAIL": {
        "REPLY":       0.35,
        "REPLY_ALL":   0.15,
        "ATTACH_SEND": 0.15,
        "CLICK_LINK":  0.20,   # [!]
        "DONE":        0.15,
    },
    "REPLY":       {"FWD_EXTERNAL":    0.40, "DONE": 0.60},   # [!]
    "REPLY_ALL":   {"MASS_FWD_BCC":    0.40, "DONE": 0.60},   # [!]
    "ATTACH_SEND": {"DOWNLOAD_ATTACH": 0.40, "DONE": 0.60},   # [!]
    "SEARCH_INBOX":{"SEARCH_SENS_KW":  0.60, "DONE": 0.40},   # [!]
}

# State names that are flagged as suspicious in the output
SUSPICIOUS_STATES = {
    "CLICK_LINK",
    "FWD_EXTERNAL",
    "MASS_FWD_BCC",
    "DOWNLOAD_ATTACH",
    "SEARCH_SENS_KW",
}

# ---------------------------------------------------------------------------
# SESSION FREQUENCY  (Poisson lambda per work hour)
# ---------------------------------------------------------------------------
EMAIL_SESSIONS_PER_HOUR_LAMBDA = {
    "normal_employee":   2,
    "developer":         1,
    "stressed_employee": 2,
    "malicious_insider": 3,
}

# ---------------------------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------------------------
OUTPUT_CSV  = "output/simulation_log.csv"
RANDOM_SEED = 42
