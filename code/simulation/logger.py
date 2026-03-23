"""
simulation/logger.py
Collects events and writes CSV.

Columns:
  tick, day, hour, time_label, period,
  agent_id, profile, risk_score, threshold_crossed,
  session_id, chain_step, behavior, suspicious
"""

import csv
import os
from config import settings


class EventLogger:

    COLUMNS = [
        "tick", "day", "hour", "time_label", "period",
        "agent_id", "profile", "risk_score", "threshold_crossed",
        "session_id", "chain_step", "behavior", "suspicious",
    ]

    def __init__(self):
        self._rows: list[dict] = []

    def log(self, snap: dict, agent, session_id: int,
            chain_step: int, behavior: str, suspicious: bool) -> None:
        self._rows.append({
            "tick":              snap["tick"],
            "day":               snap["day"],
            "hour":              snap["hour"],
            "time_label":        snap["time_label"],
            "period":            "work_hours" if snap["is_work_hours"] else "off_hours",
            "agent_id":          agent.agent_id,
            "profile":           agent.profile_name,
            "risk_score":        round(agent.risk_score, 1),
            "threshold_crossed": agent.threshold_crossed,
            "session_id":        session_id,
            "chain_step":        chain_step,
            "behavior":          behavior,
            "suspicious":        suspicious,
        })

    def to_csv(self, path: str | None = None) -> str:
        out = path or settings.OUTPUT_CSV
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(self._rows)
        return os.path.abspath(out)

    def summary(self) -> dict:
        total      = len(self._rows)
        suspicious = sum(1 for r in self._rows if r["suspicious"])
        by_profile: dict = {}
        for r in self._rows:
            p = r["profile"]
            by_profile.setdefault(p, {"total": 0, "suspicious": 0})
            by_profile[p]["total"] += 1
            if r["suspicious"]:
                by_profile[p]["suspicious"] += 1
        return {"total_events": total, "suspicious_events": suspicious,
                "by_profile": by_profile}

    @property
    def rows(self) -> list[dict]:
        return list(self._rows)
