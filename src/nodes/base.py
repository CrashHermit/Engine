from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import dspy
from langgraph.config import get_stream_writer
from langgraph.types import Send

S = TypeVar("S")


class BaseNode(ABC, Generic[S]):
    """
    Streaming LangGraph node base class.

    Subclasses declare the module class, node name, and output field in
    __init__, then override get_inputs and build_update.
    """

    def __init__(self, module_class: type, node_name: str, output_field: str) -> None:
        self._module = module_class()
        self._node_name = node_name
        self._output_field = output_field

    async def __call__(self, state: S) -> dict:
        writer = get_stream_writer()
        prediction: dspy.Prediction | None = None

        async for chunk in self._module.stream(**self.get_inputs(state)):
            if isinstance(chunk, dspy.streaming.StreamResponse):
                writer({"event": "token", "node": self._node_name, "delta": chunk.chunk})
            elif isinstance(chunk, dspy.Prediction):
                prediction = chunk

        if prediction is None:
            raise RuntimeError(f"{self._node_name} stream ended without a prediction")

        writer({
            "event": "done",
            "node": self._node_name,
            "content": getattr(prediction, self._output_field).strip(),
        })

        return self.build_update(state, prediction)

    @abstractmethod
    def get_inputs(self, state: S) -> dict:
        ...

    @abstractmethod
    def build_update(self, state: S, prediction: dspy.Prediction) -> dict:
        ...


class BaseDispatcherNode(ABC, Generic[S]):
    """
    Fan-out node: maps state to a list of Send objects for parallel execution.
    """

    async def __call__(self, state: S) -> list[Send]:
        return self.dispatch(state)

    @abstractmethod
    def dispatch(self, state: S) -> list[Send]:
        ...


class BaseCondenseNode(BaseNode[S]):
    """
    Fan-in node: same interface as BaseNode, signals that this node aggregates
    parallel worker results already accumulated in state via reducers.
    """
