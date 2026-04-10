import random

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
        self.remaining = 0
        self.state = None
        self.pending_state = None
        self.active_communication = None
        self.session_num = 0

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

    def next_state(self, state: str) -> str:
        if state in settings.MESSENGER_NORMAL_TRANSITIONS:
            row = settings.MESSENGER_NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})
            return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

        if self.is_suspicious and state in settings.SUSPICIOUS_TRANSITIONS:
            row = settings.SUSPICIOUS_TRANSITIONS[state]
        else:
            row = settings.NORMAL_TRANSITIONS.get(state, {"DONE": 1.0})

        return self.rng.choices(list(row.keys()), weights=list(row.values()))[0]

    def perform_state(self, state: str, active_communication):
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
            return self.emailbox.reply_email(active_communication)
        if state == "FORWARD":
            return self.emailbox.forward_email(active_communication)
        if state == "CLICK_LINK":
            return self.emailbox.click_link(active_communication)
        if state == "FWD_EXTERNAL":
            return self.emailbox.forward_external(active_communication)
        if state == "LEAK_ATTACH":
            return self.emailbox.leak_attachment(active_communication)
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
            return self.messengerbox.reply_message(active_communication)
        raise ValueError(f"Unknown communication state: {state}")

    def duration_range_for(self, behavior: str, communication) -> tuple[int, int]:
        low, high = settings.ACTION_DURATION_RANGES[self.profile][behavior]

        if communication is None:
            return low, high

        if behavior not in settings.ARTIFACT_SENSITIVE_ACTIONS:
            return low, high

        multiplier_map = settings.EMAIL_CATEGORY_DURATION_MULTIPLIER
        if getattr(communication, "channel", "email") == "messenger":
            multiplier_map = settings.MESSAGE_CATEGORY_DURATION_MULTIPLIER

        multiplier = multiplier_map.get(communication.category, 1.0)
        adjusted_low = max(1, round(low * multiplier))
        adjusted_high = max(adjusted_low, round(high * multiplier))
        return adjusted_low, adjusted_high

    def sample_duration(self, behavior: str, communication) -> int:
        low, high = self.duration_range_for(behavior, communication)
        return round(self.rng.uniform(low, high))

    def choose_channel(self) -> str:
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

    def communication_to_deliver(self, behavior: str, communication):
        if communication is None:
            return None
        if behavior not in {"COMPOSE", "REPLY", "FORWARD", "SEND_MESSAGE", "REPLY_MESSAGE"}:
            return None
        return communication

    def seconds_until_next_hour(self, clock) -> int:
        elapsed = clock.minute * 60 + clock.second
        return max(1, settings.SECONDS_PER_HOUR - elapsed)

    def start_new_session(self):
        self.session_num += 1
        self.active_communication = None

        if self.choose_channel() == "messenger":
            self.messengerbox.receive_new_messages(count=1)
            return "OPEN_MESSENGER"

        self.emailbox.receive_new_emails(count=1)
        return "OPEN_CLIENT"

    def begin_next_action(self, clock, logger):
        if not clock.is_work_hours:
            duration = self.seconds_until_next_hour(clock)
            logger.log(
                clock,
                self,
                session=0,
                behavior="IDLE",
                duration_seconds=duration,
                email=None,
            )
            self.remaining = duration
            self.pending_state = None
            self.state = None
            self.active_communication = None
            return None

        if self.state in {None, "DONE"}:
            self.state = self.start_new_session()

        behavior, communication = self.perform_state(self.state, self.active_communication)
        if communication is not None:
            self.active_communication = communication

        duration = max(1, self.sample_duration(behavior, communication))
        logger.log(
            clock,
            self,
            session=self.session_num,
            behavior=behavior,
            duration_seconds=duration,
            email=communication,
        )
        self.remaining = duration
        self.pending_state = self.next_state(self.state)
        return self.communication_to_deliver(behavior, communication)

    def receive_communication(self, communication):
        if getattr(communication, "channel", "") == "email":
            self.emailbox.receive_email(communication)
        elif getattr(communication, "channel", "") == "messenger":
            self.messengerbox.receive_message(communication)

    def receive_artifact(self, artifact):
        self.receive_communication(artifact)

    def step(self, clock, logger):
        if clock.minute == 0 and clock.second == 0:
            self.session_num = 0
            if clock.is_work_hours:
                self.increment_risk()

        emitted_communication = None
        if self.remaining == 0:
            emitted_communication = self.begin_next_action(clock, logger)

        if self.remaining > 0:
            if not clock.is_work_hours:
                self.recover_risk()
            self.remaining -= 1
            if self.remaining == 0:
                self.state = self.pending_state

        return emitted_communication

    def __repr__(self):
        return f"EmployeeAgent({self.agent_id!r}, {self.profile!r}, risk={self.risk_score:.1f})"
