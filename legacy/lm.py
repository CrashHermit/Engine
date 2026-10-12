import os

from dotenv import load_dotenv
from dspy import LM, configure

load_dotenv()

lm: LM = LM(
    model=os.getenv("LM_MODEL", "openrouter/google/gemma-4-26b-a4b-it"),
    api_key=os.getenv("LM_API_KEY"),
    temperature=0.7,
    enable_thinking=False,
)
configure(lm=lm)
