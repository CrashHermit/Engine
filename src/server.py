import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.model.message import Message
from graph import Graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = Graph().build().compile()
    yield


app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

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
    human_message = Message(role="human", content=request.text, name="You")

    result = await app.state.graph.ainvoke({"human_message": human_message})

    ai_message: Message = result["ai_message"]
    return {"content": ai_message.content}
