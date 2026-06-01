import logging

from src.core.model.message import Message
from src.database.repository.base import BaseRepository
from src.database.repository.message import MessageRepository


class MessageService:
    def __init__(self, base: BaseRepository, messages: MessageRepository) -> None:
        self._logger = logging.getLogger("engine.service.message")
        self._base = base
        self._messages = messages

    def get_history(self) -> list[Message]:
        history = self._messages.get_history()
        self._logger.debug("get_history count=%s", len(history))
        return history

    def append(self, messages: list[Message]) -> None:
        self._logger.debug("append messages count=%s", len(messages))
        with self._base.transaction():
            self._messages.append(messages)
