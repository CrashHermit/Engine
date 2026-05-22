from typing import AsyncGenerator

import dspy
from langgraph.config import get_stream_writer


class StreamingDSPyNode(dspy.Module):
    def __init__(self, node_name: str, output_field: str) -> None:
        super().__init__()
        self._node_name: str = node_name
        self._output_field: str = output_field
        self._streaming_engine = None

    def _get_streaming_engine(self):
        if self._streaming_engine is None:
            self._streaming_engine = dspy.streamify(
                program=self,
                stream_listeners=[
                    dspy.streaming.StreamListener(signature_field_name=self._output_field)
                ],
                is_async_program=True,
            )
        return self._streaming_engine

    async def stream(
        self, **kwargs
    ) -> AsyncGenerator[dspy.streaming.StreamResponse | dspy.Prediction, None]:
        async for chunk in self._get_streaming_engine()(**kwargs):
            yield chunk

    async def stream_to_writer(self, **kwargs) -> dspy.Prediction:
        writer = get_stream_writer()
        prediction: dspy.Prediction | None = None

        async for chunk in self.stream(**kwargs):
            if isinstance(chunk, dspy.streaming.StreamResponse):
                writer({"event": "token", "node": self._node_name, "delta": chunk.chunk})
            elif isinstance(chunk, dspy.Prediction):
                prediction = chunk
                writer({"event": "done", "node": self._node_name, "content": getattr(chunk, self._output_field).strip()})

        if prediction is None:
            raise RuntimeError(f"{self._node_name} stream ended without a prediction")

        return prediction
