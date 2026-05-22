import dspy


class BaseModule(dspy.Module):
    def __init__(self, signature, stream_fields: list[str], predictor=dspy.Predict) -> None:
        super().__init__()
        self.predict = predictor(signature=signature)
        self._stream_fields = stream_fields
        self._streaming_engine = None

    def forward(self, **kwargs) -> dspy.Prediction:
        return self.predict(**kwargs)

    async def aforward(self, **kwargs) -> dspy.Prediction:
        return await self.predict.acall(**kwargs)

    async def stream(self, **kwargs):
        if self._streaming_engine is None:
            self._streaming_engine = dspy.streamify(
                self,
                stream_listeners=[
                    dspy.streaming.StreamListener(signature_field_name=f)
                    for f in self._stream_fields
                ],
                is_async_program=True,
            )
        async for chunk in self._streaming_engine(**kwargs):
            yield chunk
