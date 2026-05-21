import asyncio
from typing import AsyncGenerator

from core.model.message import Message
from graph import Graph


class Engine:
    def __init__(self) -> None:
        self.graph = Graph().build().compile()
        self.message_history: list[Message] = []

    async def stream_message(self, text: str) -> AsyncGenerator[dict, None]:
        human_message: Message = Message(role="human", content=text, name="You")

        async for part in self.graph.astream(
            {
                "message_history": self.message_history,
                "human_message": human_message,
            },
            stream_mode=["custom", "updates"],
            version="v2",
        ):
            if part["type"] == "custom":
                yield part["data"]
            elif part["type"] == "updates":
                for node_name, update in part["data"].items():
                    if new_messages := update.get("message_history"):
                        self.message_history.extend(new_messages)
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
