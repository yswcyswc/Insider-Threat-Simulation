"""
environment/email.py 

A single email sitting in an agent's EmailBox stack.

Categories
----------
"normal"    — routine workplace email, safe
"phishing"  — crafted to trick the user (fake login, link click)
"malicious" — carries a malicious attachment or C2 callback link
"""

from dataclasses import dataclass, field
from typing import Literal

EmailCategory = Literal["normal", "phishing", "malicious"]


@dataclass
class Email:
    email_id: int
    sender:   str
    recipient: str
    subject:  str
    category: EmailCategory
    is_read:  bool = field(default=False)

    @property
    def artifact_id(self) -> int:
        return self.email_id

    @property
    def artifact_kind(self) -> str:
        return "email"

    @property
    def channel(self) -> str:
        return "email"

    def __repr__(self) -> str:
        return (f"Email(id={self.email_id}, category={self.category!r}, "
                f"sender={self.sender!r}, recipient={self.recipient!r}, "
                f"subject={self.subject!r}, read={self.is_read})")
