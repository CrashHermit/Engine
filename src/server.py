import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model.message import Message
from database.connection import DatabaseConnection
from database.repository.message import MessageRepository
from database.repository.user import UserRepository
from database.schema import SchemaManager
from graph import Graph


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = Graph().build().compile()
    app.state.conn = DatabaseConnection()
    app.state.conn.open()
    SchemaManager(app.state.conn.database).ensure()
    logger.info("ArcadeDB Studio: %s", app.state.conn.studio_url)
    await run_in_threadpool(UserRepository(app.state.conn.database).get_or_create_user)
    yield
    app.state.conn.shutdown_server()


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
    db = app.state.conn.database
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
