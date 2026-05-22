import asyncio
from typing import AsyncGenerator

import lm  # noqa: F401 — configures dspy global LM on import
from langgraph.checkpoint.memory import MemorySaver

from core.model.message import Message
from graph import Graph


class Engine:
    def __init__(self) -> None:
        self.graph = Graph().build().compile(checkpointer=MemorySaver())
        self._thread_config = {"configurable": {"thread_id": "main"}}

    async def stream_message(self, text: str) -> AsyncGenerator[dict, None]:
        human_message = Message(role="human", content=text, name="You")

        async for part in self.graph.astream(
            {"human_message": human_message},
            config=self._thread_config,
            stream_mode=["custom", "updates"],
            version="v2",
        ):
            if part["type"] == "custom":
                yield part["data"]
            elif part["type"] == "updates":
                for node_name in part["data"]:
                    yield {"event": "node_update", "node": node_name}

    async def run(self) -> None:
        while True:
            human_input: str = await asyncio.to_thread(input, "You: ")

            if human_input.lower() == "exit":
                print("Exiting...")
                break

            print("Narrator: ", end="", flush=True)
            saw_tokens: bool = False

            async for event in self.stream_message(human_input):
                if event.get("event") == "token":
                    saw_tokens = True
                    print(event["delta"], end="", flush=True)
                elif event.get("event") == "done":
                    if not saw_tokens:
                        print(event["content"], end="", flush=True)
                    print()


if __name__ == "__main__":
    asyncio.run(Engine().run())
