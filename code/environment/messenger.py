from dataclasses import dataclass, field
from typing import Literal

MessageCategory = Literal["normal", "phishing", "malicious"]


@dataclass
class Messenger:
    message_id: int
    sender: str
    recipient: str
    body: str
    category: MessageCategory
    is_read: bool = field(default=False)

    @property
    def artifact_id(self) -> int:
        return self.message_id

    @property
    def artifact_kind(self) -> str:
        return "message"

    @property
    def channel(self) -> str:
        return "messenger"

    def __repr__(self) -> str:
        return (
            f"Messenger(id={self.message_id}, category={self.category!r}, "
            f"sender={self.sender!r}, recipient={self.recipient!r}, "
            f"body={self.body!r}, read={self.is_read})"
        )
