import asyncio

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

            print("Narrator: ", end="", flush=True)
            saw_tokens = False

            async for part in self.graph.astream(
                {
                    "message_history": self.message_history,
                    "human_message": human_message,
                },
                stream_mode=["custom", "updates"],
                version="v2",
            ):
                if part["type"] == "custom":
                    data = part["data"]
                    if data.get("event") == "narrator_token":
                        saw_tokens = True
                        print(data["delta"], end="", flush=True)
                    elif data.get("event") == "narrator_done":
                        if not saw_tokens:
                            print(data["content"], end="", flush=True)
                        print()
                elif part["type"] == "updates" and "narrator" in part["data"]:
                    update = part["data"]["narrator"]
                    if new_messages := update.get("message_history"):
                        self.message_history.extend(new_messages)


if __name__ == "__main__":
    asyncio.run(Engine().run())
