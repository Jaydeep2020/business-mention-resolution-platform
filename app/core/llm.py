from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


# ==========================================================
# COMMON LLM CREATOR
# ==========================================================

def create_llm(model_name: str, timeout: float) -> ChatOpenAI:

    if not settings.OPENAI_API_KEY:

        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return ChatOpenAI(
        model=model_name,
        api_key=settings.OPENAI_API_KEY,
        timeout=timeout,
        max_retries=2,
    )


# ==========================================================
# Q&A LLM
# ==========================================================

@lru_cache(maxsize=1)
def get_qa_llm() -> ChatOpenAI:

    return create_llm(
        model_name=settings.QA_MODEL,
        timeout=settings.QA_LLM_TIMEOUT_SECONDS
    )


# ==========================================================
# SMART ASSISTANT LLM
# ==========================================================

@lru_cache(maxsize=1)
def get_assistant_llm() -> ChatOpenAI:

    return create_llm(
        model_name=settings.ASSISTANT_MODEL,
        timeout=settings.ASSISTANT_LLM_TIMEOUT_SECONDS,
    )