"""
agent/employee.py — one employee agent.

Each tick the agent gains risk. Once risk >= SUSPICIOUS_THRESHOLD,
the email chain can include suspicious states (leaking, clicking bad links, etc.)
"""

import random
from config import settings


class EmployeeAgent:

    def __init__(self, agent_id: str, profile: str, rng: random.Random):
        self.agent_id = agent_id
        self.profile = profile          # "normal" | "stressed" | "malicious"
        self.rng = rng
        self.risk_score = 0.0

    # __ Risk _____________________________________________

    @property
    def is_suspicious(self) -> bool:
        return self.risk_score >= settings.SUSPICIOUS_THRESHOLD

    def increment_risk(self):
        self.risk_score += settings.RISK_INCREMENT[self.profile]

    # __ Email chain _____________________________________

    def _next_state(self, state: str) -> str:
        """Pick the next email state using the appropriate transition table."""
        if self.is_suspicious and state in settings.SUSPICIOUS_TRANSITIONS:
            row = settings.SUSPICIOUS_TRANSITIONS[state]
        else:
            row = settings.NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})

        return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

    def run_email_session(self) -> list[str]:
        """
        Walk through one email session from OPEN_CLIENT to DONE.
        Returns the list of states visited (not including DONE).
        """
        state = "OPEN_CLIENT"
        states = [state]
        while state != "DONE":
            state = self._next_state(state)
            if state != "DONE":
                states.append(state)
        return states

    def sessions_this_hour(self) -> int:
        return settings.SESSIONS_PER_HOUR[self.profile]

    def __repr__(self):
        return f"EmployeeAgent({self.agent_id!r}, {self.profile!r}, risk={self.risk_score:.1f})"
