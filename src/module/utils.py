from core.model.message import Message


def format_messages(messages: list[Message]) -> str:
    parts = []
    for m in messages:
        label = m.name if m.name else m.role.capitalize()
        parts.append(f"{label}: {m.content}")
    return "\n".join(parts)
