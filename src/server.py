import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model.message import Message
from database.repository.message import MessageRepository
from database.repository.user import UserRepository
from database.store import WorldStore
from graph import Graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = Graph().build().compile()
    app.state.store = WorldStore()
    app.state.store.open()
    await run_in_threadpool(UserRepository(app.state.store.database).get_or_create)
    yield
    app.state.store.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    db = app.state.store.database
    msg_repo = MessageRepository(db)

    message_history = await run_in_threadpool(msg_repo.get_history)
    human_message = Message(role="human", content=request.text, name="You")

    await run_in_threadpool(msg_repo.append, [human_message])

    result = await app.state.graph.ainvoke(
        {"message_history": message_history, "human_message": human_message}
    )

    ai_message: Message = result["ai_message"]
    await run_in_threadpool(msg_repo.append, [ai_message])

    return {"content": ai_message.content}
