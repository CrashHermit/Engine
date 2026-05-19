import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from graph import Graph


class Engine:
    def __init__(self) -> None:
        self.graph = Graph().build().compile()
        self.messages: list = []

    async def run(self) -> None:
        while True:
            text = await asyncio.to_thread(input, "You: ")

            if text.lower() == "exit":
                print("Exiting...")
                break

            if not text.strip():
                continue

            result = await self.graph.ainvoke({"messages": [HumanMessage(content=text)]})
            self.messages = result["messages"]

            last = self.messages[-1]
            if isinstance(last, AIMessage):
                print(f"AI: {last.content}")


if __name__ == "__main__":
    engine = Engine()
    asyncio.run(engine.run())
