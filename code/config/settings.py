"""
config/settings.py — all simulation parameters in one place.
"""

# __ Schedule _____________________________________________
WORK_HOURS_START = 9     # 09:00
WORK_HOURS_END = 17    # 17:00
SIMULATION_DAYS = 5

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY  = 86400

# data
EMPLOYEE_CSV = "data/employees.csv"


# __ Risk _________________________________________________
SUSPICIOUS_THRESHOLD = 100 

# How much risk each profile adds per tick (1 tick = 1 hour)
RISK_INCREMENT = {
    "normal": 0.5 / 3600,
    "stressed": 1.5 / 3600,
    "malicious": 2.5 / 3600,
}

# __ Email sessions per work hour (fixed, not random) _____
SESSIONS_PER_HOUR = {
    "normal": 2,
    "stressed": 2,
    "malicious": 3,
}

BEHAVIOR_DURATION_SECONDS = {
    # normal email states
    "OPEN_CLIENT": 30,   # open / unlock the client
    "VIEW_INBOX": 60,   # scan subject lines
    "READ_EMAIL": 180,   # read a message          (3 min)
    "COMPOSE": 600,   # write a new email       (10 min)
    "SEARCH": 120,   # search the mailbox      (2 min)
    "DELETE": 20,   # delete a message
    "REPLY": 300,   # compose a reply         (5 min)
    "FORWARD": 60,   # forward with a note
    # suspicious email states
    "CLICK_LINK":  45,
    "FWD_EXTERNAL": 120,
    "LEAK_ATTACH":  180,
    "SEARCH_SENSITIVE": 180,
    # etc_behaviour
    "RESTROOM": 300, # 5-min bathroom break
    "AWAY_DESK": 900, # 15-min away (coffee, chat…)
    # off-hours
    "IDLE": 3_600,   # 1-hour idle block
}

# __ Email state transitions _______________________________
# Normal pathway (suspicious states are locked)
BEHAVIOR_DURATION_SECONDS = {
    # normal
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


# Weights for randomly generating emails in the inbox stack.
EMAIL_CATEGORY_WEIGHTS = {
    "normal": 0.75,
    "phishing": 0.15,
    "malicious": 0.10,
}
INBOX_INITIAL_SIZE = 20  
INBOX_MAX_SIZE = 50

# __ Output ________________________________________________
OUTPUT_CSV = "output/simulation_log.csv"
RANDOM_SEED = 42
