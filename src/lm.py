import os
from dspy import LM, configure
from dotenv import load_dotenv

load_dotenv()


def make_lm(model_env: str, default: str, **kwargs) -> LM:
    return LM(
        model=os.getenv(model_env, default),
        api_key=os.getenv("LM_API_KEY"),
        **{"temperature": 0.7, **kwargs},
    )


lm: LM = make_lm("LM_MODEL", "openrouter/google/gemma-4-26b-a4b-it")
configure(lm=lm)
