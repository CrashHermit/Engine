import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logging.getLogger("nodes.narrator").setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

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
async def chat(request: ChatRequest) -> StreamingResponse:
    db = app.state.store.database
    session_repo = SessionRepository(db)
    msg_repo = MessageRepository(db)

    if await run_in_threadpool(session_repo.get, request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    message_history = await run_in_threadpool(msg_repo.get_history, request.session_id)
    human_message = Message(role="human", content=request.text, name="You")

    await run_in_threadpool(msg_repo.append, request.session_id, [human_message])

    async def event_stream():
        ai_message: Message | None = None
        event_count = 0
        token_count = 0
        logger.info(
            "event_stream start | session=%s | history_len=%d",
            request.session_id,
            len(message_history),
        )
        try:
            async for event in app.state.graph.astream(
                {"message_history": message_history, "human_message": human_message},
                stream_mode="custom",
            ):
                event_count += 1
                logger.debug("LangGraph event #%d: %r", event_count, event)
                if event.get("event") == "token":
                    token_count += 1
                    yield f"data: {json.dumps(event)}\n\n"
                elif event.get("event") == "message":
                    content = event.get("content", "")
                    logger.info("message event received | content_len=%d | tokens_so_far=%d", len(content), token_count)
                    ai_message = Message(role="ai", content=content, name="Narrator")
                    if token_count == 0 and content:
                        # DSPy skipped streaming (cache hit or single-chunk response); send full content as one token
                        logger.warning("No streaming tokens received — falling back to single-chunk delivery")
                        yield f"data: {json.dumps({'event': 'token', 'delta': content})}\n\n"
        except Exception:
            logger.exception("Error in event_stream for session %s", request.session_id)
        finally:
            logger.info(
                "event_stream end | session=%s | total_events=%d | tokens_yielded=%d | ai_message_saved=%s",
                request.session_id,
                event_count,
                token_count,
                ai_message is not None,
            )
            if ai_message is not None:
                await run_in_threadpool(msg_repo.append, request.session_id, [ai_message])

    return StreamingResponse(event_stream(), media_type="text/event-stream")
