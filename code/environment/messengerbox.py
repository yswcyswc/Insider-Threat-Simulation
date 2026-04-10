import csv
from collections import defaultdict
from pathlib import Path

from config import settings
from environment.messenger import Messenger


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_SENDERS_CSV = _DATA_DIR / "message_senders.csv"
_BODIES_CSV = _DATA_DIR / "message_bodies.csv"


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
_BODIES = _load_pool(_BODIES_CSV, "body")

_next_id = 0


def _new_id():
    global _next_id
    _next_id += 1
    return _next_id


def _pick_contact(rng, contacts, fallback):
    if contacts:
        return rng.choice(sorted(contacts))
    return fallback


def _make_message(rng, owner_id, contacts, direction="incoming"):
    cats = list(settings.MESSAGE_CATEGORY_WEIGHTS.keys())
    weights = list(settings.MESSAGE_CATEGORY_WEIGHTS.values())
    cat = rng.choices(cats, weights=weights)[0]

    if direction == "outgoing":
        contact = _pick_contact(rng, contacts, owner_id)
        sender = owner_id
        recipient = contact
    elif cat == "normal":
        contact = _pick_contact(rng, contacts, owner_id)
        sender = contact
        recipient = owner_id
    else:
        sender = rng.choice(_SENDERS[cat])
        recipient = owner_id

    return Messenger(
        message_id=_new_id(),
        sender=sender,
        recipient=recipient,
        body=rng.choice(_BODIES[cat]),
        category=cat,
    )


class MessengerBox:
    def __init__(self, owner_id, rng, informal_contacts):
        self.owner_id = owner_id
        self.rng = rng
        self.informal_contacts = set(informal_contacts)
        self._queue = [
            _make_message(rng, owner_id, self.informal_contacts)
            for _ in range(settings.MESSAGEBOX_INITIAL_SIZE)
        ]
        self._sent = []
        self._deleted = []

    @property
    def inbox_size(self):
        return len(self._queue)

    def receive_message(self, message):
        if len(self._queue) < settings.MESSAGEBOX_MAX_SIZE:
            self._queue.append(message)

    def read_message(self):
        if not self._queue:
            return "VIEW_CHATS", None
        message = self._queue.pop()
        message.is_read = True
        return "READ_MESSAGE", message

    def send_message(self):
        message = _make_message(
            self.rng,
            self.owner_id,
            self.informal_contacts,
            direction="outgoing",
        )
        message.is_read = True
        self._sent.append(message)
        return "SEND_MESSAGE", message

    def reply_message(self, original=None):
        reply = _make_message(
            self.rng,
            self.owner_id,
            self.informal_contacts,
            direction="outgoing",
        )
        if original is not None and getattr(original, "sender", "") in self.informal_contacts:
            reply.recipient = original.sender
        reply.is_read = True
        self._sent.append(reply)
        return "REPLY_MESSAGE", reply

    def delete_message(self):
        if not self._queue:
            return "DELETE_MESSAGE", None
        message = self._queue.pop()
        self._deleted.append(message)
        return "DELETE_MESSAGE", message

    def search_messages(self):
        return "SEARCH_MESSAGES", None

    def receive_new_messages(self, count=1):
        space = settings.MESSAGEBOX_MAX_SIZE - len(self._queue)
        for _ in range(min(count, space)):
            self._queue.append(
                _make_message(self.rng, self.owner_id, self.informal_contacts)
            )

    def __repr__(self):
        return (
            f"MessengerBox(owner={self.owner_id!r}, "
            f"inbox={self.inbox_size}, sent={len(self._sent)})"
        )
