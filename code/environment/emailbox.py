import csv
from collections import defaultdict
from pathlib import Path

from config import settings
from environment.email import Email


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_SENDERS_CSV = _DATA_DIR / "email_senders.csv"
_SUBJECTS_CSV = _DATA_DIR / "email_subjects.csv"


def _load_pool(csv_path, value_column):
    pool = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["category"].strip()
            value = row[value_column].strip()
            if category and value:
                pool[category].append(value)
    return dict(pool)


_SENDERS = _load_pool(_SENDERS_CSV, "sender")
_SUBJECTS = _load_pool(_SUBJECTS_CSV, "subject")

_next_id = 0


def _new_id():
    global _next_id
    _next_id += 1
    return _next_id


def _pick_contact(rng, contacts, fallback):
    if contacts:
        return rng.choice(sorted(contacts))
    return fallback


def _internal_address(name):
    return f"{name}@company.com"


def _is_formal_contact(address, contacts):
    if not address.endswith("@company.com"):
        return False
    name = address.removesuffix("@company.com")
    return name in contacts


def _make_email(rng, owner_id, contacts, direction="incoming"):
    cats = list(settings.EMAIL_CATEGORY_WEIGHTS.keys())
    weights = list(settings.EMAIL_CATEGORY_WEIGHTS.values())
    cat = rng.choices(cats, weights=weights)[0]

    if direction == "outgoing":
        contact = _pick_contact(rng, contacts, owner_id)
        sender = _internal_address(owner_id)
        recipient = _internal_address(contact)
    elif cat == "normal":
        contact = _pick_contact(rng, contacts, owner_id)
        sender = _internal_address(contact)
        recipient = _internal_address(owner_id)
    else:
        sender = rng.choice(_SENDERS[cat])
        recipient = _internal_address(owner_id)

    return Email(
        email_id=_new_id(),
        sender=sender,
        recipient=recipient,
        subject=rng.choice(_SUBJECTS[cat]),
        category=cat,
    )


class EmailBox:
    def __init__(self, owner_id, rng, formal_contacts):
        self.owner_id = owner_id
        self.rng = rng
        self.formal_contacts = set(formal_contacts)
        self._stack = [
            _make_email(rng, owner_id, self.formal_contacts)
            for _ in range(settings.INBOX_INITIAL_SIZE)
        ]
        self._sent = []
        self._deleted = []

    @property
    def inbox_size(self):
        return len(self._stack)

    def receive_email(self, email):
        if len(self._stack) < settings.INBOX_MAX_SIZE:
            self._stack.append(email)

    def read_email(self):
        if not self._stack:
            return "VIEW_INBOX", None
        email = self._stack.pop()
        email.is_read = True
        return "READ_EMAIL", email

    def write_email(self):
        email = _make_email(
            self.rng,
            self.owner_id,
            self.formal_contacts,
            direction="outgoing",
        )
        email.is_read = True
        self._sent.append(email)
        return "COMPOSE", email

    def reply_email(self, original=None):
        reply = _make_email(
            self.rng,
            self.owner_id,
            self.formal_contacts,
            direction="outgoing",
        )
        if original is not None and _is_formal_contact(getattr(original, "sender", ""), self.formal_contacts):
            reply.recipient = original.sender
        reply.is_read = True
        self._sent.append(reply)
        return "REPLY", reply

    def forward_email(self, original=None):
        fwd = _make_email(
            self.rng,
            self.owner_id,
            self.formal_contacts,
            direction="outgoing",
        )
        fwd.is_read = True
        self._sent.append(fwd)
        return "FORWARD", fwd

    def delete_email(self):
        if not self._stack:
            return "DELETE", None
        email = self._stack.pop()
        self._deleted.append(email)
        return "DELETE", email

    def search_inbox(self):
        return "SEARCH", None

    def click_link(self, email=None):
        return "CLICK_LINK", email

    def forward_external(self, email=None):
        return "FWD_EXTERNAL", email

    def leak_attachment(self, email=None):
        return "LEAK_ATTACH", email

    def search_sensitive(self):
        return "SEARCH_SENSITIVE", None

    def restroom_break(self):
        return "RESTROOM", None

    def away_from_desk(self):
        return "AWAY_DESK", None

    def receive_new_emails(self, count=1):
        space = settings.INBOX_MAX_SIZE - len(self._stack)
        for _ in range(min(count, space)):
            self._stack.append(_make_email(self.rng, self.owner_id, self.formal_contacts))

    def __repr__(self):
        return f"EmailBox(owner={self.owner_id!r}, inbox={self.inbox_size}, sent={len(self._sent)})"
