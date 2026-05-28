from src.core.model.message import Message
from src.database.repository.message import MessageRepository


class MessageService:
    def __init__(self, messages: MessageRepository) -> None:
        self._messages = messages

    def get_history(self) -> list[Message]:
        return self._messages.get_history()

    def append(self, messages: list[Message]) -> None:
        self._messages.append(messages)
