import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections.abc import Mapping
from typing import Any


def configure_logging() -> None:
    """Configure process logging once via environment.

    ENGINE_LOG_LEVEL controls verbosity (default: INFO).
    ENGINE_LOG_FILE controls file output path (default: logs/engine.log).
    ENGINE_LOG_THIRD_PARTY_LEVEL controls noise from external libs
    (default: WARNING).
    """
    level_name = os.getenv("ENGINE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    third_party_level_name = os.getenv("ENGINE_LOG_THIRD_PARTY_LEVEL", "WARNING").upper()
    third_party_level = getattr(logging, third_party_level_name, logging.WARNING)
    log_file = Path(os.getenv("ENGINE_LOG_FILE", "logs/engine.log"))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Keep your application logs verbose while muting dependency internals.
    for noisy_logger in (
        "aiosqlite",
        "asyncio",
        "langgraph",
        "httpx",
        "httpcore",
        "openai",
    ):
        logging.getLogger(noisy_logger).setLevel(third_party_level)


def short(value: Any, *, limit: int = 160) -> str:
    text = repr(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...({len(text)} chars)"


def summarize_mapping(mapping: Mapping[str, Any], *, limit: int = 12) -> dict[str, str]:
    items = list(mapping.items())
    if len(items) > limit:
        items = items[:limit]
    summary = {k: short(v) for k, v in items}
    if len(mapping) > limit:
        summary["..."] = f"{len(mapping) - limit} more keys"
    return summary
