import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import Engine

app: FastAPI = FastAPI()
engine: Engine = Engine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    text: str


@app.post("/chat")
async def chat(request: MessageRequest) -> StreamingResponse:
    async def event_stream():
        async for event in engine.stream_message(request.text):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
