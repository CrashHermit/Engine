import asyncio
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from src.logging_utils import configure_logging

logger = logging.getLogger("engine.sandbox.interrupt")

class State(TypedDict):
    user_text: str
    question: str | None
    done: bool

async def router(state: State) -> dict:
    if state.get("user_text", "").startswith("ANSWER:"):
        return {"done": True}
    if not state.get("question"):
        return {"done": False}
    return {"done": False}

async def ask(state: State) -> dict:
    return {"question": "What exactly do you want to do?"}

async def finish(state: State) -> dict:
    return {"done": True}

def build():
    g = StateGraph(State)
    g.add_node("router", router)
    g.add_node("ask", ask)
    g.add_node("finish", finish)

    g.add_edge(START, "router")
    g.add_conditional_edges(
        source="router",
        path=lambda s: s.get("done"),
        path_map={
            True: "finish",
            False: "ask",
        },
    )
    g.add_edge("ask", "router")
    g.add_edge("finish", END)

    return g.compile(
        checkpointer=MemorySaver(),
        interrupt_after=["ask"],
    )

async def main():
    configure_logging()
    graph = build()
    config = {"configurable": {"thread_id": "1"}}

    result = await graph.ainvoke({"user_text": "Hello, how are you?"}, config=config)
    logger.info("After turn 1: %s", result)

    snapshot = graph.get_state(config=config)
    logger.info("next: %s", snapshot.next)
    logger.info("values: %s", snapshot.values)

    result = await graph.ainvoke(
        Command(update={"user_text": "ANSWER: I'm fine, thank you!"}),
        config=config,
    )
    snapshot = graph.get_state(config=config)
    logger.info("After resume: %s", result)
    logger.info("next: %s", snapshot.next)
    logger.info("values: %s", snapshot.values)

if __name__ == "__main__":
    asyncio.run(main())