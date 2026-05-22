import os

import dspy

# Tell LangGraph's MemorySaver that our Message type is safe to deserialize via msgpack
os.environ.setdefault("LANGGRAPH_ALLOWED_MSGPACK_MODULES", "core.model.message")

lm = dspy.LM(
    model=os.getenv("LM_MODEL", "openrouter/google/gemma-4-26b-a4b-it"),
    api_key=os.environ["LM_API_KEY"],
    temperature=0.7,
)
dspy.configure(lm=lm)
