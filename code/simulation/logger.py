import csv
import os
from config import settings


class EventLogger:

    COLUMNS = [
        "tick", "day", "hour", "minute", "second", "period",
        "agent_id", "profile", "risk_score", "is_suspicious",
        "session", "behavior", "duration_seconds",
        "channel", "artifact_kind", "artifact_id", "artifact_category",
        "sender", "recipient", "flagged",
    ]

    def __init__(self):
        self.rows: list[dict] = []

    def log(self, clock, agent, session: int, behavior: str, duration_seconds, email=None):
        self.rows.append({
            "tick": clock.tick,
            "day": clock.day,
            "hour": clock.hour,
            "minute": clock.minute,
            "second":  clock.second,
            "period": "work" if clock.is_work_hours else "off",
            "agent_id": agent.agent_id,
            "profile": agent.profile,
            "risk_score": round(agent.risk_score, 1),
            "is_suspicious": agent.is_suspicious,
            "session": session,
            "behavior": behavior,
            "duration_seconds": duration_seconds,
            "channel": getattr(email, "channel", "") if email else "",
            "artifact_kind": getattr(email, "artifact_kind", "") if email else "",
            "artifact_id": getattr(email, "artifact_id", "") if email else "",
            "artifact_category": getattr(email, "category", "") if email else "",
            "sender": getattr(email, "sender", "") if email else "",
            "recipient": getattr(email, "recipient", "") if email else "",
            "flagged": behavior in settings.SUSPICIOUS_STATES,
        })

    def to_csv(self) -> str:
        os.makedirs(os.path.dirname(settings.OUTPUT_CSV), exist_ok=True)
        with open(settings.OUTPUT_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(self.rows)
        return os.path.abspath(settings.OUTPUT_CSV)

    def summary(self) -> dict:
        total = len(self.rows)
        flagged = sum(1 for r in self.rows if r["flagged"])
        return {"total_events": total, "flagged_events": flagged}
