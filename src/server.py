import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model.message import Message
from database.repository.message import MessageRepository
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
    session_id = await run_in_threadpool(repo.create)
    return {"session_id": session_id}


class ChatRequest(BaseModel):
    session_id: str
    text: str


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    db = app.state.store.database
    session_repo = SessionRepository(db)
    msg_repo = MessageRepository(db)

    if await run_in_threadpool(session_repo.get, request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    message_history = await run_in_threadpool(msg_repo.get_history, request.session_id)
    human_message = Message(role="human", content=request.text, name="You")

    await run_in_threadpool(msg_repo.append, request.session_id, [human_message])

    result = await app.state.graph.ainvoke(
        {"message_history": message_history, "human_message": human_message}
    )

    ai_message: Message = result["ai_message"]
    await run_in_threadpool(msg_repo.append, request.session_id, [ai_message])

    return {"content": ai_message.content}
