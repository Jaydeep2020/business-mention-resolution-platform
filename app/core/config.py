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

    # Number of texts encoded together.
    EMBEDDING_BATCH_SIZE: int = 64

    # How many vector candidates FAISS should return
    # before the final scoring step.
    VECTOR_SEARCH_CANDIDATES: int = 50

    # Stored relative to project root.
    BUSINESS_VECTOR_INDEX_PATH: str = (
        "data/vector_store/businesses.faiss"
    )

    class Config:

        env_file = ".env"

        extra = "ignore"


settings = Settings()