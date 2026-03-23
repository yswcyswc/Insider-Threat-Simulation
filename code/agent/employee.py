"""
agent/employee.py
Each agent accumulates a risk score each tick.
Suspicious email transitions are locked until the score crosses SUSPICIOUS_THRESHOLD.
"""

import math
import random
from config import settings


def _poisson_sample(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm for sampling from a Poisson distribution."""
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= rng.random()
    return max(0, k - 1)


class EmployeeAgent:

    def __init__(self, agent_id: str, profile_name: str, rng: random.Random):
        if profile_name not in settings.AGENT_PROFILES:
            raise ValueError(f"Unknown profile: {profile_name!r}")

        self.agent_id     = agent_id
        self.profile_name = profile_name
        self.rng          = rng

        self.risk_score   = 0.0
        self._state       = "DONE"

    # ------------------------------------------------------------------
    # Risk threshold
    # ------------------------------------------------------------------

    @property
    def threshold_crossed(self) -> bool:
        return self.risk_score >= settings.SUSPICIOUS_THRESHOLD

    def increment_risk(self) -> None:
        inc = settings.RISK_INCREMENT.get(self.profile_name, 0.5)
        self.risk_score += inc

    # ------------------------------------------------------------------
    # Transition table — switches based on threshold
    # ------------------------------------------------------------------

    def _get_transitions(self, state: str) -> dict:
        """
        Return the transition row for the current state.
        If the threshold is crossed AND a suspicious override exists, use it.
        Otherwise use the normal table.
        """
        if self.threshold_crossed and state in settings.SUSPICIOUS_TRANSITIONS:
            return settings.SUSPICIOUS_TRANSITIONS[state]
        return settings.NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})

    # ------------------------------------------------------------------
    # Email chain
    # ------------------------------------------------------------------

    def _step(self) -> str:
        if self._state == "DONE":
            return "DONE"
        row    = self._get_transitions(self._state)
        states = list(row.keys())
        probs  = list(row.values())
        self._state = self.rng.choices(states, weights=probs, k=1)[0]
        return self._state

    def run_email_chain(self) -> list[dict]:
        """
        Run one full email session from OPEN_CLIENT to DONE.
        Returns a list of step dicts (DONE excluded).
        """
        self._state = "OPEN_CLIENT"
        steps = [{"state": self._state,
                  "suspicious": self._state in settings.SUSPICIOUS_STATES}]
        while self._state != "DONE":
            self._step()
            if self._state != "DONE":
                steps.append({
                    "state":     self._state,
                    "suspicious": self._state in settings.SUSPICIOUS_STATES,
                })
        return steps

    def sessions_this_hour(self) -> int:
        lam = settings.EMAIL_SESSIONS_PER_HOUR_LAMBDA.get(self.profile_name, 1)
        return _poisson_sample(lam, self.rng)

    def __repr__(self) -> str:
        return (f"EmployeeAgent({self.agent_id!r}, {self.profile_name!r}, "
                f"risk={self.risk_score:.1f}, "
                f"unlocked={self.threshold_crossed})")
