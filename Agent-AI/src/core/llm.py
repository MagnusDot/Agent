from functools import cache

from langchain_openai import ChatOpenAI


@cache
def get_model(
    model_name: str,
    temperature: float = 0,
    streaming: bool = True,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        streaming=streaming,
    )
