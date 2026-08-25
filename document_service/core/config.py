from pydantic_settings import (
    BaseSettings,
)


class Settings(BaseSettings):

    # ======================================================
    # OWN DATABASE
    # ======================================================

    DOCUMENT_DB_KEY: str

    # ======================================================
    # JWT VALIDATION
    #
    # Must match Catalog Service JWT settings.
    # Catalog still ISSUES the token.
    # ======================================================

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    # ======================================================
    # CATALOG SERVICE
    # ======================================================

    CATALOG_SERVICE_URL: str = (
        "http://127.0.0.1:8000"
    )

    SERVICE_HTTP_TIMEOUT_SECONDS: float = 10.0

    INTERNAL_SERVICE_TOKEN: str

    # ======================================================
    # FILE STORAGE
    # ======================================================

    DOCUMENTS_DIR: str = (
        "data/documents"
    )

    class Config:

        env_file = (
            "document_service/.env"
        )

        extra = "ignore"


settings = Settings()