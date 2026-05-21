import asyncio
from typing import Any

from langchain_core.messages import AnyMessage, HumanMessage
from graph import Graph


class Engine:
    def __init__(self) -> None:
        self.graph = Graph().build().compile()
        self.message_history: list[AnyMessage] = []

    async def run(self) -> None:
        while True:
            human_input: str = await asyncio.to_thread(input, "You: ")
            human_message: HumanMessage = HumanMessage(content=human_input, name="You")

            if human_input.lower() == "exit":
                print("Exiting...")
                break

            result: dict[str, Any] = await self.graph.ainvoke(
                {
                    "message_history": self.message_history,
                    "human_message": human_message,
                }
            )

            self.message_history = result["message_history"]

if __name__ == "__main__":
    asyncio.run(Engine().run())
