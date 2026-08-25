from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_qa_llm() -> ChatOpenAI:
    """
    Create the OpenAI LangChain model once and reuse it.
    """

    if not settings.OPENAI_API_KEY:

        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return ChatOpenAI(
        model=settings.QA_MODEL,
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.QA_LLM_TIMEOUT_SECONDS,
        max_retries=2,
    )