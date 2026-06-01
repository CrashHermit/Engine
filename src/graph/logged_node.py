import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from src.logging_utils import summarize_mapping
from src.state import GraphState


class LoggedNode:
    """Wrap a graph node and emit structured input/output debug logs."""

    def __init__(
        self,
        name: str,
        node: Callable[[GraphState], Awaitable[dict[str, Any]]],
    ) -> None:
        self._name = name
        self._node = node
        self._logger = logging.getLogger(f"engine.node.{name}")

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        self._logger.debug("input=%s", summarize_mapping(state.model_dump()))
        result = await self._node(state)
        if isinstance(result, Mapping):
            self._logger.debug("output=%s", summarize_mapping(dict(result)))
        else:
            self._logger.debug("output=%r", result)
        return result
