import random
from collections import deque
from config import settings
from environment.emailbox import EmailBox


class EmployeeAgent:

    def __init__(self, agent_id: str, profile: str, rng: random.Random):
        self.agent_id = agent_id
        self.profile = profile  
        self.rng = rng
        self.risk_score = 0.0
        self.emailbox = EmailBox(agent_id, rng)
        self._queue = deque()
        self._remaining = 0

    # Risk

    @property
    def is_suspicious(self) -> bool:
        return self.risk_score >= settings.SUSPICIOUS_THRESHOLD

    def increment_risk(self):
        self.risk_score += settings.RISK_INCREMENT[self.profile]

    def recover_risk(self):
        self.risk_score = max(
            0.0,
            self.risk_score - settings.IDLE_RISK_RECOVERY_PER_SECOND,
        )

    # Email chains

    def _next_state(self, state: str) -> str:
        """Pick the next email state using the appropriate transition table."""
        if self.is_suspicious and state in settings.SUSPICIOUS_TRANSITIONS:
            row = settings.SUSPICIOUS_TRANSITIONS[state]
        else:
            row = settings.NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})

        return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

    def _perform_state(self, state: str, active_email):
        if state == "OPEN_CLIENT":
            return state, None
        if state == "VIEW_INBOX":
            return state, None
        if state == "READ_EMAIL":
            return self.emailbox.read_email()
        if state == "COMPOSE":
            return self.emailbox.write_email()
        if state == "SEARCH":
            return self.emailbox.search_inbox()
        if state == "DELETE":
            return self.emailbox.delete_email()
        if state == "REPLY":
            return self.emailbox.reply_email(active_email)
        if state == "FORWARD":
            return self.emailbox.forward_email(active_email)
        if state == "CLICK_LINK":
            return self.emailbox.click_link(active_email)
        if state == "FWD_EXTERNAL":
            return self.emailbox.forward_external(active_email)
        if state == "LEAK_ATTACH":
            return self.emailbox.leak_attachment(active_email)
        if state == "SEARCH_SENSITIVE":
            return self.emailbox.search_sensitive()
        raise ValueError(f"Unknown email state: {state}")

    def _duration_range_for(self, behavior: str, email) -> tuple[int, int]:
        low, high = settings.ACTION_DURATION_RANGES[self.profile][behavior]

        if email is None:
            return low, high

        if behavior not in settings.EMAIL_SENSITIVE_ACTIONS:
            return low, high

        multiplier = settings.EMAIL_CATEGORY_DURATION_MULTIPLIER.get(email.category, 1.0)
        adjusted_low = max(1, round(low * multiplier))
        adjusted_high = max(adjusted_low, round(high * multiplier))
        return adjusted_low, adjusted_high

    def _sample_duration(self, behavior: str, email) -> int:
        low, high = self._duration_range_for(behavior, email)
        return round(self.rng.uniform(low, high))

    def run_email_session(self) -> list[tuple[str, object, int]]:
        """
        Walk through one email session from OPEN_CLIENT to DONE.
        Returns a list of (behavior, email, duration_seconds) tuples.
        """
        session_events = []
        state = "OPEN_CLIENT"
        active_email = None

        while state != "DONE":
            behavior, email = self._perform_state(state, active_email)
            if email is not None:
                active_email = email

            session_events.append(
                (behavior, email, self._sample_duration(behavior, email))
            )
            state = self._next_state(state)

        return session_events

    def sessions_this_hour(self) -> int:
        return settings.SESSIONS_PER_HOUR[self.profile]

    def _build_work_hour_plan(self) -> list[tuple[int, str, int, object]]:
        hour_plan = []
        remaining = settings.SECONDS_PER_HOUR
        session_num = 1

        while remaining > 0:
            session_events = self.run_email_session()
            for behavior, email, duration in session_events:
                if remaining <= 0:
                    break

                actual_duration = min(duration, remaining)
                hour_plan.append((session_num, behavior, actual_duration, email))
                remaining -= actual_duration

            self.emailbox.receive_new_emails(count=1)
            session_num += 1

        return hour_plan

    def _plan_current_hour(self, is_work_hours: bool):
        if is_work_hours:
            self.increment_risk()
            hour_plan = self._build_work_hour_plan()
        else:
            hour_plan = [(0, "IDLE", settings.SECONDS_PER_HOUR, None)]

        self._queue = deque(hour_plan)
        self._remaining = 0

    def step(self, clock, logger):
        if clock.minute == 0 and clock.second == 0:
            self._plan_current_hour(clock.is_work_hours)

        while self._remaining == 0 and self._queue:
            session_num, behavior, duration, email = self._queue.popleft()
            if duration <= 0:
                continue

            logger.log(clock, self, session=session_num, behavior=behavior, duration_seconds=duration, email=email, )
            self._remaining = duration

        if self._remaining > 0:
            if not clock.is_work_hours:
                self.recover_risk()
            self._remaining -= 1

    def __repr__(self):
        return f"EmployeeAgent({self.agent_id!r}, {self.profile!r}, risk={self.risk_score:.1f})"
