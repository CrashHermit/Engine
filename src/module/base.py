from typing import (
    Any, 
    AsyncGenerator
)
from dspy import (
    streamify,
    Predict, 
    Signature, 
    Module, 
    Prediction,
)
from dspy.streaming import (
    StreamListener, 
    StreamResponse,
)

class BaseModule(Module):
    def __init__(
        self,
        signature: Signature, 
        stream_fields: list[str], 
        predictor: Predict = Predict
    ) -> None:
        super().__init__()
        self.predict: Predict = predictor(signature=signature)
        self._stream_fields: list[str] = stream_fields
        self._streaming_engine: streamify | None = None

    def forward(self, **kwargs: Any) -> Prediction:
        return self.predict(**kwargs)

    async def aforward(self, **kwargs: Any) -> Prediction:
        return await self.predict.acall(**kwargs)

    async def stream(self, **kwargs: Any) -> AsyncGenerator[StreamResponse, Prediction]:
        if self._streaming_engine is None:
            self._streaming_engine = streamify(
                program=self,
                stream_listeners=[
                    StreamListener(signature_field_name=field)
                    for field in self._stream_fields
                ],
                is_async_program=True,
            )
        async for chunk in self._streaming_engine(**kwargs):
            yield chunk
