import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model.message import Message
from database.repository.session import SessionRepository
from database.store import WorldStore
from graph import Graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = Graph().build().compile()
    app.state.store = WorldStore()
    app.state.store.open()
    yield
    app.state.store.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.post("/session")
async def create_session() -> dict:
    repo = SessionRepository(app.state.store.database)
    session_id = repo.create()
    return {"session_id": session_id}


class ChatRequest(BaseModel):
    session_id: str
    text: str


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    repo = SessionRepository(app.state.store.database)
    if repo.get(request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # TODO: load message history from ArcadeDB via MessageRepository
    message_history: list[Message] = []

    human_message = Message(role="human", content=request.text, name="You")

    async def event_stream():
        async for event in app.state.graph.astream(
            {"message_history": message_history, "human_message": human_message},
            stream_mode="custom",
        ):
            if event.get("event") == "token":
                yield f"data: {json.dumps(event)}\n\n"
            elif event.get("event") == "message":
                # TODO: save human_message + ai_message to ArcadeDB via MessageRepository
                pass

    return StreamingResponse(event_stream(), media_type="text/event-stream")
