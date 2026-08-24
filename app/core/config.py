from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    SECRET_KEY: str = "change-this-secret-key"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ======================================================
    # RESOLUTION RATE LIMIT
    # ======================================================

    # Maximum resolution requests a single logged-in user
    # can make during one rate-limit window.
    RESOLUTION_RATE_LIMIT_REQUESTS: int = 10

    # Window duration in seconds.
    RESOLUTION_RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:

        env_file = ".env"

        extra = "ignore"


settings = Settings()