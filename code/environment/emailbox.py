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


def _make_email(rng):
    cats = list(settings.EMAIL_CATEGORY_WEIGHTS.keys())
    weights = list(settings.EMAIL_CATEGORY_WEIGHTS.values())
    cat = rng.choices(cats, weights=weights)[0]
    return Email(
        email_id=_new_id(),
        sender=rng.choice(_SENDERS[cat]),
        subject=rng.choice(_SUBJECTS[cat]),
        category=cat,
    )


class EmailBox:
    def __init__(self, owner_id, rng):
        self.owner_id = owner_id
        self.rng = rng
        self._stack = [_make_email(rng) for _ in range(settings.INBOX_INITIAL_SIZE)]
        self._sent = []
        self._deleted = []

    @property
    def inbox_size(self):
        return len(self._stack)

    def read_email(self):
        if not self._stack:
            return "VIEW_INBOX", None
        email = self._stack.pop()
        email.is_read = True
        return "READ_EMAIL", email

    def write_email(self):
        email = _make_email(self.rng)
        email.sender = f"{self.owner_id}@company.com"
        email.is_read = True
        self._sent.append(email)
        return "COMPOSE", email

    def reply_email(self, original=None):
        reply = _make_email(self.rng)
        reply.sender = f"{self.owner_id}@company.com"
        reply.is_read = True
        self._sent.append(reply)
        return "REPLY", reply

    def forward_email(self, original=None):
        fwd = _make_email(self.rng)
        fwd.sender = f"{self.owner_id}@company.com"
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
            self._stack.append(_make_email(self.rng))

    def __repr__(self):
        return f"EmailBox(owner={self.owner_id!r}, inbox={self.inbox_size}, sent={len(self._sent)})"