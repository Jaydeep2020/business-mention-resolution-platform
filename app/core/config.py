from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    SECRET_KEY: str = "change-this-secret-key"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ======================================================
    # RESOLUTION RATE LIMIT
    # ======================================================

    RESOLUTION_RATE_LIMIT_REQUESTS: int = 10

    RESOLUTION_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ======================================================
    # EMBEDDINGS
    # ======================================================

    EMBEDDING_MODEL_NAME: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    EMBEDDING_BATCH_SIZE: int = 64

    VECTOR_SEARCH_CANDIDATES: int = 50

    BUSINESS_VECTOR_INDEX_PATH: str = (
        "data/vector_store/businesses.faiss"
    )

    # ======================================================
    # CATALOG QUESTION ANSWERING
    # ======================================================

    OPENAI_API_KEY: str | None = None

    QA_MODEL: str = "gpt-4o-mini"

    QA_MAX_RESULTS: int = 10

    QA_LLM_TIMEOUT_SECONDS: float = 30.0

    # ======================================================
    # SMART RESOLUTION ASSISTANT
    # ======================================================

    ASSISTANT_MODEL: str = "gpt-4o-mini"

    ASSISTANT_LLM_TIMEOUT_SECONDS: float = 30.0

    # The LLM must be at least this confident before
    # we allow its recommendation to auto-resolve.
    ASSISTANT_LLM_CONFIDENCE_THRESHOLD: float = 0.85

    # Even if the LLM is confident, the underlying
    # candidate score must not be extremely weak.
    ASSISTANT_MIN_CANDIDATE_SCORE: float = 0.70

    ASSISTANT_MAX_CANDIDATES: int = 5

    class Config:

        env_file = ".env"

        extra = "ignore"


settings = Settings()