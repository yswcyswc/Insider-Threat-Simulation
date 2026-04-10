import random
from collections import deque
from config import settings
from environment.emailbox import EmailBox
from environment.messengerbox import MessengerBox


class EmployeeAgent:

    def __init__(
        self,
        agent_id: str,
        profile: str,
        rng: random.Random,
        email_weight: float,
        messenger_weight: float,
        formal_contacts: set[str],
        informal_contacts: set[str],
    ):
        self.agent_id = agent_id
        self.profile = profile  
        self.rng = rng
        self.email_weight = email_weight
        self.messenger_weight = messenger_weight
        self.risk_score = 0.0
        self.formal_contacts = set(formal_contacts)
        self.informal_contacts = set(informal_contacts)
        self.emailbox = EmailBox(agent_id, rng, self.formal_contacts)
        self.messengerbox = MessengerBox(agent_id, rng, self.informal_contacts)
        self._queue = deque()
        self._remaining = 0

    # Risk

    @property
    def is_suspicious(self) -> bool:
        return self.risk_score >= settings.SUSPICIOUS_THRESHOLD

    def increment_risk(self):
        self.risk_score += settings.RISK_INCREMENT[self.profile]

    def recover_risk(self):
        self.risk_score = max(0.0, self.risk_score - settings.IDLE_RISK_RECOVERY_PER_SECOND,)

    # Email chains

    def _next_state(self, state: str) -> str:
        """Pick the next email state using the appropriate transition table."""
        if state in settings.MESSENGER_NORMAL_TRANSITIONS:
            row = settings.MESSENGER_NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})
            return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

        if self.is_suspicious and state in settings.SUSPICIOUS_TRANSITIONS:
            row = settings.SUSPICIOUS_TRANSITIONS[state]
        else:
            row = settings.NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})

        return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

    def _perform_state(self, state: str, active_artifact):
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
            return self.emailbox.reply_email(active_artifact)
        if state == "FORWARD":
            return self.emailbox.forward_email(active_artifact)
        if state == "CLICK_LINK":
            return self.emailbox.click_link(active_artifact)
        if state == "FWD_EXTERNAL":
            return self.emailbox.forward_external(active_artifact)
        if state == "LEAK_ATTACH":
            return self.emailbox.leak_attachment(active_artifact)
        if state == "SEARCH_SENSITIVE":
            return self.emailbox.search_sensitive()
        if state == "OPEN_MESSENGER":
            return state, None
        if state == "VIEW_CHATS":
            return state, None
        if state == "READ_MESSAGE":
            return self.messengerbox.read_message()
        if state == "SEND_MESSAGE":
            return self.messengerbox.send_message()
        if state == "SEARCH_MESSAGES":
            return self.messengerbox.search_messages()
        if state == "DELETE_MESSAGE":
            return self.messengerbox.delete_message()
        if state == "REPLY_MESSAGE":
            return self.messengerbox.reply_message(active_artifact)
        raise ValueError(f"Unknown communication state: {state}")

    def _duration_range_for(self, behavior: str, artifact) -> tuple[int, int]:
        low, high = settings.ACTION_DURATION_RANGES[self.profile][behavior]

        if artifact is None:
            return low, high

        if behavior not in settings.ARTIFACT_SENSITIVE_ACTIONS:
            return low, high

        multiplier_map = settings.EMAIL_CATEGORY_DURATION_MULTIPLIER
        if getattr(artifact, "channel", "email") == "messenger":
            multiplier_map = settings.MESSAGE_CATEGORY_DURATION_MULTIPLIER

        multiplier = multiplier_map.get(artifact.category, 1.0)
        adjusted_low = max(1, round(low * multiplier))
        adjusted_high = max(adjusted_low, round(high * multiplier))
        return adjusted_low, adjusted_high

    def _sample_duration(self, behavior: str, artifact) -> int:
        low, high = self._duration_range_for(behavior, artifact)
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

    def run_messenger_session(self) -> list[tuple[str, object, int]]:
        session_events = []
        state = "OPEN_MESSENGER"
        active_message = None

        while state != "DONE":
            behavior, message = self._perform_state(state, active_message)
            if message is not None:
                active_message = message

            session_events.append(
                (behavior, message, self._sample_duration(behavior, message))
            )
            state = self._next_state(state)

        return session_events

    def sessions_this_hour(self) -> int:
        return settings.SESSIONS_PER_HOUR[self.profile]

    def _choose_channel(self) -> str:
        choices = []
        weights = []

        if self.formal_contacts and self.email_weight > 0:
            choices.append("email")
            weights.append(self.email_weight)

        if self.informal_contacts and self.messenger_weight > 0:
            choices.append("messenger")
            weights.append(self.messenger_weight)

        if not choices:
            return "email"

        return self.rng.choices(choices, weights=weights)[0]

    def _build_work_hour_plan(self) -> list[tuple[int, str, int, object]]:
        hour_plan = []
        remaining = settings.SECONDS_PER_HOUR
        session_num = 1

        while remaining > 0:
            if self._choose_channel() == "messenger":
                session_events = self.run_messenger_session()
                self.messengerbox.receive_new_messages(count=1)
            else:
                session_events = self.run_email_session()
                self.emailbox.receive_new_emails(count=1)

            for behavior, email, duration in session_events:
                if remaining <= 0:
                    break

                actual_duration = min(duration, remaining)
                hour_plan.append((session_num, behavior, actual_duration, email))
                remaining -= actual_duration

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

    def receive_artifact(self, artifact):
        if getattr(artifact, "channel", "") == "email":
            self.emailbox.receive_email(artifact)
        elif getattr(artifact, "channel", "") == "messenger":
            self.messengerbox.receive_message(artifact)

    def _artifact_to_deliver(self, behavior: str, artifact):
        if artifact is None:
            return None
        if behavior not in {"COMPOSE", "REPLY", "FORWARD", "SEND_MESSAGE", "REPLY_MESSAGE"}:
            return None
        return artifact

    def step(self, clock, logger):
        if clock.minute == 0 and clock.second == 0:
            self._plan_current_hour(clock.is_work_hours)

        emitted_artifact = None
        while self._remaining == 0 and self._queue:
            session_num, behavior, duration, email = self._queue.popleft()
            if duration <= 0:
                continue

            logger.log(clock, self, session=session_num, behavior=behavior, duration_seconds=duration, email=email, )
            self._remaining = duration
            emitted_artifact = self._artifact_to_deliver(behavior, email)

        if self._remaining > 0:
            if not clock.is_work_hours:
                self.recover_risk()
            self._remaining -= 1

        return emitted_artifact

    def __repr__(self):
        return f"EmployeeAgent({self.agent_id!r}, {self.profile!r}, risk={self.risk_score:.1f})"
