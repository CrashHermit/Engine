from __future__ import annotations

from src.core.model.message import Message
from src.database.repository.base import BaseRepository
from src.database.repository.message import MessageRepository


class MessageService:
    def __init__(self, base: BaseRepository, messages: MessageRepository) -> None:
        self._base = base
        self._messages = messages

    def get_history(self) -> list[Message]:
        return self._messages.get_history()

    def append(self, messages: list[Message]) -> None:
        with self._base.transaction():
            self._messages.append(messages)
