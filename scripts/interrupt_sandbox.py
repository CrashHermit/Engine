import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

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
    graph = build()
    config = {"configurable": {"thread_id": "1"}}

    result = await graph.ainvoke({"user_text": "Hello, how are you?"}, config=config)
    print("After turn 1:", result)

    snapshot = graph.get_state(config=config)
    print("next:", snapshot.next)
    print("values:", snapshot.values)

    result = await graph.ainvoke(
        Command(update={"user_text": "ANSWER: I'm fine, thank you!"}),
        config=config,
    )
    snapshot = graph.get_state(config=config)
    print("After resume:", result)
    print("next:", snapshot.next)
    print("values:", snapshot.values)

if __name__ == "__main__":
    asyncio.run(main())