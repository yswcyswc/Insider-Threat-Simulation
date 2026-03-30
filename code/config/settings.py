"""
config/settings.py — all simulation parameters in one place.
"""

# ── Schedule ─────────────────────────────────────────────
WORK_HOURS_START = 9     # 09:00
WORK_HOURS_END = 17    # 17:00
SIMULATION_DAYS = 5

# ── Risk ─────────────────────────────────────────────────
SUSPICIOUS_THRESHOLD = 100  # normal agents cap at ~60 over 5 days, only stressed/malicious cross this

# How much risk each profile adds per tick (1 tick = 1 hour)
RISK_INCREMENT = {
    "normal": 0.5,
    "stressed": 1.5,
    "malicious": 2.5,
}

# ── Email sessions per work hour (fixed, not random) ─────
SESSIONS_PER_HOUR = {
    "normal": 2,
    "stressed": 2,
    "malicious": 3,
}

# ── Email state transitions ───────────────────────────────
# Normal pathway (suspicious states are locked)
NORMAL_TRANSITIONS = {
    "OPEN_CLIENT": {"VIEW_INBOX": 0.7,  "COMPOSE": 0.2, "SEARCH": 0.1},
    "VIEW_INBOX": {"READ_EMAIL": 0.8,  "DELETE": 0.2},
    "READ_EMAIL": {"REPLY":  0.6,  "FORWARD": 0.2, "DONE": 0.2},
    "COMPOSE": {"DONE": 1.0},
    "SEARCH": {"DONE": 1.0},
    "DELETE": {"DONE": 1.0},
    "REPLY": {"DONE": 1.0},
    "FORWARD": {"DONE": 1.0},
}

# Suspicious pathway (only active after threshold is crossed)
SUSPICIOUS_TRANSITIONS = {
    "READ_EMAIL": {"REPLY": 0.3, "FORWARD": 0.1, "CLICK_LINK": 0.4, "DONE": 0.2},
    "REPLY": {"FWD_EXTERNAL": 0.5, "DONE": 0.5},
    "FORWARD": {"LEAK_ATTACH":  0.5, "DONE": 0.5},
    "SEARCH": {"SEARCH_SENSITIVE": 0.7, "DONE": 0.3},
}

# Which states count as suspicious in the output
SUSPICIOUS_STATES = {"CLICK_LINK", "FWD_EXTERNAL", "LEAK_ATTACH", "SEARCH_SENSITIVE"}

# ── Output ────────────────────────────────────────────────
OUTPUT_CSV = "output/simulation_log.csv"
RANDOM_SEED = 42
